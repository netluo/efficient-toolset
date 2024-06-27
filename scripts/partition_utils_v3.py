# -*- coding: utf-8 -*-
# @Time    : 2022/3/18 16:39
# @Author  : chengxiang.luo
# @Email   : andrew.luo1992@gmail.com
# @File    : partition_utils_v2.py
# @Software: PyCharm
import argparse
import asyncio
import calendar
import datetime
import logging
import os
import re
import smtplib
import threading
import time
from email.header import Header
from email.mime.text import MIMEText
from logging import handlers

import nest_asyncio
import pymysql
from prettytable import PrettyTable

nest_asyncio.apply()

# ----- config -------
# host = '172.16.250.231'
# port = 6001
# user = 'partitionuser'
# password = 'Passw0rd'
# database = 'zabbix'
table_need_add = ['history', 'history_uint', 'history_log', 'history_str', 'history_text', 'trends', 'trends_uint']
table_need_add_by_day = ['history', 'history_uint']
table_need_add_by_month = ['history_log', 'history_str', 'history_text', 'trends', 'trends_uint']
# table_need_drop = ['history', 'history_uint']

partition_once_to_drop = 7  # drop 分区时，一次性删多少天
# ------ end --------

c_date = datetime.date.today()  # 当前日期

# 获取当月天数
monthRange = calendar.monthrange(c_date.year, c_date.month)[1]
partition_retention_days = partition_to_create_days = monthRange  # 分区保留天数 # 每次建分区建多少天

# datetime.datetime(2022, 3, 18, 19, 9, 10, 551382)
# c_unixtime = time.mktime(c_date.timetuple())  # 浮点数，1647532800.0，当天 00:00:00 的时间戳，用的时候需要转为int + 86400 变为明天凌晨的
# c_unixtime = c_date.strftime("%Y%m%d")

# 当天凌晨的时间点
c_unixtime = time.mktime(c_date.timetuple()).__int__()


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
    def __init__(self, host, port, user, password, database):
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.database = database

        self.logfile = 'partition_utils.log'
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

    def get_db_cursor(self):
        try:
            dbconn01 = pymysql.connect(host=self.host, port=self.port, user=self.user, password=self.password,
                                       db=self.database)
            dbcursor01 = dbconn01.cursor()
            self.logger.info("DB connect success")
            return dbconn01, dbcursor01
        except Exception as e001:
            self.logger.error("e001: db connect failed. %s" % e001)
            raise e001

    def set_read_only(self, _is_ro: int):
        try:
            _db_conn, _cur = self.get_db_cursor()
            _cur.execute("set global read_only =%d;" % _is_ro)
            _db_conn.commit()
            self.logger.warning("set global read_only to %d." % _is_ro)
        except Exception as e002:
            self.logger.error(e002)

    async def rename_table(self, table_name):
        _db_conn, _cur = self.get_db_cursor()
        try:
            rename_sql = 'rename table {table} to {table}_gho;'.format(table=table_name)
            _cur.execute(rename_sql)
            _db_conn.commit()
            self.logger.warning(rename_sql)
        except Exception as e003:
            if e003.args[0] == 1146:
                pass
            else:
                self.logger.error(e003)

    async def recover_table(self, table_name):
        _db_conn, _cur = self.get_db_cursor()
        recover_sql = 'rename table {table}_gho to {table};'.format(table=table_name)
        _cur.execute(recover_sql)
        _db_conn.commit()
        self.logger.warning(recover_sql)

    async def partition_add_by_day(self, table_name):
        _db_conn, _cur = self.get_db_cursor()
        tms1 = c_unixtime
        # for table_name in args:
        # 增加分区
        for i in range(partition_to_create_days):
            start = time.time()
            tms1 = tms1 + 86400  # 明天凌晨 00:00
            ymd_str = time.strftime("%Y%m%d", time.localtime(tms1))
            add_partition_sql = 'alter table {table}_gho add partition(partition p{pdate} ' \
                                'VALUES LESS THAN ({punixtime}) ' \
                                'DATA DIRECTORY = \"/data1/data/services/mysql\" ENGINE = InnoDB);'.format(
                table=table_name, pdate=ymd_str,
                punixtime=tms1 + 86400)  # 因为今天的已经创建了，所以至少从明天开始，间隔为86400 * interval
            self.logger.info(add_partition_sql)
            try:
                _cur.execute(add_partition_sql)
                _db_conn.commit()
                self.logger.warning(
                    "the table %s add partition done. used time %s ." % (table_name, time.time() - start))
            except pymysql.err.MySQLError as e003:
                if e003.args[0] == 1517:
                    pass
                else:
                    self.logger.error("Error code: %d ,%s" % (e003.args[0], e003.args[1]))

    async def partition_add_by_month(self, table_name):
        _db_conn, _cur = self.get_db_cursor()

        # 下个月1号凌晨的时间戳
        # tms1 = time.mktime(datetime.date(c_date.year, c_date.month + 1, 1).timetuple()).__int__()

        # 增加3个月的分区
        for i in range(3):
            start = time.time()
            c_month = (c_date.month + 1 + i) % 12 + 1
            c_year = c_date.year + (c_date.month + 1 + i) // 12
            tms1 = time.mktime(datetime.date(c_year, c_month, 1).timetuple()).__int__()
            # ymd_str = time.strftime("%Y%m%d", time.localtime(tms1))
            ymd_str = "%04d%02d00" % (c_year, c_month - 1)
            add_partition_sql = 'alter table {table}_gho add partition(partition p{pdate} ' \
                                'VALUES LESS THAN ({punixtime}) ' \
                                'DATA DIRECTORY = \"/data1/data/services/mysql\" ENGINE = InnoDB);'.format(
                table=table_name, pdate=ymd_str,
                punixtime=tms1)
            self.logger.info(add_partition_sql)
            try:
                _cur.execute(add_partition_sql)
                _db_conn.commit()
                self.logger.warning(
                    "the table %s add partition done. used time %s ." % (table_name, time.time() - start))
            except pymysql.err.MySQLError as e003:
                if e003.args[0] == 1517:
                    pass
                else:
                    self.logger.error("Error code: %d ,%s" % (e003.args[0], e003.args[1]))

    async def partition_drop(self, table_name):
        _db_conn, _cur = self.get_db_cursor()
        tms2 = c_unixtime - partition_retention_days * 86400
        # for table_name in args[:2]:
        # 删除分区
        get_partition_name_sql = "select TABLE_NAME,PARTITION_NAME,PARTITION_DESCRIPTION from information_schema.PARTITIONS " \
                                 "where TABLE_SCHEMA='zabbix' and TABLE_NAME='{table_name}_gho' and " \
                                 "PARTITION_DESCRIPTION <= {tms2} order by PARTITION_DESCRIPTION desc " \
                                 "limit 30;".format(table_name=table_name, tms2=tms2)
        self.logger.info(get_partition_name_sql)
        _cur.execute(get_partition_name_sql)
        _res = _cur.fetchall()
        # pname= _cur.fetchall()
        if _cur.description:
            table = PrettyTable()
            table.field_names = [col[0] for col in _cur.description]
            for (tblname, pname, pdesc) in _res:
                table.add_row((table_name, pname, pdesc))
                start = time.time()
                drop_partition_sql = 'alter table {table}_gho drop partition {ptodrop};'.format(table=table_name,
                                                                                                ptodrop=pname)
                self.logger.info(drop_partition_sql)
                try:
                    _cur.execute(drop_partition_sql)
                    _db_conn.commit()
                    self.logger.warning(
                        "the table %s drop partition done. used time %s ." % (table_name, time.time() - start))
                except pymysql.MySQLError as e004:
                    if e004.args[0] == 1507:
                        pass
                    else:
                        self.logger.error("Error code: %d ,%s" % (e004.args[0], e004.args[1]))
            self.logger.info('\n' + str(table))

    async def add_and_drop(self, table_name):
        await self.rename_table(table_name)
        if table_name in table_need_add_by_day:
            await self.partition_add_by_day(table_name)
            await self.partition_drop(table_name)
        if table_name in table_need_add_by_month:
            await self.partition_add_by_month(table_name)
        await self.recover_table(table_name)

    def run(self, aloop: asyncio.AbstractEventLoop, table_name):
        try:
            # 尝试并行处理
            aloop.run_until_complete(self.add_and_drop(table_name))
            self.logger.info("Total time for table %s: %s , stop at %s ." % (
                table_name, (time.time() - start_time), datetime.datetime.now()))
        except Exception as e005:
            self.logger.error(e005)

    @staticmethod
    def send_mail():
        hostname = os.uname()[1]
        mail_server = "smtp.exmail.qq.com"
        mail_host = "smtp.exmail.qq.com"
        mail_user = "sa@example.com"
        mail_pass = "examplePwd"
        mail_port = 465
        sender = 'checker@example.com'
        receivers = ['ops_dba@example.com']
        text = "您好,今天的MySQL分区创建失败了.请登陆%s服务器查看" % hostname
        message = MIMEText(text, 'plain', 'utf-8')
        message['From'] = Header("报警机器人", 'utf-8')
        message['To'] = Header("MySQL分区检查", 'utf-8')
        subject = '测试环境分区检查'
        message['Subject'] = Header(subject, 'utf-8')
        try:
            smtp_obj = smtplib.SMTP()
            smtp_obj.connect(mail_host)
            smtp_obj.login(mail_user, mail_pass)
            smtp_obj.sendmail(sender, receivers, message.as_string())
            return "send email successfully"
        except smtplib.SMTPException as e:
            return "Error: can't send email with err %s" % e


if __name__ == '__main__':
    start_time = time.time()
    parser = argparse.ArgumentParser(conflict_handler='resolve')
    parser.add_argument("-h", "--host", help="Connect to host", type=str, required=True)
    parser.add_argument("-P", "--port", help="Port number to use for connection", type=int, required=True)
    parser.add_argument("-u", "--user", help="Name of user", type=str, required=True)
    parser.add_argument("-p", "--password", help="Password of user", required=True)
    parser.add_argument("-D", "--database", help="database of user", default='zabbix', type=str)
    # parser.add_argument("-f", "--file", help="The script generate from MySQL mysql_tzinfo_to_sql", required=True)
    # parser.add_argument("-t", "--tenant", help="Tenant for import data if not sys")
    args = parser.parse_args()
    host = args.host
    port = args.port
    user = args.user
    pwd = args.password
    database = args.database
    p_mgr = partition_mgr(host, port, user, pwd, database)
    p_mgr.logger.info("Begin at %s ." % datetime.datetime.now())
    p_mgr.set_read_only(1)
    loop_day = asyncio.new_event_loop()
    asyncio.set_event_loop(loop_day)
    for table in table_need_add:
        threading.Thread(target=p_mgr.run, args=(loop_day, table)).start()
    p_mgr.set_read_only(0)

# 按月增加分区的功能出现了问题，需要处理   done
# [line:222] - ERROR: This event loop is already running 处理： 使用nest_asyncio 解决
# --------- 以下错误通过更换python37 解决 -----------------
# Exception in callback _patch_task.<locals>.step()
# handle: <Handle _patch_task.<locals>.step()>
# Traceback (most recent call last):
# File "/usr/lib64/python3.6/asyncio/events.py", line 145, in _run
# self._callback(*self._args)
# File "/usr/local/lib/python3.6/site-packages/nest_asyncio.py", line 195, in step
# step_orig(task, exc)
# File "/usr/lib64/python3.6/asyncio/tasks.py", line 245, in _step
# self.__class__._current_tasks.pop(self._loop)
# KeyError: <_UnixSelectorEventLoop running=False closed=False debug=False>
# --------------------------------
