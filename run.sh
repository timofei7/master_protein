#!/bin/bash

usage="$0. Usage:\n
parameter 1: serv, app, all -- will launch either just the server, just the app, or everything\n
parameter 2: port number to bind the app to (optional). If negative, will only kill previous instances."
if [[ $# < 1 || $# > 2 ]]; then
  echo -e $usage
  exit 4
fi

w=6 # number of workers to launch
type=$1
if [[ $# > 1 ]]; then
  port=$(($2+0))
else
  port=5001
fi
if [[ $type != "all" && $type != "app" && $type != "serv" ]]; then
  echo $usage
  exit 4
fi

x=`whoami`
if [[ $type = "all" || $type = "serv" ]]; then
  # create output directory
  if [[ -d processing ]]; then
    mkdir -p processing
  fi

  # kill old workers and server instance
  for i in {1..10000}; do
    pidf="/tmp/rqworker.$x.$i.pid"
    if [ ! -f $pidf ]; then
      break
    fi
    kill -9 `cat $pidf`
    rm $pidf
  done
  pidf="/tmp/redis.$x.pid"
  if [ -f $pidf ]; then
    kill -9 `cat $pidf`
    rm $pidf
  fi

  # launch server and worker instances
  if [[ $port -gt 0 ]]; then
    redis-server --daemonize yes --pidfile /tmp/redis.$x.pid --logfile /tmp/redis.$x.log
#    redis-server --pidfile /tmp/redis.$x.pid --logfile /tmp/redis.$x.log &
    for (( i=1; i<=$w; i++ )); do
      rqworker --pid /tmp/rqworker.$x.$i.pid &
    done
  fi
fi

if [[ $type = "all" || $type = "app" ]]; then
  # kill previous app
  pidf="/tmp/gunicorn.$x.pid"
  if [ -f $pidf ]; then
    pkill -F $pidf
    rm $pidf
  fi

  # launch app
  if [[ $port -gt 0 ]]; then
    gunicorn --pid $pidf --access-logfile /tmp/gunicorn.$x.log --daemon -w $w --graceful-timeout 1200 --timeout 1200 -b 0.0.0.0:$port MasterApp:app
  fi
fi

