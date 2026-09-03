# Networking Homework

Notes and command output from the devops-hero repo session 4 (networking) and the Linux
ip command cheat sheet from session 2.

## How I ran these

My laptop is a Mac, and the ip and ss commands do not exist there because they are
Linux tools. So I ran everything inside an Ubuntu container to get real Linux output:

    docker run --rm -it --cap-add=NET_ADMIN ubuntu:22.04 bash
    apt-get update
    apt-get install -y iproute2 iputils-ping dnsutils traceroute net-tools curl wget nginx

The container has one network interface, eth0, with the IP 172.17.0.3, and the Docker
bridge 172.17.0.1 acts as its gateway. That is why the addresses below are all in the
172.17.x.x range.

## Part 1: Looking at addresses and interfaces

### ip addr show

Shows every network interface and the IP addresses assigned to it. This is the first
command I run when I want to know the machine's IP.

    11: eth0@if20: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 65535 qdisc noqueue state UP
        link/ether 42:f1:29:44:47:0a brd ff:ff:ff:ff:ff:ff link-netnsid 0
        inet 172.17.0.3/16 brd 172.17.255.255 scope global eth0
           valid_lft forever preferred_lft forever

What I understood: link/ether is the MAC address, which is the hardware address burned
into the card. inet is the IPv4 address, and /16 is the subnet mask, meaning the first
16 bits are the network part and the remaining 16 bits are for hosts. UP means the
interface is enabled and LOWER_UP means the cable or virtual link is actually connected.

### ip -brief addr

The same information but one line per interface, much easier to read.

    lo               UNKNOWN        127.0.0.1/8 ::1/128
    tunl0@NONE       DOWN
    gre0@NONE        DOWN
    eth0@if20        UP             172.17.0.3/16

What I understood: lo is the loopback interface, 127.0.0.1, which the machine uses to
talk to itself. The tunnel interfaces are created by default but are DOWN, so they are
not in use. Only eth0 actually carries traffic here.

### ip link show

Shows the interfaces at the link layer, so MAC addresses and state, but no IP addresses.

    1: lo: <LOOPBACK,UP,LOWER_UP> mtu 65536 qdisc noqueue state UNKNOWN mode DEFAULT
        link/loopback 00:00:00:00:00:00 brd 00:00:00:00:00:00
    11: eth0@if20: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 65535 qdisc noqueue state UP
        link/ether 42:f1:29:44:47:0a brd ff:ff:ff:ff:ff:ff link-netnsid 0

What I understood: ip link is about layer 2 and ip addr is about layer 3. mtu is the
biggest packet the interface will send in one piece, normally 1500 on a real network.

### ifconfig

The older command that does roughly what ip addr does. It still works but it is
deprecated on modern Linux, and it is not installed by default any more.

    eth0: flags=4163<UP,BROADCAST,RUNNING,MULTICAST>  mtu 65535
            inet 172.17.0.3  netmask 255.255.0.0  broadcast 172.17.255.255
            ether 42:f1:29:44:47:0a  txqueuelen 0  (Ethernet)
            RX packets 2825  bytes 65610118 (65.6 MB)
            TX packets 1316  bytes 97521 (97.5 KB)

What I understood: it shows the same address as ip addr, just written differently.
255.255.0.0 is the same thing as /16. RX and TX are the packets received and sent, which
is useful for spotting an interface that is up but not passing any traffic.

### hostname and hostname -I

    e2fdb57a44fe
    172.17.0.3

What I understood: hostname alone prints the machine name, and hostname -I prints just
the IP addresses. The -I version is handy in scripts because there is nothing to parse.

## Part 2: Routing

### ip route

Shows the routing table, which is the list of rules the kernel uses to decide where to
send a packet.

    default via 172.17.0.1 dev eth0
    172.17.0.0/16 dev eth0 proto kernel scope link src 172.17.0.3

What I understood: the second line says anything in 172.17.0.0/16 is on the local
network and can be reached directly through eth0. The default line is the catch all, so
anything not matching a more specific route goes to the gateway 172.17.0.1. If the
default route is missing, the machine can talk to its own subnet but not to the internet.

### ip route get

Asks the kernel which route a specific destination would actually take.

    $ ip route get 8.8.8.8
    8.8.8.8 via 172.17.0.1 dev eth0 src 172.17.0.3 uid 0
        cache

What I understood: this is quicker than reading the whole table by hand, it tells you
the gateway, the outgoing interface and the source IP that will be used.

### ip route add and ip route delete

    $ ip route add 10.20.0.0/16 via 172.17.0.1 dev eth0
    $ ip route
    default via 172.17.0.1 dev eth0
    10.20.0.0/16 via 172.17.0.1 dev eth0
    172.17.0.0/16 dev eth0 proto kernel scope link src 172.17.0.3

    $ ip route delete 10.20.0.0/16
    $ ip route
    default via 172.17.0.1 dev eth0
    172.17.0.0/16 dev eth0 proto kernel scope link src 172.17.0.3

What I understood: you can add a route to a specific network through a chosen gateway,
and the more specific route wins over the default one. These changes are temporary and
disappear on reboot, permanent routes go in the network config files.

### ip neigh

Shows the ARP table, which maps IP addresses on the local network to MAC addresses.

    172.17.0.1 dev eth0 lladdr fa:60:b4:a0:1a:3f REACHABLE

What I understood: before sending a packet to a machine on the same network, the system
needs its MAC address, and ARP is how it finds it. REACHABLE means the entry was
confirmed recently. This is worth checking when two machines on the same subnet cannot
reach each other.

## Part 3: Changing addresses and links

### ip addr add and ip addr del

    $ ip addr add 10.10.10.5/24 dev eth0
    $ ip -brief addr show eth0
    eth0@if26        UP             172.17.0.3/16 10.10.10.5/24

    $ ip addr del 10.10.10.5/24 dev eth0
    $ ip -brief addr show eth0
    eth0@if26        UP             172.17.0.3/16

What I understood: one interface can hold more than one IP address at the same time.
The change is only in memory, so a reboot removes it. This needs root, and inside Docker
it also needs the NET_ADMIN capability.

### ip link set

    $ ip link set eth0 mtu 1400
    11: eth0@if26: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1400 qdisc noqueue state UP

What I understood: ip link set changes the interface itself rather than its address. The
other common forms are ip link set eth0 down to switch the interface off and ip link set
eth0 up to bring it back. Running down on a remote server over SSH would cut your own
connection, so it is not something to try casually.

## Part 4: Testing connectivity

### ping

Sends ICMP echo requests and waits for replies, the quickest way to check if a host is
reachable and how slow the link is.

    $ ping -c 4 google.com
    PING google.com (142.251.43.14) 56(84) bytes of data.
    64 bytes from tsa03s08-in-f14.1e100.net (142.251.43.14): icmp_seq=1 ttl=63 time=39.4 ms
    64 bytes from tsa03s08-in-f14.1e100.net (142.251.43.14): icmp_seq=2 ttl=63 time=28.5 ms
    64 bytes from tsa03s08-in-f14.1e100.net (142.251.43.14): icmp_seq=3 ttl=63 time=38.8 ms
    64 bytes from tsa03s08-in-f14.1e100.net (142.251.43.14): icmp_seq=4 ttl=63 time=35.4 ms

    --- google.com ping statistics ---
    4 packets transmitted, 4 received, 0% packet loss, time 3007ms
    rtt min/avg/max/mdev = 28.510/35.512/39.417/4.325 ms

What I understood: -c 4 stops after 4 packets, otherwise it runs forever. time is the
round trip in milliseconds and ttl is how many hops the reply had left. 0% packet loss
means the path is healthy. A ping that resolves the name but gets no reply usually means
a firewall is dropping ICMP rather than the host being down.

### traceroute

Shows each router along the path to a destination.

    $ traceroute -m 8 google.com
    traceroute to google.com (142.251.43.14), 8 hops max, 60 byte packets
     1  172.17.0.1 (172.17.0.1)  0.391 ms  0.012 ms  0.012 ms
     2  * * *
     3  * * *

What I understood: hop 1 is my gateway. The stars mean those routers did not reply,
which is normal because many of them are configured not to answer, and here the Docker
network hides the rest of the path too. Where it does work, traceroute tells you at
which hop the traffic starts slowing down or stops.

## Part 5: DNS

### nslookup

Resolves a name to an IP address.

    $ nslookup github.com
    Server:		192.168.65.7
    Address:	192.168.65.7#53

    Non-authoritative answer:
    Name:	github.com
    Address: 20.207.73.82

What I understood: Server is the DNS server that answered. Non-authoritative means the
answer came from a cache, not from the domain's own name server. Port 53 is the standard
DNS port.

### dig

The more detailed DNS tool.

    $ dig github.com +short
    20.207.73.82

    $ dig github.com
    ;; ->>HEADER<<- opcode: QUERY, status: NOERROR, id: 5659
    ;; flags: qr rd ra; QUERY: 1, ANSWER: 1, AUTHORITY: 0, ADDITIONAL: 0

    ;; QUESTION SECTION:
    ;github.com.			IN	A

    ;; ANSWER SECTION:
    github.com.		62	IN	A	20.207.73.82

    ;; Query time: 1 msec
    ;; SERVER: 192.168.65.7#53(192.168.65.7) (UDP)

What I understood: +short gives just the IP, which is what you want in a script. The
full output shows the record type, A for an IPv4 address, and the number 62 which is the
TTL, the seconds the answer can be cached before being looked up again. status NOERROR
means the lookup succeeded.

### host

A shorter version of the same thing.

    $ host github.com
    github.com has address 20.207.73.82
    github.com mail is handled by 0 github-com.mail.protection.outlook.com.

What I understood: it also prints the MX record, which is the mail server for that
domain.

### /etc/resolv.conf

The file that says which DNS servers the machine uses.

    # Generated by Docker Engine.
    nameserver 192.168.65.7

What I understood: if name lookups fail but pinging an IP directly works, this file is
the first place to check, because it means DNS is broken rather than the network.

### /etc/hosts

A local list of name to IP mappings, checked before DNS.

    127.0.0.1	localhost
    ::1	localhost ip6-localhost ip6-loopback
    172.17.0.3	acb08bf20146

What I understood: anything listed here wins over DNS, which is useful for testing a
domain against a specific server before changing the real DNS records.

## Part 6: Ports and connections

### ss -tulpn

Shows what is listening on the machine. I started nginx first so there would be
something to see.

    Netid State  Recv-Q Send-Q Local Address:Port Peer Address:Port Process
    tcp   LISTEN 0      511          0.0.0.0:80        0.0.0.0:*    users:(("nginx",pid=3059,fd=6))
    tcp   LISTEN 0      511             [::]:80           [::]:*    users:(("nginx",pid=3059,fd=7))

What I understood: the flags are t for TCP, u for UDP, l for listening only, p for the
process name and n for numeric ports instead of names. 0.0.0.0:80 means nginx accepts
connections on port 80 from any address, whereas 127.0.0.1:80 would mean local only.
This is the command to run when a port is already in use and you need to know what has
it.

### netstat -tulpn

The older equivalent of ss, same flags.

    Proto Recv-Q Send-Q Local Address           Foreign Address         State       PID/Program name
    tcp        0      0 0.0.0.0:80              0.0.0.0:*               LISTEN      3059/nginx: master
    tcp6       0      0 :::80                   :::*                    LISTEN      3059/nginx: master

What I understood: the same information as ss. ss is faster and is the recommended one
now, netstat comes from the net-tools package which is deprecated.

### ss -s

A summary of all sockets.

    Total: 35
    TCP:   36 (estab 0, closed 34, orphaned 0, timewait 2)

    Transport Total     IP        IPv6
    TCP	  2         1         1

What I understood: estab is the number of live connections and timewait is connections
that have closed but are still being held briefly. A huge timewait count on a busy
server is a known symptom worth knowing about.

## Part 7: Talking to a web server

### curl -I

Sends an HTTP request and prints only the response headers.

    $ curl -I http://localhost
    HTTP/1.1 200 OK
    Server: nginx/1.18.0 (Ubuntu)
    Date: Tue, 01 Sep 2026 06:59:49 GMT
    Content-Type: text/html
    Content-Length: 612
    Connection: keep-alive

What I understood: 200 OK means the server answered normally. This is the fastest way to
check whether a service is actually up, and it tells you which server software is
answering. Without -I you get the whole page body instead.

### curl to find the public IP

    $ curl -s ifconfig.me
    202.131.xxx.xxx

What I understood: this shows the address the outside world sees, which is my router's
public IP, not the private 172.17.0.3 the container has. That is NAT in action, many
private addresses sharing one public one. I have masked the last part here since this
file goes into a public repo.

### wget

Downloads a file instead of printing it.

    $ wget -q -O page.html http://example.com
    $ ls -l page.html
    -rw-r--r-- 1 root root 559 Aug 31 04:09 page.html
    $ head -4 page.html
    <!doctype html><html lang="en"><head><title>Example Domain</title>...

What I understood: the difference from curl is that wget saves to a file by default and
curl prints to the screen by default. -q is quiet mode and -O sets the output filename.

## Summary of what each command is for

ip addr shows the IP addresses, ip link shows the interfaces and MAC addresses, ip route
shows where packets go, and ip neigh shows the ARP table. ifconfig and netstat are the
older versions of ip and ss, still around but deprecated.

ping checks if a host answers, traceroute shows the path to it.

nslookup, dig and host all resolve names to IPs, with dig giving the most detail.

ss and netstat show which ports are open and which process owns them.

curl and wget talk to web servers, curl for checking and wget for downloading.

The order I would use when something is not reachable: check the interface has an IP
with ip addr, check there is a default route with ip route, ping the gateway, ping an IP
like 8.8.8.8 to test raw connectivity, then ping a domain name to test DNS separately,
and finally use ss to confirm the service on the other end is actually listening.
