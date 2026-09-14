#!/bin/sh
set -eu

# Only containers on the local bridge and the host gateway may use this proxy.
iptables -A INPUT -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT
iptables -A INPUT -i lo -j ACCEPT
for network in $(ip -4 route show dev eth0 | awk 'index($1, "/") {print $1}'); do
    iptables -A INPUT -s "$network" -p tcp -m multiport --dports 9051,9080 -j ACCEPT
done
iptables -P INPUT DROP

# Allow replies to the app, but block new connections to host services and
# AWS metadata, including both instance and ECS task credential endpoints.
iptables -A OUTPUT -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT
iptables -A OUTPUT -o lo -j ACCEPT
for resolver in $(awk '/^nameserver / {print $2}' /etc/resolv.conf); do
    case "$resolver" in *:*) continue ;; esac
    iptables -A OUTPUT -d "$resolver" -p udp --dport 53 -j ACCEPT
    iptables -A OUTPUT -d "$resolver" -p tcp --dport 53 -j ACCEPT
done
for network in 0.0.0.0/8 10.0.0.0/8 100.64.0.0/10 127.0.0.0/8 169.254.0.0/16 172.16.0.0/12 192.168.0.0/16 224.0.0.0/4 240.0.0.0/4; do
    iptables -A OUTPUT -d "$network" -j REJECT
done

# Use IPv4 relays and close the alternate path to IPv6 instance metadata.
ip6tables -P OUTPUT DROP
ip6tables -P INPUT DROP
ip6tables -A INPUT -i lo -j ACCEPT
ip6tables -A INPUT -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT
ip6tables -A OUTPUT -o lo -j ACCEPT
ip6tables -A OUTPUT -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT
