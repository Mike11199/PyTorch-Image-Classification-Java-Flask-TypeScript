#!/bin/sh
set -eu
cookie=$(od -An -tx1 -v /tor-control/control_auth_cookie | tr -d ' \n')
printf 'AUTHENTICATE %s\r\nGETINFO status/bootstrap-phase\r\nQUIT\r\n' "$cookie" |
    nc -w 2 127.0.0.1 9051 | grep -q 'PROGRESS=100'
