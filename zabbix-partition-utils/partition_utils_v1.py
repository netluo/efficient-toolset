# -*- coding: utf-8 -*-
# @Time    : 2022/3/18 16:39
# @Author  : chengxiang.luo
# @Email   : andrew.luo1992@gmail.com
# @File    : partition_utils_v1.py
# @Software: PyCharm

import subprocess
import datetime
import time

# ----- config -------
host = '172.16.250.231'
port = 6001
user = 'partitionuser'
password = 'Passw0rd'
database = 'zabbix'
table_name_list = ['history', 'history_log', 'history_str',
                   'history_text', 'history_uint', 'trends', 'trends_uint']
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

for table_name in table_name_list:
    tms1 = int(c_unixtime)
    tms2 = int(c_unixtime) - (86400 * partiton_retention_days)
    sql = 'set global read_only =1;set session lock_wait_timeout = 3; rename table {table} to {table}_test;'.format(
        table=table_name)
    cmd = "mysql -h {host} -P{port} -u {user} -p{password} -D{db} -e '{sql}'".format(
        host=host, port=port, user=user, password=password, db=database, sql=sql)
    subprocess.getoutput(cmd)

    for i in range(partiton_tocreate_days):
        tms1 = tms1 + 86400
        ymd_str = time.strftime("%Y%m%d", time.localtime(tms1))
        add_partition_sql = 'alter table {table}_test add partition(partition p{pdate} VALUES LESS THAN ({punixtime}) DATA DIRECTORY = \"/data1/data/services/mysql\" ENGINE = InnoDB);'.format(
            table=table_name, pdate=ymd_str, punixtime=tms1 + 86400)
        add_partition_shell = "mysql -h {host} -P{port} -u {user} -p{password} -D{db} -e '{sql}'".format(
            host=host, port=port, user=user, password=password, db=database, sql=add_partition_sql)
        print(add_partition_sql)
        # 创建分区的时候，分区名字是当天,小于的是明天凌晨 0 点整
        res1 = subprocess.getoutput(add_partition_shell)
        print(res1)

    for i in range(partition_once_to_drop):
        tms2 = tms2 - 86400
        ymd2_str = time.strftime("%Y%m%d", time.localtime(tms2))
        sql2 = "mysql -h {host} -P{port} -u {user} -p{password} -D{db} -e 'alter table {table}_test drop partition p{ptodrop};'".format(
            host=host, port=port, user=user, password=password, db=database, table=table_name, ptodrop=ymd2_str)
        print(sql2)
        res2 = subprocess.getoutput(sql2)
        print(res2)

    sql = "set session lock_wait_timeout = 3;rename table {table}_test to {table};set global read_only = 0;".format(
        table=table_name)
    cmd = "mysql -h {host} -P{port} -u {user} -p{password} -D{db} -e '{sql}'".format(
        host=host, port=port, user=user, password=password, db=database, sql=sql)
    subprocess.getoutput(cmd)
