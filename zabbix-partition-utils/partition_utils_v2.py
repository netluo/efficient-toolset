# -*- coding: utf-8 -*-
# @Time    : 2022/3/18 16:39
# @Author  : chengxiang.luo
# @Email   : andrew.luo1992@gmail.com
# @File    : partition_utils_v2.py
# @Software: PyCharm

import datetime
import logging
import re
import time
from logging import handlers

import asyncio
import pymysql

# ----- config -------
# host = '172.16.250.231'
# port = 6001
# user = 'partitionuser'
# password = 'Passw0rd'
# database = 'zabbix'
table_need_add = ['history', 'history_log', 'history_str', 'history_text', 'history_uint', 'trends', 'trends_uint']
table_need_drop = ['history', 'history_uint']
partiton_retention_days = 30  # 分区保留天数
partiton_tocreate_days = 30  # 每次建分区建多少天
partition_once_to_drop = 7  # drop 分区时，一次性删多少天
# ------ end --------

c_date = datetime.date.today()  # 当前日期

# datetime.datetime(2022, 3, 18, 19, 9, 10, 551382)
# c_unixtime = time.mktime(c_date.timetuple())  # 浮点数，1647532800.0，当天 00:00:00 的时间戳，用的时候需要转为int + 86400 变为明天凌晨的
# c_unixtime = c_date.strftime("%Y%m%d")

c_unixtime = time.mktime(c_date.timetuple())


# c_date datetime.date(2022, 3, 21) c_date.timetuple() time.struct_time(tm_year=2022, tm_mon=3, tm_mday=21,
# tm_hour=0, tm_min=0, tm_sec=0, tm_wday=0, tm_yday=80, tm_isdst=-1) tm_wday -- 星期几 tm_yday -- 一年中的第几天 time.mktime(
# c_date.timetuple()) 1647792000.0

# c_date.timestamp()
# 1647601800.74308
# c_date.timestamp().__int__()
# 1647601800
# c_date.strftime("%Y%m%d")
# '20220318'

# print(datetime.datetime.strptime(c_date.__str__(), "%Y%m%d"))

class partition_mgr:
    def __init__(self):
        self.host = '127.0.0.1'
        self.port = 3306
        self.user = 'lcx'
        self.password = 'root123'
        self.database = 'zabbix'
        self.logfile = '/data2/mysql6001/logs/partition_utils.log'
        # logger 写在init里
        self.fmt = logging.Formatter('%(asctime)s - %(filename)s[line:%(lineno)d] - %(levelname)s: %(message)s')
        self.logger = logging.getLogger(self.logfile)
        self.logger.setLevel(logging.INFO)
        self.logger_handler = handlers.TimedRotatingFileHandler(filename=self.logfile, when='D',
                                                                backupCount=30, encoding='utf-8', interval=1)
        self.logger_handler.setFormatter(self.fmt)
        # # 如果对日志文件名没有特殊要求的话，可以不用设置suffix和extMatch，如果需要，一定要让它们匹配上。
        self.logger_handler.suffix = '%Y%m%d'
        self.logger_handler.extMatch = re.compile(r"^\d{8}$")
        self.logger.addHandler(self.logger_handler)

        try:
            self.mydbconn = pymysql.connect(host=self.host, port=self.port, user=self.user, password=self.password,
                                            db=self.database)
            self.dbcursor = self.mydbconn.cursor()
            self.logger.info("DB connect success")
        except Exception as e001:
            self.logger.error("e001: db connect failed. %s" % e001)

    def set_read_only(self, _is_ro: int):
        try:
            self.dbcursor.execute("set global read_only =%d;" % _is_ro)
            self.mydbconn.commit()
            self.logger.warning("set global read_only to %d." % _is_ro)
        except Exception as e002:
            self.logger.error(e002)

    async def rename_table(self, *args):
        for table_name in args:
            rename_sql = 'rename table {table} to {table}_gho;'.format(table=table_name)
            self.dbcursor.execute(rename_sql)
            self.mydbconn.commit()
            self.logger.warning(rename_sql)

    async def recover_table(self, *args):
        for table_name in args:
            recover_sql = 'rename table {table}_gho to {table};'.format(table=table_name)
            self.dbcursor.execute(recover_sql)
            self.mydbconn.commit()
            self.logger.warning(recover_sql)

    # async def prunning(self,parogram):
    #     await asyncio.create_subprocess_exec(program=parogram)

    async def partition_add(self, table_name):
        tms1 = int(c_unixtime)
        # for table_name in args:
        # 增加分区
        for i in range(partiton_tocreate_days):
            start = time.time()
            tms1 = tms1 + 86400
            ymd_str = time.strftime("%Y%m%d", time.localtime(tms1))
            add_partition_sql = 'alter table {table}_gho add partition(partition p{pdate} ' \
                                'VALUES LESS THAN ({punixtime}) ' \
                                'DATA DIRECTORY = \"/data1/data/services/mysql\" ENGINE = InnoDB);'.format(
                table=table_name, pdate=ymd_str, punixtime=tms1 + 86400)
            self.logger.info(add_partition_sql)
            try:
                self.dbcursor.execute(add_partition_sql)
                self.mydbconn.commit()
                self.logger.warning(
                    "the table %s add partition done. used time %s ." % (table_name, time.time() - start))
            except pymysql.err.MySQLError as e003:
                if e003.args[0] == 1517:
                    pass
                else:
                    self.logger.error("Error code: %d ,%s" % (e003.args[0], e003.args[1]))

    async def partition_drop(self, table_name):
        tms2 = int(c_unixtime) - (86400 * partiton_retention_days)
        # for table_name in args[:2]:
        # 删除分区
        for i in range(partition_once_to_drop):
            start = time.time()
            tms2 = tms2 - 86400
            ymd2_str = time.strftime("%Y%m%d", time.localtime(tms2))
            drop_partition_sql = 'alter table {table}_gho drop partition p{ptodrop};'.format(table=table_name,
                                                                                             ptodrop=ymd2_str)
            self.logger.info(drop_partition_sql)
            try:
                self.dbcursor.execute(drop_partition_sql)
                self.mydbconn.commit()
                self.logger.warning(
                    "the table %s drop partition done. used time %s ." % (table_name, time.time() - start))
            except pymysql.MySQLError as e004:
                if e004.args[0] == 1507:
                    pass
                else:
                    self.logger.error("Error code: %d ,%s" % (e004.args[0], e004.args[1]))

    async def run(self):
        try:
            # 尝试并行处理
            add_partition_tast_list = []
            drop_partition_tast_list = [
                asyncio.ensure_future(self.partition_drop('history')),
                asyncio.ensure_future(self.partition_drop('history_uint'))
            ]
            await self.rename_table('history', 'history_log', 'history_str', 'history_text', 'history_uint', 'trends',
                                    'trends_uint')
            for tname in table_need_add:
                add_partition_tast_list.append(asyncio.ensure_future(self.partition_add(tname)))
            _add_done, _add_pending = await asyncio.wait(add_partition_tast_list, timeout=100)
            _drop_done, _drop_pending = await asyncio.wait(drop_partition_tast_list, timeout=480)
            self.logger.warning("add partition %s done. add %s pending." % (str(_add_done), str(_add_pending)))
            self.logger.warning("drop partition %s done. drop %s pending." % (str(_add_done), str(_add_pending)))
            # await asyncio.gather(self.partition_add(*args), self.partition_drop(*args))
            await self.recover_table('history', 'history_log', 'history_str', 'history_text', 'history_uint', 'trends',
                                     'trends_uint')
            self.mydbconn.close()
        except Exception as e005:
            self.logger.error(e005)


if __name__ == '__main__':
    p_mgr = partition_mgr()
    start_time = time.time()
    p_mgr.set_read_only(1)
    loop = asyncio.get_event_loop()
    loop.run_until_complete(p_mgr.run())
    p_mgr.set_read_only(0)
    p_mgr.logger.info("Total time : %s " % (time.time() - start_time))
    print("Total time : %s " % (time.time() - start_time))
