# -*- coding: utf-8 -*-
# @Time    : 2023/2/14 14:12
# @Author  : chengxiang.luo
# @Email   : zibuyu886@sina.cn
# @File    : compute_partition.py
# @Software: PyCharm

import logging
import re
from logging import handlers

import pymysql


class ComputePartition:
    def __init__(self):
        self.memstore_limit_percentage = 50


# 查询SQL ： select id from eo_oslms_test.lms_activity_test partition(p0) order by id;
class MysqlOperation:
    def __init__(self):
        self.host = '10.0.9.147'
        self.port = 2883
        self.user = 'root@web#ob_cluster'
        self.password = 'web_ro'
        self.database = 'web_ro_test'

        self.logfile = 'leader-switch.log'
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
            dbconnection = pymysql.connect(host=self.host, port=self.port, user=self.user, password=self.password,
                                           db=self.database)
            dbcursor = dbconnection.cursor()
            return dbconnection, dbcursor
        except Exception as e001:
            raise e001

    # 1. 获取不是更新的updated_at的字段的数据的主键，传入下一步
    # 2. 根据主键去查线上的数据，如果updated_at比较新，则写入lms_activity_fix表里

    def get_ids(self):
        _db_conn, _cur = self.get_db_cursor()
        try:
            _cur.execute(
                "select id from eo_oslms_test.lms_activity_test where id > 7000000 and id < 8396000 order by id;")
            # _cur.execute("select id from eo_oslms_test.lms_activity_test partition(p0) order by id;")
            _ids = _cur.fetchall()
            for (_id,) in _ids:
                # self.logger.info("The current id is : %d ." % (_id))
                # self.get_diff_data(_id)
                _cur.execute("select course_id from eo_oslms_test.lms_activity_test where id = %d" % _id)
                # ((course_id,),)=_cur.fetchall()
        except Exception as e001:
            print(e001)
            self.logger.error(e001)
        finally:
            _cur.close()
            _db_conn.close()


while True:
    MysqlOperation().get_ids()
