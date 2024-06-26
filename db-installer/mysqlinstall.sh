#!/usr/bin/env bash
# version 1.3
MYSQL_VERSION=8.0.20
SERVER_ID=$(hostname -I | awk '{print $1}' | awk -F '.' '{print $NF}')
MYSQL_HOME=/usr/local/mysql-${MYSQL_VERSION}
MYSQL_GZ=mysql-${MYSQL_VERSION}-el7-x86_64.tar.gz
TOTAL_MEM=$(free -m | grep Mem | awk '{print $2}')

if [ "$TOTAL_MEM" -gt 129024 ]; then
    MYSQL_BUFFER_POOL='90G'
else
    res="$((TOTAL_MEM * 6 / 10))"
    MYSQL_BUFFER_POOL=$(awk -v a=$res 'BEGIN{print(int(a)==(a))?int(a):int(a)+1}')M
fi

function pre_user() {
    groupadd -g 27 mysql
    useradd -u 27 -g 27 --no-create-home --shell /bin/false --comment 'MySQL Server' mysql
}

function pre_dir() {
    mkdir -p $MYSQL_HOME
    mkdir -p "$DATA_DIR"/{binlog,conf,data,logs,relaylog,scripts,tmp}
    chown -R mysql.mysql "$DATA_DIR"
}

function pre_share_lib() {
    yum install numactl-libs.x86_64 libaio-devel -y
}

function get_mysql() {
    # 官方镜像源
    # wget https://cdn.mysql.com/archives/mysql-8.0/mysql-8.0.20-el7-x86_64.tar.gz
    cd /tmp && wget https://dl.eeo-inc.com/software/mysql/$MYSQL_GZ
    tar zxvf /tmp/$MYSQL_GZ -C /usr/local
}

function generate_my_cnf() {
    cat <<EOF >"$DATA_DIR"/conf/my.cnf
# mysql: 8.0.20
# version: 2020-05-29

[client]
socket                                                   =$DATA_DIR/tmp/mysql.sock
port                                                     =$MYSQL_PORT
host                                                     =127.0.0.1
prompt                                                   =eeo[\\\\u@\\\\h:(\\\\d) \\\\R:\\\\m:\\\\s]>
default-character-set                                    =utf8mb4

[mysqld]
character-set-client-handshake                           =False
character-set-server                                     =utf8mb4
collation-server                                         =utf8mb4_unicode_ci
init-connect                                             ='SET NAMES utf8mb4'

basedir                                                  =/usr/local/mysql-8.0.20
socket                                                   =$DATA_DIR/tmp/mysql.sock
pid_file                                                 =$DATA_DIR/tmp/mysql.pid
slow_query_log_file                                      =$DATA_DIR/logs/slow.log
log_error                                                =$DATA_DIR/logs/mysqld.log
general_log_file                                         =$DATA_DIR/logs/general.log
datadir                                                  =$DATA_DIR/data
port                                                     =$MYSQL_PORT
mysqlx_port                                              =$MYSQLX_PORT
mysqlx_socket                                            =$DATA_DIR/tmp/mysqlx.sock
user                                                     =mysql
default_storage_engine                                   =InnoDB
skip_name_resolve                                        =ON

### 慢查询
#log_queries_not_using_indexes                           =ON
long_query_time                                          =1
slow_query_log                                           =on

###binlog
log_bin                                                  =$DATA_DIR/binlog/mysql-bin
log_bin_index                                            =$DATA_DIR/binlog/mysql-bin.index
sync_binlog                                              =0
binlog_format                                            =row
binlog_cache_size                                        =64K
binlog_rows_query_log_events                             =1
# 代替expire_logs_days=7
binlog_expire_logs_seconds                               =604800
binlog_checksum                                          =CRC32
binlog_ignore_db                                         =mysql
binlog_ignore_db                                         =information_schema
binlog_ignore_db                                         =performance_schema

###relaylog
relay_log                                                =$DATA_DIR/relaylog/relay-log
relay_log_index                                          =$DATA_DIR/relaylog/relay-log.index
relay_log_info_repository                                =TABLE

###replication
server_id                                                =$SERVER_ID
auto_increment_increment                                 =1
auto_increment_offset                                    =1
sync_master_info                                         =1

###master
master_info_repository                                   =TABLE
log_slave_updates                                        =true
master_verify_checksum                                   =1

###slave
# 2018/12/20 MTS
slave_parallel_workers                                   =4
slave_parallel_type                                      =LOGICAL_CLOCK
binlog_group_commit_sync_delay                           =100
binlog_group_commit_sync_no_delay_count                  =10

slave_sql_verify_checksum                                =1
#slave_skip_errors                                       =1062
#relay_log_recovery                                      =0
slave_pending_jobs_size_max                              =128M

###global
max_connect_errors                                       =999999
max_connections                                          =30000
thread_cache_size                                        =256
#open_files_limit                                        =65535
table_open_cache                                         =30000

###myisam
key_buffer_size                                          =1G
bulk_insert_buffer_size                                  =16M

###innodb
innodb_open_files                                        =60000
innodb_buffer_pool_size                                  =$MYSQL_BUFFER_POOL
innodb_buffer_pool_instances                             =8
innodb_flush_log_at_trx_commit                           =0
innodb_flush_method                                      =O_DIRECT
innodb_io_capacity                                       =1800
innodb_read_io_threads                                   =8
innodb_write_io_threads                                  =8
innodb_file_per_table                                    =ON
innodb_rollback_on_timeout                               =ON
innodb_log_files_in_group                                =3
innodb_log_file_size                                     =1G

###session
join_buffer_size                                         =4M
max_heap_table_size                                      =16M
tmp_table_size                                           =16M
read_buffer_size                                         =4M
read_rnd_buffer_size                                     =16M
sort_buffer_size                                         =4M
net_read_timeout                                         =3600
net_write_timeout                                        =3600
max_allowed_packet                                       =64M
wait_timeout                                             =86400
lock_wait_timeout                                        =180
sql_mode                                                 =STRICT_TRANS_TABLES,NO_ENGINE_SUBSTITUTION
report_host                                              =$(hostname -I | awk '{print $1}')

### other
# 解决日志时间问题（+8）
log_timestamps                                           =SYSTEM
default_authentication_plugin                            =mysql_native_password
explicit_defaults_for_timestamp
# GTID
gtid-mode                                                =ON
enforce-gtid-consistency                                 =ON

#error:too many connent
## admin port login
admin_address                                            =127.0.0.1
admin_port                                               =$MYSQL_ADMIN_PORT
create_admin_listener_thread                             =ON

[mysqld_safe]
log_error                                                =$DATA_DIR/logs/mysqld.log
pid_file                                                 =$DATA_DIR/tmp/mysqld.pid

[innobackupex]
open-files-limit                                         =2000000
EOF
    if [ -f /etc/my.cnf ]; then
        echo "The link exist, pass."
    else
        ln -s "$DATA_DIR"/conf/my.cnf /etc/my.cnf
    fi
}

function generate_systemd() {
    cat <<EOF >/usr/lib/systemd/system/mysqld$MYSQL_PORT.service
[Unit]
Description=MySQL Server
Documentation=man:mysqld(8)
Documentation=http://dev.mysql.com/doc/refman/en/using-systemd.html
After=network.target
After=syslog.target
[Install]
WantedBy=multi-user.target
[Service]
User=mysql
Group=mysql
TimeoutSec=0
PermissionsStartOnly=true
#ExecStartPre=/usr/bin/mysqld_pre_systemd
ExecStart=$MYSQL_HOME/bin/mysqld_safe --defaults-file=$DATA_DIR/conf/my.cnf
EnvironmentFile=-/etc/sysconfig/mysql
Environment=MYSQLD_PARENT_PID=1
PrivateTmp=false
EOF
    systemctl daemon-reload && systemctl enable mysqld"$MYSQL_PORT".service
    echo "export PATH=\$PATH:$MYSQL_HOME/bin" >>/etc/profile.d/mysql.sh
    echo "export LD_LIBRARY_PATH=\$LD_LIBRARY_PATH:$MYSQL_HOME/lib" >>/etc/profile.d/mysql.sh
    source /etc/profile.d/mysql.sh
}

function init_mysql() {
    $MYSQL_HOME/bin/mysqld --defaults-file="$DATA_DIR"/conf/my.cnf --initialize --user=mysql --initialize-insecure
    systemctl start mysqld"$MYSQL_PORT".service
    SET_ROOT_PWD_SQL="alter user root@'localhost' identified by '!!)a1106';"
    echo "$SET_ROOT_PWD_SQL"
    mysql -h localhost -P"$MYSQL_PORT" -S "$DATA_DIR"/tmp/mysql.sock -uroot -e"$SET_ROOT_PWD_SQL"
}

while getopts "p:udhlmgi" opt; do
    case $opt in
    p)
        MYSQL_PORT=$OPTARG
        MYSQLX_PORT=$((MYSQL_PORT + 2))
        MYSQL_ADMIN_PORT=$((MYSQL_PORT + 1))
        DATA_DIR=/data1/mysql${MYSQL_PORT}
        ;;
    u)
        echo "$(date +'%F %T') : preuser"
        pre_user
        ;;
    d)
        echo "$(date +'%F %T') : predir"
        pre_dir
        ;;
    l)
        echo "$(date +'%F %T') : install dependencies ."
        pre_share_lib
        ;;
    m)
        echo "$(date +'%F %T') : get mysql and tar zxvf "
        get_mysql
        ;;
    g)
        echo "$(date +'%F %T') : generate my.cnf , systemd"
        generate_my_cnf && generate_systemd
        ;;
    i)
        echo "$(date +'%F %T') : init mysql and set root password."
        init_mysql
        ;;

    h | *)
        echo "$0 -p $PORT -udlmgir"
        echo "      egg: $0 -p \$PORT -u -d -l -m -g -i -r"
        echo "      -h            show help"
        echo "      -u            set os user : mysql"
        echo "      -d            set os mysql data dir"
        echo "      -l            install mysql dependencies"
        echo "      -m            get mysql software"
        echo "      -g            generate my.cnf , systemd"
        echo "      -i            init mysql and set mysql root user's password"
        ;;
    esac
done
