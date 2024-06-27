#!/usr/bin/env bash
# @Time    : 2022/11/27 10:16
# @Author  : chengxiang.luo
# @Email   : andrew.luo1992@gmail.com
# @File    : clear_lms_topic.sh.sh
# @Software: PyCharm

function add_topic() {
    # ob-eooslms-eooshw-c0到8
    for i in $(seq 0 8); do
        kafka-topics.sh --bootstrap-server "$BROKER_IP":9092 --config retention.ms=604800000 --create --partitions 1 --replication-factor 3 --config min.insync.replicas=2 --topic ob-eooslms-eooshw-c$i
    done
    # ob-eooslms-eoosexam-c0到8
    for i in $(seq 0 8); do
        kafka-topics.sh --bootstrap-server "$BROKER_IP":9092 --config retention.ms=604800000 --create --partitions 1 --replication-factor 3 --config min.insync.replicas=2 --topic ob-eooslms-eoosexam-c$i
    done
    kafka-topics.sh --bootstrap-server "$BROKER_IP":9092 --config retention.ms=604800000 --create --partitions 1 --replication-factor 3 --config min.insync.replicas=2 --topic ob-eooslms-eoos
    kafka-topics.sh --bootstrap-server "$BROKER_IP":9092 --config retention.ms=604800000 --create --partitions 1 --replication-factor 3 --config min.insync.replicas=2 --topic ob-eooslms-eooshw
    kafka-topics.sh --bootstrap-server "$BROKER_IP":9092 --config retention.ms=604800000 --create --partitions 1 --replication-factor 3 --config min.insync.replicas=2 --topic ob-eooslms-eoosexam
}

function del_topic() {
    for i in $(seq 0 8); do
        kafka-topics.sh --bootstrap-server "$BROKER_IP":9092 --delete --topic ob-eooslms-eoosexam-c$i
    done

    for i in $(seq 0 8); do
        kafka-topics.sh --bootstrap-server "$BROKER_IP":9092 --delete --topic ob-eooslms-eooshw-c$i
    done
    kafka-topics.sh --bootstrap-server "$BROKER_IP":9092 --delete --topic ob-eooslms-eoos
    kafka-topics.sh --bootstrap-server "$BROKER_IP":9092 --delete --topic ob-eooslms-eooshw
    kafka-topics.sh --bootstrap-server "$BROKER_IP":9092 --delete --topic ob-eooslms-eoosexam
}

function get_topic() {
    kafka-topics.sh --bootstrap-server "$BROKER_IP":9092 --list | grep eooslms-eoos
}

while getopts "gab:dh" opt; do
    case $opt in
    b)
        BROKER_IP=$OPTARG
        ;;
    g)
        get_topic
        ;;
    a)
        add_topic
        ;;
    d)
        del_topic
        ;;
    h | *)
        echo "$0 -adgh"
        echo "      egg: $0 -adgh"
        echo "      -h            show help"
        echo "      -b            set broker ip"
        echo "      -a            add topic"
        echo "      -d            delete topic"
        echo "      -g            get topic"
        ;;
    esac
done