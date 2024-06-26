#!/usr/bin/env bash
# @Time    : 2023/1/16 13:02
# @Author  : chengxiang.luo
# @Email   : chengxiang.luo@eeoa.com
# @File    : ob-backup.sh
# @Software: PyCharm

DIR_NAME=$(date +'%Y_%m_%d_%H_%M')
LMS_DB_LIST=(eo_oslms eo_oscomment)
EEOWEB_DB_LIST=(eo_classroom eo_oshwlog)
FLOWIN_DB_LIST=(eo_cosys eo_conewbee)
BACKUP_ROOT_DIR=/data1/obback
export JAVA_HOME=/usr/lib/jvm/java-1.8.0-openjdk-1.8.0.342.b07-1.el7_9.x86_64/jre/
mkdir -p $BACKUP_ROOT_DIR/"$DIR_NAME"
cd "$BACKUP_ROOT_DIR/$DIR_NAME" || exit

for DBNAME in "${LMS_DB_LIST[@]}"; do
    {
        mkdir "$DBNAME"
        /usr/local/ob-loader-dumper-3.0.0-RELEASE-ce/bin/obdumper -h 10.0.10.1 -P 2883 -u obdumper_ro -p obdumper_ro --sys-password obdumper_ro -c obcluster -t lms -D "$DBNAME" --thread=32 --all -f "$DBNAME" >lms_"$DBNAME".log 2>&1
        wait
        tar --use-compress-program=pigz -cpf "$DBNAME".tar.gz "$DBNAME" && rm -rf "$DBNAME"
    } &
done

for DBNAME in "${EEOWEB_DB_LIST[@]}"; do
    {
        mkdir "$DBNAME"
        /usr/local/ob-loader-dumper-3.0.0-RELEASE-ce/bin/obdumper -h 10.0.10.1 -P 2883 -u obdumper_ro -p obdumper_ro --sys-password obdumper_ro -c obcluster -t test_tenant -D "$DBNAME" --thread=32 --all -f "$DBNAME" >test_tenant_"$DBNAME".log 2>&1
        wait
        tar --use-compress-program=pigz -cpf "$DBNAME".tar.gz "$DBNAME" && rm -rf "$DBNAME"
    } &
done

for DBNAME in "${FLOWIN_DB_LIST[@]}"; do
    {
        mkdir "$DBNAME"
        /usr/local/ob-loader-dumper-3.0.0-RELEASE-ce/bin/obdumper -h 10.0.10.1 -P 2883 -u obdumper_ro -p obdumper_ro --sys-password obdumper_ro -c obcluster -t test_tenant -D "$DBNAME" --thread=32 --all -f "$DBNAME" >test_tenant_"$DBNAME".log 2>&1
        wait
        tar --use-compress-program=pigz -cpf "$DBNAME".tar.gz "$DBNAME" && rm -rf "$DBNAME"
    } &
done

wait
#上传到 minio
cd "$BACKUP_ROOT_DIR/" || exit
/usr/local/bin/mc cp -q -r "$DIR_NAME" obbackup/db-backup/data/eeo/oceanbase/

# 删除七天前的备份
wait
find /data1/obback/ -mtime +7 -type d -exec rm -rf {} \;
