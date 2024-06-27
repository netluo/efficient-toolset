#!/usr/bin/env bash
# @Time    : 2022/7/5 16:23
# @Author  : chengxiang.luo
# @Email   : andrew.luo1992@gmail.com
# @File    : truncat_bigfile.sh
# @Software: PyCharm

TRUNCATE=/usr/bin/truncate
FILE=$1

if [ x"$1" = x ]; then
    echo "Please input filename in"
    exit 1
else
    SIZE_M=$(du -sm "$1" | awk '{print $1}')
    # 2000 表示每次删除2000m
    for i in $(seq "${SIZE_M}" -2000 0); do
        sleep 1
        echo "${TRUNCATE} -s ${i}M ${FILE}"
        ${TRUNCATE} -s "${i}"M "${FILE}"
    done
fi

if [ $? -eq 0 ]; then
    \rm -f "${FILE}"
else
    echo "Please check file"
fi
