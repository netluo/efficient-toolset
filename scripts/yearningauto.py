# -*- coding: utf-8 -*-
# @Time    : 2022/6/20 14:43
# @Author  : chengxiang.luo
# @Email   : andrew.luo1992@gmail.com
# @File    : yearningauto.py
# @Software: PyCharm

import argparse
import datetime
import json

import prettytable
import requests


class ynAutoAgree:
    def __init__(self, url_prefix):
        self.url_prefix = url_prefix
        self.headers = {
            "content-type": "application/json;charset=UTF-8",  # 重要参数
            "accept": "application/json, text/plain, */*",
            "authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9"
                             ".eyJleHAiOjE2NTU3MzExNzEsIm5hbWUiOiJhZG1pbiIsInJvbGUiOiJzdXBlciJ9"
                             ".Mv_mnjHH09MJYZW6DAliebH0m86FGi1GiEKvhfho8fE",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
                          "Chrome/102.0.5005.124 Safari/537.36 Edg/102.0.1245.41",
            "referer": "{}".format(self.url_prefix)
        }
        self.cookies = dict(cookie="_ga=GA1.2.949065217.1650943285")
        self.url = "{prefix}/api/v2/audit/query/list".format(prefix=self.url_prefix)

        # 只请求第一页
        # status :
        # 1 : 同意过的，正在查询的
        # 2 : 待审核
        # 3 : 查询结束了的
        # 7 : 所有
        self.params = {
            "page": 1,
            "find": {
                "picker": [],
                "valve": False,
                "text": "",
                "explain": "",
                "work_id": "",
                "type": 2,
                "status": 7
            }
        }

    # 获取token
    def yn_login(self):
        _url = "{prefix}/login".format(prefix=self.url_prefix)
        _data = {
            "username": "admin",
            "password": "!!)a1106"
        }
        _res = requests.post(url=_url, data=json.dumps(_data), headers=self.headers, cookies=self.cookies)
        # print(_res.text)
        self.token = json.loads(_res.text)["payload"]["token"]
        self.headers["authorization"] = "Bearer " + str(self.token)

    # 获取第一页的查询列表
    def put_page(self, status_code):
        self.params["find"].update({"status": status_code})
        _payload = json.dumps(self.params)
        _res = requests.put(url=self.url, headers=self.headers, data=_payload, cookies=self.cookies)
        # print(self.url)
        # print(_res.status_code)
        if _res.status_code == 200 and status_code == 2:
            return self.get_work_id(_res)
        elif _res.status_code == 200 and status_code == 1:
            return self.get_running_query(_res)
        else:
            print(datetime.datetime.now(), "error : 出错了")

    # 获取work_id
    def get_work_id(self, json_res):
        _res_dict = json.loads(json_res.text)
        _res_list = _res_dict['payload']['data']
        for _query in _res_list:
            print('username: ', _query['username'], '\twork_id:', _query['work_id'])
            self.post_agreed(_query['work_id'])

    def get_running_query(self, json_res):
        _res_dict = json.loads(json_res.text)
        _res_list = _res_dict['payload']['data']
        _pt = prettytable.PrettyTable()
        _pt.field_names = ["work_id", "username", "date"]
        print("正在执行的查询：")
        for _query in _res_list:
            _pt.add_row([_query['work_id'], _query['username'], _query["date"]])
        print(_pt)

    # 同意查询
    def post_agreed(self, work_id: str):
        _url = "{prefix}/api/v2/audit/query/state".format(prefix=self.url_prefix)
        _data = {"work_id": work_id, "tp": "agreed"}
        agreed_res = requests.post(_url, data=json.dumps(_data), headers=self.headers, cookies=self.cookies)
        print(agreed_res.text)

    # 终止查询
    def post_stop(self, work_id: str):
        _url = "{prefix}/api/v2/audit/query/state".format(prefix=self.url_prefix)
        _data = {"work_id": work_id, "tp": "stop"}
        agreed_res = requests.post(_url, data=json.dumps(_data), headers=self.headers, cookies=self.cookies)
        print(agreed_res.text)


if __name__ == '__main__':
    parse = argparse.ArgumentParser(description="yearning auto agreed. ", add_help=True)
    parse.add_argument('-u', '--url', help="set the url for yearning", type=str, default="https://yn.test-inc.com")
    parse.add_argument('-a', '--agreed', help="agree to query. ", action='store_true')
    parse.add_argument('-k', '--kill', help="kill all query, use work_id. ", nargs='+', metavar='', type=str)
    parse.add_argument('-l', '--list', help="list all running query.", action='store_true')
    args = parse.parse_args()
    if args.url:
        ynauto = ynAutoAgree(args.url)
        ynauto.yn_login()
        if args.agreed:
            ynauto.put_page(2)
        if args.list:
            ynauto.put_page(1)
        if args.kill:
            print(args.kill)
            for worker_id in args.kill:
                ynauto.post_stop(worker_id)
