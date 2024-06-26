# ！/usr/bin/env python3
import argparse
import datetime
import os

import pymysql


class mysqlUserMigrite:
    def __init__(self, host, port, user, passwd, socket):
        self.host: str = host
        self.port: int = port
        self.user: str = user
        self.password: str = passwd
        self.db_count: int = 0
        self.des_dir: str = './'
        self.des_file = datetime.datetime.now()
        self.dump_dbs = None
        self.unix_socket = socket

    def user_migrate(self):
        mydb = pymysql.connect(host=self.host, port=self.port, user=self.user, password=self.password
                               , unix_socket=self.unix_socket)

        mycorsur = mydb.cursor()
        # 查询用户，授权主机，和认证字符串的语句
        uerquerysql = "select user,host,plugin,authentication_string from mysql.user where user not in ('mysql.infoschema','mysql.session','mysql.sys','root')"
        mycorsur.execute(uerquerysql)
        user_and_host = []
        exec_sql = []
        # 用户的所有授权，字典文件
        grants_for_user = {}

        for user, host, plugin, authentication_string in mycorsur.fetchall():
            user_host = "'{}'@'{}'".format(user, host)
            user_and_host.append(user_host)
            create_user_sql: str = "create user if not exists {} identified with {} as '{}';\n".format(
                user_host, plugin, authentication_string)
            exec_sql.append(create_user_sql)

        # 写入列表，并写入本地文件夹
        with open('mysql-user-migration.txt', 'a') as f:
            f.writelines(exec_sql)

        for uh in user_and_host:
            mycorsur.execute("show grants for {}".format(uh))
            gt = []
            for grants in mycorsur.fetchall():
                # type(grants) <class 'tuple'>
                gt.append(grants[0])
                grants_for_user.update({uh: gt})
                with open('mysql-user-migration.txt', 'a+') as f:
                    f.write(grants[0] + ';\n')

    def db_migrate(self, *args):
        try:
            mysql_dump_str = "/usr/bin/mysqldump -h {host} --port {port} --no-defaults --user {username} -p{password} " \
                             "--databases {dbs} --single-transaction --master-data=2 --set-gtid-purged=OFF > {des_dir}/{file}".format(
                host=self.host, port=self.port, username=self.user, password=self.password, dbs=args[0],
                des_dir=self.des_dir, file=self.des_file)
            os.system(mysql_dump_str)
        except Exception as err001:
            print(err001)


if __name__ == '__main__':
    parse = argparse.ArgumentParser(description="migrate users or databases", add_help=True)
    parse.add_argument("--host", default='localhost', help="set the host", metavar='hostname', required=True)
    parse.add_argument('-P', "--port", default=3306, type=int, help="set the mysql port", metavar='', required=True)
    parse.add_argument("-S", "--socket", help="if host is localhost, the socket is required", metavar='',
                       default=None)
    parse.add_argument("-u", "--user", help="set the user", metavar='', required=True)
    parse.add_argument("-p", "--password", help="set the password", metavar='', required=True)
    parse.add_argument("-m", "--mig-type", help="can be 'users' or ${dbname}", metavar='', default='users',
                       required=True)
    myargs = parse.parse_args()
    host = myargs.host
    port = myargs.port
    user = myargs.user
    passwd = myargs.password
    socket = myargs.socket
    mum = mysqlUserMigrite(host=host, port=port, user=user, passwd=passwd, socket=socket)
    if myargs.mig_type == 'users':
        mum.user_migrate()
