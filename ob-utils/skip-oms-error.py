# -*- coding: utf-8 -*-
# @Time    : 2023/2/21 15:19
# @Author  : chengxiang.luo
# @Email   : zibuyu886@sina.cn
# @File    : skip-oms-error.py
# @Software: PyCharm
from logging import handlers

import js2py
import logging
import pymysql
import re
import requests


class MysqlOperation:
    def __init__(self):
        self.host = '10.0.2.116'
        self.port = 2883
        self.user = 'root@oms_meta#obforocp'
        self.password = 'AAbb11__'
        self.database = 'drc_rm_db'

        self.logfile = 'skip-oms-err.log'
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
            return dbconn01, dbcursor01
        except Exception as e001:
            raise e001

    def get_err_id(self):
        _dbconn, _cur = self.get_db_cursor()
        _cur.execute("select id from ops_request where creator = 'HA' and status = 'ERROR'")
        ids = _cur.fetchall()
        for (errid,) in ids:
            self.res_err(errid)
            pass

    def get_ctoken(self):
        js_string = 'var l="bigfish_ctoken_"+(+new Date).toString(22);'
        ctoken = js2py.eval_js(js_string)
        return ctoken

    def res_err(self, err_id):
        ctoken = self.get_ctoken()
        headers = {
            "accept": "*/*",
            "accept-language": "zh-CN",
            "authority": "ob-oms-lab.test-inc.com",
            "content-length": "0",
            "origin": "https://ob-oms-lab.test-inc.com",
            "referer": f"https://ob-oms-lab.test-inc.com/oms-v2/operation/work/{err_id}?id={err_id}",
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-origin",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36 Edg/110.0.1587.50"
        }

        cookies = {
            "_ga": "GA1.1.949065217.1650943285",
            "_ga_W2FYNR9BLD": "GS1.1.1667448210.5.1.1667448328.0.0.0",
            "ctoken": "bigfish_ctoken_18c6digkhe",
            "user_token": "dHM9MTY3Njk1NzM2MTA2NCZ1c2VyPWFkbWluJnBhc3N3b3JkPUFBYmIxMSU0MCUyMw"
        }

        response = requests.put(
            f'https://ob-oms-lab.test-inc.com/omsp/operator/request/skip?ctoken={ctoken}&id={err_id}&dimension=ORDER',
            # params=params,
            cookies=cookies,
            headers=headers,
        )
        print(err_id, '\t', response.text)


if __name__ == '__main__':
    skipper = MysqlOperation()
    skipper.get_err_id()
