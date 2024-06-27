#!/usr/bin/env bash
PGBASEDIR=/data1/pg5432
PGUSER=postgres
PGGROUP=postgres
PGDATA=$PGBASEDIR/pgdata
PGVERSION='14.2'
PGHOME=/usr/local/postgresql-$PGVERSION
MAXCONN=1000

function prepare_dir() {
    mkdir -p $PGBASEDIR/{pgdata,archive,scripts,backup,soft,conf,logs}
    mkdir $PGHOME
    chown -R $PGUSER.$PGGROUP $PGBASEDIR
}

function prepare_user() {
    groupadd $PGGROUP
    useradd -g $PGGROUP $PGUSER
    chown -R $PGUSER.$PGGROUP $PGBASEDIR
}

function prepare_libs() {
    yum install systemd-devel python3-devel python-devel readline-devel zlib-devel -y
}

function pg_make() {
    wget https://dl.test-inc.com/software/mysql/postgresql-$PGVERSION.tar.gz --no-check-certificate
    tar zxvf postgresql-$PGVERSION.tar.gz && cd postgresql-$PGVERSION || exit
    ./configure --prefix=$PGHOME --with-python --enable-debug --with-systemd
    make all && make install
    cd contrib && make all && make install
}

function init_db() {
    su - $PGUSER -c "initdb -D $PGDATA -E UTF8 --locale=en_US.UTF8 -U $PGUSER"
}

function make_conf() {
    echo "include '$PGBASEDIR/conf/my.conf'" >>$PGDATA/postgresql.conf
#    mv $PGDATA/{pg_hba.conf,pg_ident.conf} $PGBASEDIR/conf/
}

function pg_base_bak() {
    # create user repl login replication ENCRYPTED PASSWORD 'repl1234';
    pg_basebackup -h 192.168.32.128 -p 5432 -U repl -F p -P -R -X stream -D $PGBASEDIR/pgdata -W
}

function gen_conf() {
    CPU_NUM=$(cat /proc/cpuinfo | grep processor | wc -l)
    TOTALMEM=$(free -m | grep Mem | awk '{print $2}')
    cat <<EOF >$PGBASEDIR/conf/my.conf
wal_level= replica
archive_mode=on
#
archive_command='test ! -f /postgresql/archive/%f || cp %p /postgresql/archive/%f'
listen_addresses = '*'
max_wal_senders=10
wal_sender_timeout=60s
#primary_conninfo = ''
max_replication_slots=10
wal_log_hints=on

## loggile
log_destination = 'csvlog'
logging_collector = on
log_directory = '$PGBASEDIR/logs'
log_filename = 'postgresql-%Y-%m-%d_%H%M%S.log'
log_file_mode = 0600
log_rotation_age = 1d
log_rotation_size = 512MB
log_min_messages = info
# 记录执行慢的SQL
# 慢查询阈值，查询时间超过阈值被定义为慢查询，单位毫秒
log_min_duration_statement = 60
log_checkpoints = on
log_connections = on
log_disconnections = on
log_duration = on
log_lock_waits = on

## log DDL	##
log_statement = 'ddl'

data_directory='$PGBASEDIR/pgdata'
hba_file = '$PGBASEDIR/conf/pg_hba.conf'
ident_file = '$PGBASEDIR/conf/pg_ident.conf'
unix_socket_directories = '$PGBASEDIR/pgdata'

max_connections = 200
shared_buffers = $((TOTALMEM / 4))MB
effective_cache_size = $((TOTALMEM * 3 / 4))MB
maintenance_work_mem = $((TOTALMEM / 16))MB
checkpoint_completion_target = 0.9
wal_buffers = 16MB
default_statistics_target = 100
random_page_cost = 1.1
effective_io_concurrency = 200
work_mem = $((TOTALMEM / 16 / $MAXCONN * CPU_NUM))MB
min_wal_size = 1GB
max_wal_size = 4GB
max_worker_processes = $CPU_NUM
max_parallel_workers_per_gather = $((CPU_NUM / 2))
max_parallel_workers = $CPU_NUM
max_parallel_maintenance_workers = $((CPU_NUM / 2))
EOF
}

function gen_systemd() {
    cat <<EOF >/usr/lib/systemd/system/postgresql-14.service
[Unit]
Description=PostgreSQL 14 database server
Documentation=https://www.postgresql.org/docs/14/static/

[Service]
Type=notify

User=postgres
Group=postgres
ExecStart=$PGHOME/bin/postmaster -D $PGDATA
ExecReload=/bin/kill -HUP \$MAINPID
KillMode=mixed
KillSignal=SIGINT
TimeoutSec=0

[Install]
WantedBy=multi-user.target
EOF
}

function set_bashprofile() {
    cat <<EOF >>/home/postgres/.bash_profile
export LANG=en_US.UTF8
export PGPORT=5432
export PGDATA=$PGDATA
export PGHOME=$PGHOME
export LD_LIBRARY_PATH=\$PGHOME/lib:/lib64:/usr/lib64:/usr/local/lib64:/lib:/usr/lib:/usr/local/lib:$LD_LIBRARY_PATH
export PATH=\$PGHOME/bin:$PATH:.
export DATE=\$(date +"%Y%m%d%H%M")
export MANPATH=\$PGHOME/share/man:$MANPATH
export PGHOST=\$PGDATA
export PGUSER=postgres
export PGDATABASE=postgres
EOF
}

function set_passwd() {
    # su - postgres -c "psql -c 'alter user postgres ENCRYPTED password \'!!)a1106'"
    echo "Please set password Manually"
}

while getopts "udlmgirh" opt; do
    case $opt in
    u)
        echo "$(date +'%F %T') : preuser"
        prepare_user
        ;;
    d)
        echo "$(date +'%F %T') : predir"
        prepare_dir
        ;;
    l)
        echo "$(date +'%F %T') : install dependencies ."
        prepare_libs
        ;;
    m)
        echo "$(date +'%F %T') : get pg and make install "
        pg_make
        ;;
    g)
        echo "$(date +'%F %T') : generate my.cnf , systemd"
        gen_conf && gen_systemd && set_bashprofile
        systemctl daemon-reload && systemctl enable postgresql-14.service
        ;;
    i)
        echo "$(date +'%F %T') : init postgres data"
        init_db && make_conf
        ;;
    r)
        echo "$(date +'%F %T') : set root password "
        set_root_user
        ;;
    h | *)
        echo "$0 -udlmgir"
        echo "      -h            show help"
        echo "      -u            set os user : postgres"
        echo "      -d            set os postgres datadir"
        echo "      -l            install postgres dependencies"
        echo "      -m            get postgres software"
        echo "      -g            generate postgressql.conf , systemd"
        echo "      -i            init postgres"
        echo "      -r            set postgres root user's password"
        echo "step  :"
        echo "      1. -u "
        echo "      2. -d "
        echo "      3. -l "
        echo "      4. -m "
        echo "      5. -g "
        echo "      6. -i "
        ;;
    esac
done
