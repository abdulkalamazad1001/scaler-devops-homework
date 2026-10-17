#!/usr/bin/env bash
# Read-only network observations inside an isolated Ubuntu container.
set -euo pipefail
set -x
ip -brief address
ip route
ip route get 1.1.1.1
ip neigh
ifconfig
hostname -I
ping -c 2 127.0.0.1
dig example.com
nslookup example.com
host example.com
cat /etc/resolv.conf
cat /etc/hosts
ss -tulpn
ss -s
netstat -tulpn
curl --retry 2 --connect-timeout 10 -I https://example.com
wget --timeout=15 -qO /tmp/example.html https://example.com
grep 'Example Domain' /tmp/example.html
# Routers may suppress TTL-expired replies; '*' is an observed timeout, not proof of failure.
traceroute -m 4 -q 1 -w 1 example.com
