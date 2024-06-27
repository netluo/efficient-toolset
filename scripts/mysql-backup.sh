#!/usr/bin/env bash
# @Time    : 2023/3/15 18:59
# @Author  : chengxiang.luo
# @Email   : andrew.luo1992@gmail.com
# @File    : mysql-backup.sh
# @Software: PyCharm

# mysql data backup script
#
# use mysqldump --help,get more detail.

# 设置变量
DB_NAMES="wordpress halo"
BAK_DIR="/data"
LOG_FILE="/data/mysqlbak.log"
DATETIME=$(date +%Y_%m_%d_%H_%M_%S)
KEEP_DAYS=7

# 设置 MySQL 用户名和密码，如果不希望在脚本中明文写入密码，可以通过其他方式进行设置，如环境变量或者配置文件。
MYSQL_USER="dumper"
MYSQL_PASSWORD="Dumper@123"

# 定义上传备份文件到七牛云的函数
upload_file() {
    local FILE_PATH="$1"
    local REMOTE_PATH="database/$(basename "$FILE_PATH")"
    echo "$(date +'%Y-%m-%d %H:%M:%S') 开始上传备份文件至七牛云存储"
    /usr/bin/qshell fput lingxibak "$REMOTE_PATH" "$FILE_PATH" | sed -r "s/\x1B\[([0-9]{1,2}(;[0-9]{1,2})?)?[m|K]//g"
}

# 备份 MySQL 数据库
BAK_FILE="$BAK_DIR/mysql_bak_$DATETIME.gz"
/usr/bin/mysqldump -h127.0.0.1 -u"$MYSQL_USER" -p"$MYSQL_PASSWORD" --databases wordpress halo | gzip >"$BAK_FILE"

# 输出日志
LOG_MSG="数据库 [$DB_NAMES] 备份完成\n$BAK_FILE"
echo -e "$LOG_MSG" >>"$LOG_FILE"

# 上传备份文件至七牛云存储
upload_file "$BAK_FILE" >>"$LOG_FILE" 2>&1

# 删除旧备份文件
echo "删除${KEEP_DAYS}天前的备份文件" >>"$LOG_FILE"
find "$BAK_DIR" -type f -name "$DB_NAMES*" -mtime +"$KEEP_DAYS" -delete >>"$LOG_FILE" 2>&1

# 输出空行
echo "" >>"$LOG_FILE"
