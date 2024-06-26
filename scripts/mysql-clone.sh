#!/usr/bin/env bash

CLONE_ADMIN_USER="clone_user@'172.16.250.%'"
CLONE_ADMIN_PASSWORD="clone_user"
CLONE_VALID_DONOR_LIST="172.16.250.231"
MYSQL_DONOR_PORT=61106
MYSQL_LOCAL_PORT=61106
ROOT_PASSWORD="Passw0rd"
MYSQLCNF=/etc/my.cnf
DATADIR=$(grep datadir $MYSQLCNF | awk -F'=' '{print $2}')

# 仅支持GTID模式
# GTID_MODE=1
#删除旧文件
function del_old_file() {
    systemctl stop mysqld && rm -rf /data/logs/services/mysql/* && $(find $DATADIR -type d | xargs rm -rf) && rm -rf /data/data/services/mysql/binlog/* && rm -rf /data/data/services/mysql/relaylog/*
}

function start_mysqld() {
    systemctl start mysqld
    OLD_PASSWORD=$(grep 'temporary password' /data/logs/services/mysql/mysqld.log | awk '{printf $NF}')
    SET_PASSWD_TXT="set global validate_password.policy='LOW';alter user root@localhost identified by '${ROOT_PASSWORD}';"
    mysql -h localhost -P${MYSQL_LOCAL_PORT} -uroot -p${OLD_PASSWORD} -e "${SET_PASSWD_TXT}" --connect-expired-password
}

function install_plugin() {
    INSTALL_PLUGIN_SQL="INSTALL PLUGIN clone SONAME 'mysql_clone.so'"
    mysql -h localhost -P${MYSQL_LOCAL_PORT} -uroot -p${ROOT_PASSWORD} -e "${INSTALL_PLUGIN_SQL}" --connect-expired-password
}
function set_clone_user() {
    SET_CLONE_USER_SQL="set global validate_password.policy='LOW';CREATE USER IF NOT EXISTS ${CLONE_ADMIN_USER} IDENTIFIED by '${CLONE_ADMIN_PASSWORD}';GRANT BACKUP_ADMIN,CLONE_ADMIN ON *.* TO ${CLONE_ADMIN_USER};"
    mysql -h localhost -P${MYSQL_LOCAL_PORT} -uroot -p${ROOT_PASSWORD} -e "${SET_CLONE_USER_SQL}" --connect-expired-password
}

function begin_clone() {
    date +'%F %T'
    CLONE_SQL="SET GLOBAL clone_valid_donor_list = '${CLONE_VALID_DONOR_LIST}:${MYSQL_DONOR_PORT}';CLONE INSTANCE FROM clone_user@'${CLONE_VALID_DONOR_LIST}':${MYSQL_LOCAL_PORT} IDENTIFIED BY 'clone_user';"
    mysql -h localhost -P${MYSQL_LOCAL_PORT} -uroot -p${ROOT_PASSWORD} -e "${CLONE_SQL}" --connect-expired-password && date +'%F %T' && echo "CLONE ENDS ... "
}
#function change_master() {
#    CHANGE_MASTER_SQL="STOP SLAVE;CHANGE MASTER TO MASTER_HOST='${CLONE_VALID_DONOR_LIST}', MASTER_PORT=${MYSQL_LOCAL_PORT} ,MASTER_USER='repl',MASTER_PASSWORD='repl20150602',MASTER_LOG_FILE='',  MASTER_LOG_POS=;START SLAVE;"
#    mysql -h localhost -P${MYSQL_LOCAL_PORT} -uroot -p${ROOT_PASSWORD} -e "${CHANGE_MASTER_SQL}" --connect-expired-password
#}

function execute_all() {
    del_old_file
    start_mysqld
    install_plugin
    set_clone_user
    begin_clone
    change_master
}
function usage() {
    echo "mysql-clone {-h|-d|-s|-u|-c|-m|-a}"
    echo "del_old_file(-d)                  -- stop mysqld and delete old mysql-datafiles"
    echo "start_mysqld(-s)                  -- start mysqld and set newpassword"
    echo "install_plugin(-i)                -- install clone plgin"
    echo "set_clone_user(-u)                -- set clone user"
    echo "begin_clone(-c)                   -- set clone donor and clone"
    echo "change_master(-m)                 -- change master"
    echo "execute_all(-a)                   -- execute all"
}

case "$1" in
'-d')
    del_old_file
    ;;
'-s')
    start_mysqld
    ;;
'-i')
    install_plugin
    ;;
'-u')
    set_clone_user
    ;;
'-c')
    begin_clone
    ;;
'-m')
    change_master
    ;;
'-a')
    execute_all
    ;;
*)
    usage
    ;;
esac
