#!/usr/bin/env bash
# @Time    : 2022/11/23 15:57
# @Author  : chengxiang.luo
# @Email   : andrew.luo1992@gmail.com
# @File    : ocp-alarm.sh.sh
# @Software: PyCharm

# should contains shebang in first line, only python/bash are supported

echo "Below is a list of alarm paras"

# below variables can be referenced by prefix "$", for example, $alarm_name or ${alarm_name}

echo "alarm_name:$alarm_name"
echo "app_type:$app_type"
echo "alarm_threshold:$alarm_threshold"
echo "alarm_time=$alarm_time"
echo "alarm_last_interval:$alarm_last_interval"
echo "alarm_time:$alarm_time"
echo "alarm_level:$alarm_level"
echo "alarm_type:$alarm_type"
echo "alarm_summary:$alarm_summary"
echo "alarm_url:$alarm_url"
echo "app:$app"
echo "alarm_duration:$alarm_duration"
echo "alarm_status:$alarm_status"
echo "alarm_scope:$alarm_scope"
echo "alarm_active_at:$alarm_active_at"
echo "alarm_target:$alarm_target"
echo "alarm_description:$alarm_description"
echo "message:$message"
echo "receiver:$receiver"
echo "alarm_id:$alarm_id"

# this function defines to how to assembly request by yourself according to your requirements
# this demo shows you how to send alarm to ding ding
function send() {
    # this token is ding ding group token, please apply and assign it to variable token
    # 钉钉告警通道
    # https://oapi.dingtalk.com/robot/send?access_token=0d81c8e3d516efe88f3994bbdc2fbbf21c4cbbc2bf53e4701e2b2995d791de25
    URL='https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=46ce13d5-3f56-49ee-a88f-f2b043ba8fff'
    curl -X POST "${URL}" -H 'Content-Type: application/json' -d '{"msgtype": "markdown","markdown": {"content": "'"${message_json}"'"}}'
    return $?
}

# invoke function to
send
exit 0