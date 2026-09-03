# Scaler DevOps Homework

**Name:** T. Abdul Kalam Azad  
**Roll number:** 24BCS10053  
**Checkpoints:** 40 of 40 complete

Seven homework tasks covering Linux basics, shell scripting, networking, Git and Docker.
Each task lives in its own folder with a write-up that carries the real command output,
and the Docker tasks also carry browser screenshots as evidence.

---

## Checkpoints

Every box below was completed and has written evidence in the linked file.

### Task 1 — Linux basics → [`task-1-linux-basics/README.md`](task-1-linux-basics/README.md)

- [x] Soft link vs hard link, demonstrated with `ln`, `ln -s` and `ls -li` inode output
- [x] Proved the difference by deleting the target: the hard link survives, the soft link breaks
- [x] `adduser` vs `useradd`, with the equivalent flags spelled out for each
- [x] `journalctl` for reading systemd logs, including the follow, filter and vacuum flags
- [x] A command cheat sheet covering navigation, files, permissions, processes and archives

### Task 2 — Shell scripting → [`task-2-shell-scripting/`](task-2-shell-scripting/)

- [x] `sysinfo.sh` stores the date, hostname and username in variables and prints them
- [x] Prints disk usage with `df -h` and the first ten processes with `ps`
- [x] Asks for a directory name and a file name with `read -p`
- [x] Creates them with `mkdir -p` and `touch`
- [x] Saves the full `ps aux` output to the file with `>` redirection
- [x] Script re-run on 3 September 2026 and the write-up updated with that real output

### Task 3 — Networking → [`task-3-networking/README.md`](task-3-networking/README.md)

- [x] Addresses and interfaces: `ip addr`, `ip -brief addr`, `ip link`, `ifconfig`, `hostname -I`
- [x] Routing: `ip route`, `ip route get`, `ip route add` / `delete`, `ip neigh`
- [x] Changing addresses and links: `ip addr add` / `del`, `ip link set`
- [x] Connectivity: `ping`, `traceroute`
- [x] DNS: `nslookup`, `dig`, `host`, `/etc/resolv.conf`, `/etc/hosts`
- [x] Ports and sockets: `ss -tulpn`, `netstat -tulpn`, `ss -s`
- [x] Web requests: `curl -I`, public IP lookup, `wget`
- [x] Ran inside an Ubuntu container, because `ip` and `ss` do not exist on macOS

### Task 4 — Git → [`task-4-git/README.md`](task-4-git/README.md)

- [x] `git commit -m` vs `git commit -a -m`, tested on a tracked file
- [x] Showed that `-a` does **not** pick up untracked files
- [x] `git cherry-pick`: moved one bugfix commit to `main` and left the feature commits behind
- [x] Explained from the `--graph` output that cherry-pick creates a new hash, it does not move a commit

### Task 5 — Docker, six Hello World apps → [`task-5-docker/README.md`](task-5-docker/README.md)

- [x] Node.js and Express — `node:20-alpine`, port 3000 → host 3001
- [x] Python and Flask — `python:3.12-slim`, port 5000 → host 5001
- [x] Java with the JDK's built-in HTTP server — two stage JDK → JRE build, port 8080
- [x] Apache serving a static page — `httpd:2.4-alpine`, port 80 → host 8081
- [x] Nginx serving a static page — `nginx:1.27-alpine`, port 80 → host 8082
- [x] React built with Vite, served by Nginx — two stage build, 76 MB final image, host 8083
- [x] All six built, run and opened in a browser, with a screenshot for each in `screenshots/`
- [x] Hardening pass afterwards: `USER node`, non-root `appuser`, `NODE_ENV`, `PYTHONUNBUFFERED`

### Task 6 — Docker multi-stage build → [`task-6-docker-multistage/README.md`](task-6-docker-multistage/README.md)

- [x] Built the given multi-stage Dockerfile and ran it on host port 8080
- [x] Verified with `docker ps`, `docker logs` and `curl`, plus a browser screenshot
- [x] Compared against a single stage build of the same app and explained the small 6 MB gap honestly
- [x] Deployed three different application types — Node.js, Python and Java — side by side

### Task 7 — Docker networking and volumes → [`task-7-docker-networking-volume/README.md`](task-7-docker-networking-volume/README.md)

- [x] Three containers across three custom bridge networks, with the backend on two of them
- [x] Proved the isolation: frontend reaches backend, backend reaches MySQL, frontend cannot resolve the database at all
- [x] Host networking with Apache on port 80, including why it behaves differently on macOS
- [x] Bind mount into Nginx, edited the file on the host and saw it served without a restart
- [x] Overlay networks on a single node swarm, and how VXLAN carries traffic between hosts

---

## Repository layout

    scaler-devops-homework/
    ├── README.md                          this file
    ├── task-1-linux-basics/
    │   └── README.md
    ├── task-2-shell-scripting/
    │   ├── README.md
    │   └── sysinfo.sh                     the script itself
    ├── task-3-networking/
    │   └── README.md
    ├── task-4-git/
    │   └── README.md
    ├── task-5-docker/
    │   ├── README.md
    │   ├── nodejs-app/    python-app/    java-app/
    │   ├── Apache-app/    nginx-app/     React-app/
    │   └── screenshots/                   one per app
    ├── task-6-docker-multistage/
    │   ├── README.md
    │   ├── multi-stage-app/
    │   └── screenshots/
    └── task-7-docker-networking-volume/
        ├── README.md
        ├── bind-mount-demo/website/
        └── screenshots/

## Reproducing the work

### Task 2, the shell script

    cd task-2-shell-scripting
    chmod +x sysinfo.sh
    ./sysinfo.sh

Press Enter at both prompts to accept the defaults, `sysreport` and `processes.txt`.
The generated folder is in `.gitignore`, so it never gets committed.

### Task 5, the six Docker apps

    cd task-5-docker

    docker build -t nodejs-hello nodejs-app
    docker build -t python-hello python-app
    docker build -t java-hello   java-app
    docker build -t apache-hello Apache-app
    docker build -t nginx-hello  nginx-app
    docker build -t react-hello  React-app

    docker run -d --name node-hello -p 3001:3000 nodejs-hello
    docker run -d --name py-hello   -p 5001:5000 python-hello
    docker run -d --name jv-hello   -p 8080:8080 java-hello
    docker run -d --name ap-hello   -p 8081:80   apache-hello
    docker run -d --name ng-hello   -p 8082:80   nginx-hello
    docker run -d --name rc-hello   -p 8083:80   react-hello

Then check all six at once:

    for p in 3001 5001 8080 8081 8082 8083; do
      printf '%s -> %s\n' "$p" "$(curl -s -o /dev/null -w '%{http_code}' http://localhost:$p)"
    done

The React app returns an almost empty body to `curl`, because it renders in the browser,
so open <http://localhost:8083> to see it.

Cleanup:

    docker rm -f node-hello py-hello jv-hello ap-hello ng-hello rc-hello
    docker rmi nodejs-hello python-hello java-hello apache-hello nginx-hello react-hello

### Task 6, the multi-stage build

    cd task-6-docker-multistage
    docker build -t multistage-hello multi-stage-app
    docker run -d --name multistage-app -p 8080:3000 multistage-hello
    curl http://localhost:8080

### Task 7, networking and volumes

The write-up lists the commands for each of the four parts in order. Note that Task 2
of it publishes port 80, so nothing else can be holding that port, and Task 4 needs
`docker swarm init` for overlay networks.

## Environment these were run on

    Machine   MacBook Pro, macOS (Darwin 25.6.0)
    Docker    Docker Desktop for Mac
    Linux     Ubuntu 22.04 in a container, for Task 3, since macOS has no ip or ss

Because it is Docker Desktop, containers run inside a small Linux VM. That matters in
two places and both are called out where they come up: host networking in Task 7 reaches
the VM rather than macOS, and the ports the container sees are always the right hand side
of the `-p host:container` mapping.

## A note on ports

Ports 3000 and 5000 were already in use, so the Node and Python apps are published on
3001 and 5001 instead. Only the host side of the mapping changed. Inside their
containers the apps still listen on their normal ports, which is why the Dockerfiles
still say `EXPOSE 3000` and `EXPOSE 5000`.
