#!/bin/sh
set -eu
mkdir -p /tor-control /var/lib/tor
chmod 700 /tor-control
chown tor:tor /tor-control /var/lib/tor
/usr/local/bin/firewall.sh
exec su-exec tor tor -f /etc/tor/torrc "$@"
