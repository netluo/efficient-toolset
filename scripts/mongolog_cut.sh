#!/bin/bash
# cut mongo log

pids=$(/sbin/pidof mongod)
if [[ -z "$pid"  ]]; then
 for pid in $pids; do
  /bin/kill -SIGUSR1 "$pid"
  echo "$pid" >> /tmp/mongolog_cut.log
 done
 exit 0;

else
 echo "pids null: [$pids]" >> /tmp/mongolog_cut.log
 exit 1;
fi
