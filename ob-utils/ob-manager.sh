#!/bin/bash

IP='10.0.9.161'
PORT=2881
USER='root'
TENANT_NAME=sys
CLUSTERNAME=
PASSWORD=
TEMP=$(getopt -o ch:P:u:t:p: --long connect,host:,port:,user:tenant:password: -n 'example.bash' -- "$@")

if [ $? != 0 ]; then
  echo "Terminating..." >&2
  exit 1
fi

# Note the quotes around `$TEMP': they are essential!
#set 会重新排列参数的顺序，也就是改变$1,$2...$n的值，这些值在getopt中重新排列过了
eval set -- "$TEMP"

function start_cluster() {
    obd cluster start obcluster
}

function user_conn() {
    dbname=$2
    obclient -h${IP:-127.0.0.1} -uroot@${TENANT_NAME}${#CLUSTERNAME:-} -P${PORT:-2881} -p"${PASSWORD}" -D"${dbname:-oceanbase}" -A
    # :- 表示当变量为null 或 空字符串时取默认值
    # :- 表示当变量为null取默认值
}

function stop_cluster() {
    obd cluster stop obcluster
}

function get_all_tenant() {
    obclient -h 127.0.0.1 -P 2883 -uroot@sys#eoobce -proot123 -Doceanbase -A -e 'select tenant_id,tenant_name,primary_zone from __all_tenant'
}

case "$1" in
    'start')
#        start_cluster
        echo "start"
        ;;
    -h | --host)
        IP=$2
        shift 2
        ;;
    -P | --port)
        PORT=$2
        shift 2
        ;;
    -u | --user)
        USER=$2
        shift 2
        ;;
    'stop')
        stop_cluster
        ;;
    *)
        echo "ob-manager start|-u|stop ..."
        echo "ob-manager -u [tenant] [database]"
esac