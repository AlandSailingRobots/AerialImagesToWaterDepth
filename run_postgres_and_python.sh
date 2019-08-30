#!/usr/bin/env bash

function start_everything() {
  echo 'starting postgres'
  pg_ctl -D /usr/local/var/postgres start
}
function stop_everything() {
  pg_ctl -D /usr/local/var/postgres stop
}
pause() {
  sleep 1
  read -n 1 -p "Press any key to continue..."
}

start_everything

if [ "$1" == "" ]; then
  echo 'no arguments'
else
  echo 'argument ' "$1"
  source venv/bin/activate
  python $1
fi
  pause
  stop_everything
