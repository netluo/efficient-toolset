#!/bin/bash
# description: yearning Start Stop Restart
# processname: yearning
# chkconfig: 2345 55 25

CATALINA_HOME=/usr/local/yearning
YEARNING_PORT=8000
BINARY_NAME=Yearning

PID=$(ps -ef | grep Yearning | grep $YEARNING_PORT | head -1 | awk '{ print $2 }')

function start() {
  cd $CATALINA_HOME && nohup ./Yearning run --port $YEARNING_PORT >>yearning$YEARNING_PORT.log 2>&1 &
}

function status() {
  # shellcheck disable=SC2046
  if [ $(netstat -ntlp | grep $YEARNING_PORT | wc -l) -eq 1 ]; then
    echo "$BINARY_NAME (pid $PID) running ... "
  else
    echo "$BINARY_NAME not running ..."
  fi
}
function stop() {
  echo -n $"Shutting down $BINARY_NAME: "
  kill -9 $PID
}
case "$1" in
start)
  start
  ;;
stop)
  stop
  ;;
status)
  status
  ;;
restart)
  stop
  sleep 5
  start
  ;;
help | *)
  echo $"Usage: $0 {start|stop|status|restart|help}"
  cat <<EOF

                start           - start $BINARY_NAME
                stop            - stop $BINARY_NAME
                status          - show current status of $BINARY_NAME
                restart         - restart $BINARY_NAME if running by sending a SIGHUP or start if not running
                help            - this screen

EOF
  exit 1
  ;;
esac
