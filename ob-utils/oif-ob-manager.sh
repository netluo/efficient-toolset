#!/usr/bin/env bash
# @Time    : 2022/10/20 10:20
# @Author  : chengxiang.luo
# @Email   : chengxiang.luo@eeoa.com
# @File    : oif-ob-manager.sh
# @Software: PyCharm

HOST='10.0.2.114'
PORT=2883
USER='root'
TENANT_NAME=''
CLUSTER_NAME='obcluster'
PASSWORD='Passw0rd'
TEMP=$(getopt -o h:P:u:t:C:p:D:sc --long host:,port:,user:,tenant:,cluster,password:,database:,show,connect,help -n "$0" -- "$@")

if [ $? != 0 ]; then
    echo "Terminating..." >&2
    exit 1
fi
#
## Note the quotes around `$TEMP': they are essential!
##set 会重新排列参数的顺序，也就是改变$1,$2...$n的值，这些值在getopt中重新排列过了
eval set -- "$TEMP"

function user_conn() {
    obclient -h${HOST:-127.0.0.1} -P${PORT:-2881} -u${USER:-root}@"${TENANT_NAME}"'#'${CLUSTER_NAME:-} -p"${PASSWORD}" -D"${DBNAME:-oceanbase}" -A -c
    # :- 表示当变量为null 或 空字符串时取默认值
    # :- 表示当变量为null取默认值
}

function get_all_tenant() {
    obclient -h${HOST} -P${PORT} -u${USER:-root}@"${TENANT_NAME}"'#'${CLUSTER_NAME:-} -p"${PASSWORD}" -Doceanbase -A -e 'select tenant_id,tenant_name,primary_zone from __all_tenant'
}

function useage() {
    echo "a tool for ob connect
    -h | --host
    -P | --port
    -u | --user
    -p | --password
    -s | --show
    -D | --database
    -t | --tenant
    -C | --cluster
    -c | --connect"
}

while true; do
    case "$1" in
    -h | --host)
        HOST="$2"
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
    -p | --password)
        PASSWORD=$2
        shift 2
        ;;
    -s | --show)
        shift 1
        ;;
    -D | --database)
        DBNAME=$2
        shift 2
        ;;
    -t | --tenant)
        TENANT_NAME=$2
        shift 2
        ;;
    -C | --cluster)
        CLUSTER_NAME=$2
        shift 2
        ;;
    -c | --connect)
        user_conn
        shift
        ;;
    --help)
        useage
        shift
        ;;
    --)
        shift
        break
        ;;
    esac
done
