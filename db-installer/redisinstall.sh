#!/usr/bin/env bash
REDIS_DATA_DIR=/data1
PORT=6379

function predir() {
    REDIS_DATA_DIR=$1
    mkdir -p "$REDIS_DATA_DIR/redis$PORT"/{data,tmp,conf,logs}
}

function get_pkg() {
    wget https://dl.redis/software/redis/redis-6.0.5.tar.gz --no-check-certificate
    tar zxvf redis-6.0.5.tar.gz -C /usr/local/
}

function gen_conf() {
    PORT=$1
    cat <<EOF >$REDIS_DATA_DIR/redis${PORT}/conf/redis${PORT}.conf
bind 0.0.0.0
protected-mode yes
port $PORT
tcp-backlog 511
timeout 0
tcp-keepalive 300
daemonize yes
supervised no
pidfile "$REDIS_DATA_DIR/redis$PORT/tmp/redis$PORT.pid"
loglevel notice
logfile "$REDIS_DATA_DIR/redis$PORT/logs/redis$PORT.log"
databases 16
save 900 1
save 300 10
save 60 10000
stop-writes-on-bgsave-error yes
rdbcompression yes
rdbchecksum yes
dbfilename "dump.rdb"
dir "$REDIS_DATA_DIR/redis$PORT/data"
replica-serve-stale-data yes
replica-read-only yes
repl-diskless-sync no
repl-diskless-sync-delay 5
repl-disable-tcp-nodelay no
replica-priority 100
appendonly no
appendfilename "appendonly.aof"
appendfsync everysec
no-appendfsync-on-rewrite no
auto-aof-rewrite-percentage 100
auto-aof-rewrite-min-size 64mb
aof-load-truncated yes
lua-time-limit 5000
slowlog-log-slower-than 10000
slowlog-max-len 128
latency-monitor-threshold 0
notify-keyspace-events ""
hash-max-ziplist-entries 512
hash-max-ziplist-value 64
list-max-ziplist-size -2
list-compress-depth 0
set-max-intset-entries 512
zset-max-ziplist-entries 128
zset-max-ziplist-value 64
hll-sparse-max-bytes 3000
activerehashing yes
client-output-buffer-limit normal 0 0 0
client-output-buffer-limit replica 0 0 0
client-output-buffer-limit pubsub 0 0 0
hz 10
aof-rewrite-incremental-fsync yes
EOF
}

function redis_is_cluster() {
    cat <<EOF >>$REDIS_DATA_DIR/redis${PORT}/conf/redis${PORT}.conf
cluster-enabled yes
cluster-config-file "nodes-$PORT.conf"
cluster-node-timeout 15000
cluster-require-full-coverage no
EOF
}

function used_password() {
    cat <<EOF >>"$REDIS_DATA_DIR"/redis"${PORT}"/conf/redis"${PORT}".conf
requirepass ee@redis^#**
masterauth "ee@redis^#**"
EOF
}

function set_maxmemory() {
    count=$(grep -c maxmemory "$REDIS_DATA_DIR"/redis"${PORT}"/conf/redis"${PORT}".conf)
    if [ "$count" -eq 1 ]; then
        sed -i "s#^maxmemory.*#maxmemory $1#g" "$REDIS_DATA_DIR"/redis"${PORT}"/conf/redis"${PORT}".conf
    else
        echo "maxmemory $1" >>"$REDIS_DATA_DIR"/redis"${PORT}"/conf/redis"${PORT}".conf
    fi
}

function gen_systemd() {
    PORT=$1
    cat <<EOF >/usr/lib/systemd/system/redis$PORT.service
[Unit]
Description=Redis data structure server
Documentation=https://redis.io/documentation

[Service]
ExecStart=/usr/local/redis-6.0.5/bin/redis-server $REDIS_DATA_DIR/redis$PORT/conf/redis$PORT.conf
LimitNOFILE=65535
NoNewPrivileges=yes
Type=forking
TimeoutStartSec=10
TimeoutStopSec=10
UMask=0077
User=root
Group=root

[Install]
WantedBy=multi-user.target
EOF
}

while getopts "d:p:am:igcsh" opt; do
    case $opt in
    d)
#        echo "$(date +'%F %T') : pre dir"
        predir "$OPTARG"
        ;;
    p)
#        echo "$(date +'%F %T') : pre dir"
        PORT="$OPTARG"
        ;;
    m)
        echo "$(date +'%F %T') : set redis maxmemory (M)."
        MAX_MEMORY=$(($OPTARG * 1024 * 1024))
        echo "maxmemory set to $MAX_MEMORY"
        set_maxmemory $MAX_MEMORY
        ;;
    i)
        echo "$(date +'%F %T') : get pg and make install "
        cd /tmp && get_pkg
        ;;
    g)
        echo "$(date +'%F %T') : generate my.cnf , systemd"
        gen_conf $PORT && gen_systemd $PORT
        systemctl daemon-reload && systemctl enable redis"$PORT".service
        ;;
    a)
        echo "$(date +'%F %T') : set redis password."
        used_password
        ;;
    c)
        echo "$(date +'%F %T') : install redis as a member of cluster"
        redis_is_cluster
        ;;
    s)
        echo "$(date +'%F %T') : start redis "
        systemctl start redis"$PORT".service
        ;;
    h | *)
        echo "$0 -d \$datadir -p \$port [OPTARG]"
        echo "OPTARG :"
        echo "      -h            show help"
        echo "      -p            set redis port"
        echo "      -d            set redis datadir, default /data1"
        echo "      -m            set redis maxmemory (M)"
        echo "      -i            get redis software"
        echo "      -g            generate redis cnf file and systemd file"
        echo "      -c            redis as cluster member "
        echo "      -a            redis use password "
        echo "      -s            start redis service"
        echo "step  :"
        echo "$0 -d \$datadir -p \$port"
        echo "      1. -g "
        echo "      2. -m \$maxmemory (mb)"
        echo "      3. -a if password is is used"
        echo "      4. -c if this node is a cluster node"
        echo "      5. -i to install redis"
        echo "      6. -s start redis service"
        ;;
    esac
done
