#!/usr/bin/env bash
MONGO_DATA_DIR=/data1
PORT=27017

function predir() {
    MONGO_DATA_DIR=$1
    mkdir -p "$MONGO_DATA_DIR/mongo$PORT"/{data,tmp,conf,logs}
}

function get_pkg() {
    wget https://dl.mongo.com/software/mongo/mongo-4.2.20.tar.gz --no-check-certificate
    tar zxvf mongo-4.2.20.tar.gz -C /usr/local/
}

function gen_conf() {
    PORT=$1
    cat <<EOF >"$MONGO_DATA_DIR"/mongo"${PORT}"/conf/mongo"${PORT}".conf
systemLog:
  destination: file
  logAppend: true
  logRotate: reopen
  path: $MONGO_DATA_DIR/mongodb$PORT/log/mongodb.log

storage:
  dbPath: $MONGO_DATA_DIR/mongodb$PORT/data
  journal:
    enabled: true
  directoryPerDB: true
  syncPeriodSecs: 60
  engine: wiredTiger
  wiredTiger:
    engineConfig:
      cacheSizeGB: $CACHE_SIZE
      journalCompressor: "snappy"
      directoryForIndexes: true
    collectionConfig:
      blockCompressor: "snappy"
    indexConfig:
      prefixCompression: true

operationProfiling:
   slowOpThresholdMs: 50
   mode: "all"

processManagement:
  fork: true
  pidFilePath: $MONGO_DATA_DIR/mongodb$PORT/tmp/mongodb.pid

net:
  port: $PORT
  bindIp: 0.0.0.0
  maxIncomingConnections: 18500

security:
  keyFile: $MONGO_DATA_DIR/mongodb$PORT/conf/keyfile

replication:
  replSetName: picturebook
  oplogSizeMB: 50240
  secondaryIndexPrefetch: all

setParameter:
  enableLocalhostAuthBypass: true
  replWriterThreadCount: 32
  wiredTigerConcurrentReadTransactions: 1000
  wiredTigerConcurrentWriteTransactions: 1000
EOF
}

#function mongo_is_cluster() {
#
#}

function used_password() {
    cat <<EOF >>"$MONGO_DATA_DIR"/mongo"${PORT}"/conf/mongo"${PORT}".conf
requirepass passw0rd
masterauth "passw0rd"
EOF
}

function set_maxmemory() {
    count=$(grep -c cacheSizeGB "$MONGO_DATA_DIR"/mongo"${PORT}"/conf/mongo"${PORT}".conf)
    if [ $count -eq 1 ]; then
        sed -i "s#cacheSizeGB.*#cacheSizeGB $1#g" "$MONGO_DATA_DIR"/mongo"${PORT}"/conf/mongo"${PORT}".conf
    else
        echo "failed to set cacheSizeGB"
        exit 1
    fi
}

function gen_systemd() {
    PORT=$1
    cat <<EOF >/usr/lib/systemd/system/mongo$PORT.service
###
[Unit]
Description=MongoDB Database Server
Documentation=https://docs.mongodb.org/manual
After=network.target

[Service]
User=mongod
Group=mongod
Environment="OPTIONS=-f $MONGO_DATA_DIR/mongo$PORT/conf/mongod.conf"
EnvironmentFile=-/etc/sysconfig/mongod
ExecStart=/usr/bin/mongod $OPTIONS
PermissionsStartOnly=true
PIDFile=$MONGO_DATA_DIR/mongo$PORT/tmp/mongod.pid
Type=forking
# file size
LimitFSIZE=infinity
# cpu time
LimitCPU=infinity
# virtual memory size
LimitAS=infinity
# open files
#LimitNOFILE=64000
# processes/threads
#LimitNPROC=64000
# locked memory
LimitMEMLOCK=infinity
# total threads (user+kernel)
TasksMax=infinity
TasksAccounting=false
# Recommended limits for for mongod as specified in
# http://docs.mongodb.org/manual/reference/ulimit/#recommended-settings

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
        echo "$(date +'%F %T') : set mongo maxmemory (M)."
        MAXMEMORY=$(($OPTARG * 1024 * 1024))
        echo "maxmemory set to $MAXMEMORY"
        set_maxmemory $MAXMEMORY
        ;;
    i)
        echo "$(date +'%F %T') : get pg and make install "
        cd /tmp && get_pkg
        ;;
    g)
        echo "$(date +'%F %T') : generate mongo.cnf , systemd"
        gen_conf $PORT && gen_systemd $PORT
        systemctl daemon-reload && systemctl enable mongo"$PORT".service
        ;;
    a)
        echo "$(date +'%F %T') : set mongo password."
        used_password
        ;;
    c)
        echo "$(date +'%F %T') : install mongo as a member of cluster"
        mongo_is_cluster
        ;;
    s)
        echo "$(date +'%F %T') : start mongo "
        systemctl start mongo"$PORT".service
        ;;
    h | *)
        echo "$0 -d \$datadir -p \$port [OPTARG]"
        echo "OPTARG :"
        echo "      -h            show help"
        echo "      -p            set mongo port"
        echo "      -d            set mongo datadir, default /data1"
        echo "      -m            set mongo cacheSizeGB (G)"
        echo "      -i            get mongo software"
        echo "      -g            generate mongo cnf file and systemd file"
        echo "      -c            mongo as cluster member "
        echo "      -a            mongo use password "
        echo "      -s            start mongo service"
        echo "step  :"
        echo "$0 -d \$datadir -p \$port"
        echo "      1. -g "
        echo "      2. -m \$cacheSizeGB (GB)"
        echo "      3. -a if password is is used"
        echo "      4. -c if this node is a cluster node"
        echo "      5. -i to install mongo"
        echo "      6. -s start mongo service"
        ;;
    esac
done
