# Docker Networking and Volume Homework

All commands below were actually run and the output is copied as it appeared.

## Task 1: Container networking with three containers and three networks

The plan: a frontend, a backend and a MySQL database. The backend sits on two networks so
it can talk to both sides, and the frontend should not be able to reach the database at
all.

    frontend-net    frontend + backend
    backend-net     backend + database
    database-net    database

### Create the three networks

    $ docker network create frontend-net
    $ docker network create backend-net
    $ docker network create database-net

    $ docker network ls
    NETWORK ID     NAME           DRIVER    SCOPE
    347ca727ce50   backend-net    bridge    local
    270511660d8a   database-net   bridge    local
    668b73a0717c   frontend-net   bridge    local
    aa75b76ba87c   bridge         bridge    local
    51ef457e4253   host           host      local
    7d4efe805165   none           null      local

The last three are the networks Docker always provides. The ones I created use the bridge
driver, which is the default for a single host.

### Create the containers

    $ docker run -d --name frontend --network frontend-net alpine sleep infinity
    $ docker run -d --name backend  --network frontend-net alpine sleep infinity
    $ docker network connect backend-net backend
    $ docker run -d --name database --network backend-net -e MYSQL_ROOT_PASSWORD=rootpass mysql:8.0
    $ docker network connect database-net database

A container can only be given one network on docker run. To put it on a second network
you use docker network connect afterwards, which is how the backend ends up on two.

    $ docker ps
    NAMES      IMAGE       STATUS
    database   mysql:8.0   Up 5 seconds
    backend    alpine      Up 34 seconds
    frontend   alpine      Up 34 seconds

### Which container is on which network

    frontend  frontend-net=172.19.0.2
    backend   backend-net=172.20.0.2   frontend-net=172.19.0.3
    database  backend-net=172.20.0.3   database-net=172.21.0.2

The backend has two IP addresses, one on each network. Each network is its own subnet,
172.19, 172.20 and 172.21.

### Connectivity test 1: frontend to backend, same network

    $ docker exec frontend ping -c 2 backend
    PING backend (172.19.0.3): 56 data bytes
    64 bytes from 172.19.0.3: seq=0 ttl=64 time=0.470 ms
    64 bytes from 172.19.0.3: seq=1 ttl=64 time=0.084 ms

    --- backend ping statistics ---
    2 packets transmitted, 2 packets received, 0% packet loss

Works. Notice I pinged the name backend, not an IP. Docker runs a small DNS server on
every user created network, so containers can find each other by container name.

### Connectivity test 2: backend to database, same network

    $ docker exec backend ping -c 2 database
    PING database (172.20.0.3): 56 data bytes
    64 bytes from 172.20.0.3: seq=0 ttl=64 time=0.494 ms
    64 bytes from 172.20.0.3: seq=1 ttl=64 time=0.191 ms

    --- database ping statistics ---
    2 packets transmitted, 2 packets received, 0% packet loss

    $ docker exec backend nc -z -w 3 database 3306
    port 3306 is open from backend

The MySQL port is reachable from the backend, which is what a real application would
need.

### Connectivity test 3: frontend to database, no shared network

    $ docker exec frontend ping -c 2 database
    ping: bad address 'database'

    $ docker exec frontend nc -z -w 3 database 3306
    nc: bad address 'database'

This is the important result. The frontend cannot even resolve the name database, let
alone connect to it. The two containers share no network, so Docker's DNS on frontend-net
has no record of it.

### Members of each network

    frontend-net  frontend (172.19.0.2/16)  backend (172.19.0.3/16)
    backend-net   database (172.20.0.3/16)  backend (172.20.0.2/16)
    database-net  database (172.21.0.2/16)

### What I understood

The default bridge network lets every container talk to every other one, which is fine
for playing around but wrong for a real application. Creating separate networks and
putting each container only on the networks it needs is how you keep the database
private. The frontend can be exposed to the internet and still have no route to the
database, because the only thing that can reach both is the backend.

## Task 2: Host network

Note before the output: I am on Docker Desktop for Mac, and my laptop already had a work
container publishing port 80. I stopped that container for about a minute to free the
port, ran this exercise, and started it again afterwards.

### Pull the Apache image

    $ docker pull httpd:2.4
    Status: Downloaded newer image for httpd:2.4
    docker.io/library/httpd:2.4

### Run it on the host network

    $ docker run -d --name apache-host --network host httpd:2.4
    40dc84dc58175bf4d82fb468070eae1d597ceb6852cbc9e5a06faf5d7b4fb732

    $ docker ps
    NAMES         IMAGE       STATUS         PORTS
    apache-host   httpd:2.4   Up 3 seconds

    $ docker logs apache-host
    [mpm_event:notice] AH00489: Apache/2.4.68 (Unix) configured -- resuming normal operations
    [core:notice] AH00094: Command line: 'httpd -D FOREGROUND'

The first thing to notice is that the PORTS column is empty. With host networking there
is no port mapping, because there is no separate network namespace to map from. The
container is using the host's network directly, so Apache is simply listening on the
host's port 80.

I did not use -p at all here. Using -p with --network host does nothing and Docker warns
about it.

### Access it on port 80

    $ curl -i http://localhost:80
    HTTP/1.1 200 OK
    Server: Apache/2.4.68 (Unix)
    Content-Length: 191
    Content-Type: text/html

    $ curl http://localhost:80
    <html>
    <head><title>It works! Apache httpd</title></head>
    <body><p>It works!</p></body>
    </html>

### Proof that it really is the host's network

    $ docker run --rm curlimages/curl -s -o /dev/null -w '%{http_code}' http://localhost:80
    000

A normal bridge container asked for localhost:80 gets nothing, because its localhost is
its own loopback inside its own namespace. The host network container gets the Apache
page from the same address. That is the whole difference.

### The Mac caveat, and why I ran it twice

On Linux, --network host means the actual machine, so the page opens at http://localhost
in your browser straight away. On Docker Desktop for Mac, containers run inside a small
Linux virtual machine, so the host in host networking is that VM, not macOS. curl from
the Mac terminal gave 000 while curl from inside the VM gave 200.

So to also get a browser screenshot on port 80, I ran the same image the normal bridge
way with the port published:

    $ docker run -d --name apache-port80 -p 80:80 httpd:2.4
    $ curl -s -o /dev/null -w "%{http_code}\n" http://localhost:80
    200

![Apache on port 80](screenshots/apache-port80.png)

### What I understood

Host networking removes the isolation layer. It is faster because there is no NAT and no
port mapping, and it is useful for things that need to see the real network, like a
monitoring agent or something that uses a large range of ports. The cost is that the
container can grab any host port, there is no isolation, and two containers cannot both
use port 80. It also behaves differently on Mac and Windows, which is worth remembering.

## Task 3: Bind mount

### Create the folder and the file

    mkdir -p bind-mount-demo/website

bind-mount-demo/website/index.html:

    <!DOCTYPE html>
    <html>
      <head><title>Bind Mount Demo</title></head>
      <body style="font-family: sans-serif; text-align: center; margin-top: 15vh;">
        <h1>Hello students</h1>
      </body>
    </html>

### Mount it into an Nginx container

    $ docker run -d --name bindmount-nginx -p 8084:80 \
        -v "$(pwd)/bind-mount-demo/website":/usr/share/nginx/html:ro \
        nginx:1.27-alpine

The source path has to be absolute, which is why I used $(pwd). The :ro at the end makes
the mount read only inside the container, so the web server can serve the files but
cannot change them. That is a good default for a website.

    $ docker inspect bindmount-nginx --format '{{range .Mounts}}...{{end}}'
    type=bind
    source=/Users/.../task-7-docker-networking-volume/bind-mount-demo/website
    destination=/usr/share/nginx/html
    readonly=true

### Verify the content

    $ curl http://localhost:8084
    <h1>Hello students</h1>

![Hello students](screenshots/bind-mount-before.png)

### Modify the file and check again, without restarting

I edited index.html on my Mac, changing the heading, and did not touch the container.

    $ curl http://localhost:8084
    <h1>Hello students, this file was edited on the host</h1>
    <p>The container was never restarted.</p>

    $ docker ps
    NAMES             STATUS
    bindmount-nginx   Up 18 seconds

![Edited on the host](screenshots/bind-mount-after.png)

The status still says Up, with no restart, and the new content is being served.

### What I understood

A bind mount points a path inside the container at a real folder on the host. There is no
copy involved, both sides are looking at the same files, so an edit on the host is visible
in the container immediately. That is why the change appeared without a restart.

The difference from a named volume: a volume is managed by Docker and lives under
/var/lib/docker/volumes, and you refer to it by name. A bind mount is any path you choose
on the host. Bind mounts are ideal in development, where you want to edit code and see it
live. Volumes are the better choice in production, for things like database data, because
they do not depend on the host's folder layout and Docker can back them up and move them.

## Task 4: Overlay networks

### What they are

Bridge networks only work on one machine. An overlay network lets containers on several
different Docker hosts talk to each other as if they were on the same local network. It
does this by wrapping the container traffic in VXLAN packets and sending it over the real
network between the hosts, which is why it is called an overlay: a virtual network laid on
top of the physical one.

Overlay networks need a cluster, so you have to be in Docker Swarm mode. Trying without
one fails:

    $ docker network create -d overlay test-overlay
    Error response from daemon: This node is not a swarm manager. Use "docker swarm init"
    or "docker swarm join" to connect this node to swarm and try again.

### I tried it on a single node swarm

    $ docker swarm init
    Swarm initialized: current node (wt6xfln0wmz98e0flcoo9mrxg) is now a manager.

    To add a worker to this swarm, run the following command:
        docker swarm join --token SWMTKN-1-<token removed> 192.168.65.3:2377

    $ docker network create -d overlay --attachable my-overlay
    sdgbg5q1cuexi3tuyadmh61bv

    $ docker network ls
    NETWORK ID     NAME         DRIVER    SCOPE
    dtlqklpj7cc5   ingress      overlay   swarm
    sdgbg5q1cuex   my-overlay   overlay   swarm

Two things changed compared to the bridge networks in Task 1. The driver is overlay, and
the scope is swarm instead of local, meaning the network definition is shared across every
node in the cluster rather than existing only on this machine.

An ingress network also appeared on its own. That is the one Swarm uses for its load
balancer, so a request to a published port on any node reaches a container wherever it
happens to be running.

The --attachable flag lets plain docker run containers join the network. Without it only
swarm services can.

    $ docker run -d --name ov1 --network my-overlay alpine sleep infinity
    $ docker run -d --name ov2 --network my-overlay alpine sleep infinity

    $ docker exec ov1 ping -c 2 ov2
    PING ov2 (10.0.1.4): 56 data bytes
    64 bytes from 10.0.1.4: seq=0 ttl=64 time=0.596 ms
    64 bytes from 10.0.1.4: seq=1 ttl=64 time=0.188 ms
    2 packets transmitted, 2 packets received, 0% packet loss

    $ docker network inspect my-overlay
    driver=overlay scope=swarm attachable=true subnet=10.0.1.0/24

I only have one machine, so both containers happened to land on the same host. The point
is that the commands and the name based connection would be identical if ov2 were running
on a different server, and that is the whole value of it.

Afterwards I put my machine back how it was:

    $ docker swarm leave --force
    Node left the swarm.

### How it works across multiple hosts

Each host runs a VXLAN tunnel endpoint. When a container sends a packet to a container on
another host, the local Docker daemon wraps that packet inside a UDP packet, sends it to
the other host over the normal network, and the daemon there unwraps it and hands it to
the target container. Neither container knows any of this happened, they just see a flat
network.

The swarm managers keep a shared store of which container is on which host and what its
overlay IP is, so DNS by container or service name works across the whole cluster. Ports
4789 for VXLAN traffic, 7946 for node discovery and 2377 for cluster management have to be
open between the hosts.

### When you would use one

When an application is spread across more than one machine and the parts need to talk
privately, for example an API on one server and a database on another, without exposing
ports on the public network. Also when you want a service to be able to move between
nodes and still be reachable by the same name.

For a single machine, a bridge network is simpler and faster and does the job, so overlay
is not worth the complexity. In practice, most teams that need this now use Kubernetes,
where the same problem is solved by a CNI plugin, but the underlying idea of a virtual
network across hosts is the same.

## Summary of the network drivers

bridge is the default and works on one host, with containers on the same bridge finding
each other by name.

host removes the isolation and uses the machine's own network, so there is no port
mapping.

overlay spans multiple hosts in a swarm using VXLAN tunnels.

none gives a container no networking at all, which is occasionally useful for a job that
should not touch the network.

## Cleanup

    docker rm -f frontend backend database bindmount-nginx
    docker network rm frontend-net backend-net database-net
