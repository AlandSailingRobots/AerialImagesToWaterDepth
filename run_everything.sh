#!/usr/bin/env bash
function start_everything() {
  sudo httpd -k start
  mysql.server start
  pg_ctl -D /usr/local/var/postgres start
}
function stop_everything() {
  sudo httpd -k stop
  mysql.server stop
  pg_ctl -D /usr/local/var/postgres stop
}
pause() {
  sleep 1
  read -n 1 -p "Press any key to continue...";
}

start_everything
pause
stop_everything
