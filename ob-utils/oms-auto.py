# -*- coding: utf-8 -*-
# @Time    : 2022/7/4 14:25
# @Author  : chengxiang.luo
# @Email   : andrew.luo1992@gmail.com
# @File    : oms-auto.py
# @Software: PyCharm

import argparse
import collections
import json

import js2py
import prettytable
import requests
import yaml


class OmsAuto:
    def __init__(self, url_prefix):
        self.url_prefix = url_prefix
        self.headers = {
            "Content-Type": "application/json;charset=UTF-8",  # 重要参数
            "accept": "*/*",
            "accept-language": "zh-CN",
            "referer": "%s/oms-v2/endpoint" % self.url_prefix,
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
                          "Chrome/103.0.5060.134 Safari/537.36 Edg/103.0.1264.71"
        }
        self.ctoken = self.get_ctoken()
        self.cookies = {
            "_ga": "GA1.2.949065217.1650943285",
            "ctoken": self.ctoken,
            "user_token": "dHM9MTY1ODg4ODU1MTI1NCZ1c2VyPWFkbWluJnBhc3N3b3JkPUFBYmIxMSU0MCUyMw"
        }
        referer = collections.namedtuple('referer', ['usual', 'mig', 'mig_new'])
        self.referer = referer('/oms-v2/endpoint', '/oms-v2/migration', '/oms-v2/migration/new')

    # 获取token
    def get_ctoken(self):
        js_string = 'var l="bigfish_ctoken_"+(+new Date).toString(22);'
        ctoken = js2py.eval_js(js_string)
        return ctoken

    # 登录测试
    def oms_login(self, username, passwd):
        _url = "{prefix}/omsp/login?{ctoken}".format(prefix=self.url_prefix, ctoken=self.ctoken)
        self.headers.update({"Referer": self.url_prefix + "/oms-v2/login"})
        _data = {"name": username, "password": passwd}
        _res = requests.post(url=_url, data=json.dumps(_data), headers=self.headers, cookies=self.cookies)
        print(_res.text)
        if not json.loads(_res.text)["success"]:
            print("ERR-001:", json.loads(_res.text)["message"])
        else:
            print("login success.")

    # 获取数据源列表
    def get_db_list(self):

        _url = "{prefix}/omsp/endpoints?ctoken={ctoken}&pageNumber=1&pageSize=100".format(
            prefix=self.url_prefix, ctoken=self.ctoken)
        _get_db_list_res = requests.get(url=_url, headers=self.headers, cookies=self.cookies)
        _res = json.loads(_get_db_list_res.text)
        pt = prettytable.PrettyTable()
        if _res["success"]:
            # print(_res["data"])
            db_list = _res["data"]
            for i in range(len(db_list)):
                if db_list[i]["master"] is not None:
                    pt.field_names = list(db_list[i]["master"].keys())
                    pt.add_row(db_list[i]["master"].values())
                elif db_list[i]["slave"] is not None:
                    pt.field_names = list(db_list[i]["slave"].keys())
                    pt.add_row(db_list[i]["slave"].values())
            print(pt)
        else:
            print("ERR-002:", _res["message"])

    # 添加数据源
    def add_db_src(self, file):
        add_test_url = "{prefix}/omsp/endpoints/test?ctoken={ctoken}".format(prefix=self.url_prefix, ctoken=self.ctoken)
        with open(file, encoding='utf-8') as db_cfg_file:
            _src_connect_info: dict = yaml.load(db_cfg_file, Loader=yaml.FullLoader)
            for db_src_name in list(_src_connect_info.keys()):
                db_src = _src_connect_info[db_src_name]
                _test_res = json.loads(requests.post(url=add_test_url, data=json.dumps(db_src), headers=self.headers,
                                                     cookies=self.cookies).text)
                if _test_res["success"]:
                    print("测试添加数据源成功，可以添加")
                    add_source_url = "{prefix}/omsp/endpoints?ctoken={ctoken}".format(prefix=self.url_prefix,
                                                                                      ctoken=self.ctoken)
                    _add_res = json.loads(requests.post(url=add_source_url, data=json.dumps(_src_connect_info),
                                                        headers=self.headers,
                                                        cookies=self.cookies).text)
                    # print(_add_res.text)
                    if _add_res["success"]:
                        print("add mysql db source success.")
                    else:
                        print("ERR-003:", _add_res["message"])

    # 删除数据源
    def del_db_source(self, db_source_id):
        _url = "{prefix}/omsp/endpoints/{db_source_id}?ctoken={ctoken}&id={db_source_id}".format(prefix=self.url_prefix,
                                                                                                 ctoken=self.ctoken,
                                                                                                 db_source_id=db_source_id)
        _delete_db_res = json.loads(requests.delete(url=_url, headers=self.headers, cookies=self.cookies).text)
        if _delete_db_res['success']:
            pass

    # 获取迁移项目列表
    def get_mig_list(self, status='ALL', is_need_data=False):
        '''
        statuses :
        INIT    未启动
        RUNNING 在运行
        SUSPEND 已暂停
        FAILED  失败
        FINISHED    已完成
        RELEASING   释放中
        RELEASED    已释放
        ALL         所有
        :return:
        '''
        _url = "{prefix}/omsp/migrations?ctoken={ctoken}&pageSize=5&statuses={status}&types=ALL".format(
            prefix=self.url_prefix, ctoken=self.ctoken, status=status)
        mig_headers = self.headers.update({'referer': '%s/oms-v2/migration' % self.url_prefix, })
        _get_mig_list_res = json.loads(requests.get(url=_url, headers=mig_headers, cookies=self.cookies).text)
        _pt = prettytable.PrettyTable()
        _item_list = ["projectId", "projectName", "labels", "projectOwner", "projectImportance", "migrationType",
                      "projectStatus",
                      "sourceendpointName", "sourceendpointId", "sourcedbEngine", "destendpointName", "destendpointId",
                      "destdbEngine"]
        if _get_mig_list_res["success"] and len(_get_mig_list_res["data"]) != 0:
            if not is_need_data:
                _pt.field_names = _item_list
                for mig_detail in _get_mig_list_res["data"]:
                    _pt.add_row([mig_detail["projectId"], mig_detail["projectName"], mig_detail["projectName"],
                                 mig_detail["projectOwner"], mig_detail["projectImportance"],
                                 mig_detail["migrationType"], mig_detail["projectStatus"],
                                 mig_detail["sourceConnectInfo"]["endpointName"],
                                 mig_detail["sourceConnectInfo"]["endpointId"],
                                 mig_detail["sourceConnectInfo"]["dbEngine"],
                                 mig_detail["destConnectInfo"]["endpointName"],
                                 mig_detail["destConnectInfo"]["endpointId"], mig_detail["destConnectInfo"]["dbEngine"]
                                 ])
                print(_pt)
            else:
                """
                todo:
                """
                pass

    def get_schema_list(self, dbid):
        _url = "{prefix}/omsp/endpoints/{dbid}/objects?ctoken={ctoken}&objectType=SCHEMA".format(prefix=self.url_prefix,
                                                                                                 dbid=dbid,
                                                                                                 ctoken=self.ctoken)
        _get_schema_list_res = json.loads(
            requests.get(url=_url, headers=self.headers.update({"Referer": self.url_prefix + self.referer.mig_new}),
                         cookies=self.cookies).text)
        if _get_schema_list_res["success"]:
            print(_get_schema_list_res["data"])
        else:
            print(_get_schema_list_res["message"])

    def new_mig_task(self, src, dst, *args):
        pass


if __name__ == '__main__':
    parse = argparse.ArgumentParser(description="yearning auto agreed. ", add_help=True)
    parse.add_argument('-u', '--url', help="set the url for oms", type=str, default="http://127.0.0.1:8089")
    parse.add_argument('-a', '--add-db-source', help="add db source. ", action='store_true')
    parse.add_argument('-c', '--db-config', help="db source config file.", metavar='', type=str)
    parse.add_argument('-d', '--delete-db-source', help="delete db source. ", nargs='+', metavar='', type=str)
    parse.add_argument('-l', '--list-db-source', help="list all db source info.", action='store_true')
    parse.add_argument('-g', '--get-migration-list', help="list all migration task, no data detail.",
                       action='store_true')
    parse.add_argument('--get-migration-list-and-data', help="list all migration task with detail.",
                       action='store_true')
    args = parse.parse_args()
    if args.url:
        omsAuto = OmsAuto(args.url)
        if args.add_db_source:
            cfg = args.add_db_source
            omsAuto.add_db_src(cfg)
        if args.list_db_source:
            omsAuto.get_db_list()
        if args.delete_db_source:
            for dbid in args.delete_db_source:
                omsAuto.del_db_source(dbid)
        if args.get_migration_list:
            omsAuto.get_mig_list()

    # omaauto = omsAuto(1)
    # omaauto.oms_login()
    # omaauto.add_mysql_db_src()
    # omaauto.get_db_list()
    """
    todo:
    时区问题
    """
    # omaauto.del_db_source("e_3v1ha3rt72dc")
    # omaauto.get_db_list()
