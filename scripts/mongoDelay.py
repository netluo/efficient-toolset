# -*- coding: utf-8 -*-
# @Time    : 2023/2/16 11:38
# @Author  : chengxiang.luo
# @Email   : zibuyu886@sina.cn
# @File    : mongoDelay.py
# @Software: PyCharm

import argparse
import time

from pymongo import MongoClient
from pymongo import ReadPreference


# 定义执行时长装饰器函数
def warps(*args):
    def deco(func):
        def _deco(*args, **kwargs):
            # 记录开始时间
            start = time.time()
            # 回调原函数
            func(*args, **kwargs)
            # 记录结束时间
            end = time.time()
            # 计算执行时长
            delat = end - start
            # 转换成ms输出
            print("delay:%sms" % (int(delat * 1000)))

        return _deco

    return deco


# 连接副本集
conn = MongoClient(['10.1.51.23:27018', '10.1.51.22:27018', '10.1.51.21:27018'], username='wx', password='w123',
                   authSource='test')
# 读写分离
db = conn.get_database('test', read_preference=ReadPreference.SECONDARY_PREFERRED)
# 定义连接的集合
collection = db.student


# 创建插入数据函数


def data_insert(num):
    try:
        for i in range(1, num):
            collection.insert_one({"name": "student" + str(i), "age": (i % 100), "city": "FuZhou"})
    except Exception as e:
        print("insert data:", e)


# 创建查询数据函数，引用装饰器函数


@warps()
def data_select(num):
    try:
        count = collection.count_documents({})
        while count != num - 1:
            count = collection.count_documents({})
    except Exception as e:
        print("select data:", e)


# 创建删除数据函数


def data_delete():
    try:
        collection.delete_many({})
    except Exception as e:
        print("delete data:", e)


# 创建计算延迟时长函数


def data_delay(num):
    data_insert(num)
    data_select(num)


if __name__ == '__main__':
    # 定义脚本需要传入插入的数据量，默认值为1000，通过-n传入参数
    parser = argparse.ArgumentParser(description='insert data to mongodb number')
    parser.add_argument('-n', action='store', dest='num', type=int, required=False, default=1000)
    given_args = parser.parse_args()
    num = given_args.num
    data_delete()
    data_delay(num)
