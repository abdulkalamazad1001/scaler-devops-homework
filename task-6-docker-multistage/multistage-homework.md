# Docker Multi-Stage Build Homework

Name: Mohammed Abdurrahman

Enrollment number: <ENROLLMENT_NUMBER>

## Task 1: Run the multi-stage Dockerfile

### The source

The Dockerfile came from the devops-hero repository:

    git clone https://github.com/Nency-Ravaliya/devops-heros.git
    cd devops-heros/session6-7-docker/multi-stage-dockerfile

I copied that folder into this repo as multi-stage-app so the submission is self
contained. It has three files: Dockerfile, package.json and server.js.

The app is a small Express server:

    const express = require("express");

    const app = express();
    const PORT = 3000;

    app.get("/", (req, res) => {
      res.send("<h1>Hello World from Docker Multi-Stage Build!</h1>");
    });

    app.listen(PORT, () => {
      console.log(`Server running on port ${PORT}`);
    });

The Dockerfile:

    # -------------------------
    # Stage 1: Build
    # -------------------------
    FROM node:24-alpine AS builder
    WORKDIR /app
    COPY package*.json ./
    RUN npm install
    COPY . .

    # -------------------------
    # Stage 2: Production
    # -------------------------
    FROM node:24-alpine AS production
    WORKDIR /app
    COPY --from=builder /app/package*.json ./
    RUN npm install --omit=dev
    COPY --from=builder /app/server.js ./
    EXPOSE 3000
    CMD ["npm", "start"]

The builder stage installs everything including dev dependencies. The production stage
starts from a fresh image and copies only what is needed to run, then installs the
production dependencies with --omit=dev. Anything left behind in the builder stage,
such as dev tooling, caches and source files that are not needed, never reaches the
final image.

### Build the image

    $ docker build -t multistage-hello multi-stage-app

    #12 [production 5/5] COPY --from=builder /app/server.js ./
    #12 DONE 0.0s
    #13 exporting to image
    #13 naming to docker.io/library/multistage-hello:latest done
    #13 DONE 0.3s

### Run the container on port 8080

The app listens on port 3000 inside the container, so I mapped host port 8080 to
container port 3000.

    $ docker run -d --name multistage-app -p 8080:3000 multistage-hello
    33943338c338c5ddd42ca2ff4efe946a574686edc887ac1b1aaf3066a99e0d2e

    $ docker logs multistage-app
    > docker-hello-world@1.0.0 start
    > node server.js

    Server running on port 3000

### Verify the running container with docker ps

    $ docker ps
    CONTAINER ID   IMAGE              COMMAND                  CREATED         STATUS         PORTS                       NAMES
    33943338c338   multistage-hello   "docker-entrypoint.s…"   3 seconds ago   Up 3 seconds   0.0.0.0:8080->3000/tcp      multistage-app

The PORTS column shows 0.0.0.0:8080->3000/tcp, which confirms the application is
reachable on port 8080 on the host.

### Access the application

    $ curl -i http://localhost:8080
    HTTP/1.1 200 OK
    X-Powered-By: Express
    Content-Type: text/html; charset=utf-8
    Content-Length: 51
    Connection: keep-alive

    $ curl http://localhost:8080
    <h1>Hello World from Docker Multi-Stage Build!</h1>

The page displays Hello World from Docker Multi-Stage Build, which is what the task
asked for.

## Task 2: Evidence

Name: Mohammed Abdurrahman

Enrollment number: <ENROLLMENT_NUMBER>

### The application running in a browser

Screenshot: screenshots/multistage-app-8080.png

It shows http://localhost:8080 displaying the heading Hello World from Docker
Multi-Stage Build.

### docker ps showing the container on port 8080

    $ docker ps
    CONTAINER ID   IMAGE              COMMAND                  CREATED         STATUS         PORTS                                         NAMES
    33943338c338   multistage-hello   "docker-entrypoint.s…"   3 seconds ago   Up 3 seconds   0.0.0.0:8080->3000/tcp, [::]:8080->3000/tcp   multistage-app

### Does the multi-stage build actually save anything here?

I built the same app with an ordinary single stage Dockerfile to compare:

    $ docker images
    singlestage-hello   249MB
    multistage-hello    243MB

Only 6 MB saved. That is honest but worth explaining: this app has no dev dependencies
and nothing to compile, so there is very little for the builder stage to throw away. The
saving becomes large when the build step produces something different from its input,
for example a React app that compiles down to static files, or a Java app where the JDK
is needed to compile but only the JRE is needed to run. In my earlier Docker homework the
React app came out at 76 MB with a multi-stage build instead of over 200 MB, because only
the finished static files were kept.

## Task 3: Deploying three different types of application

I deployed three applications of different types, all from the previous Docker homework
folder in this repository, at ../task-5-docker.

    docker build -t nodejs-hello ../task-5-docker/nodejs-app
    docker build -t python-hello ../task-5-docker/python-app
    docker build -t java-hello   ../task-5-docker/java-app

    docker run -d --name node-hello -p 3001:3000 nodejs-hello
    docker run -d --name py-hello   -p 5001:5000 python-hello
    docker run -d --name jv-hello   -p 8085:8080 java-hello

1. Node.js with Express, base image node:20-alpine
2. Python with Flask, base image python:3.12-slim
3. Java using the HTTP server built into the JDK, built with a two stage JDK to JRE
   Dockerfile, base image eclipse-temurin:21

### docker ps showing all three running

    CONTAINER ID   IMAGE          COMMAND                  CREATED         STATUS         PORTS                      NAMES
    7e73b09bdb24   java-hello     "/__cacert_entrypoin…"   4 seconds ago   Up 3 seconds   0.0.0.0:8085->8080/tcp     jv-hello
    7230a4fdfe36   python-hello   "python app.py"          3 minutes ago   Up 3 minutes   0.0.0.0:5001->5000/tcp     py-hello
    7b3c5f4137d8   nodejs-hello   "docker-entrypoint.s…"   3 minutes ago   Up 3 minutes   0.0.0.0:3001->3000/tcp     node-hello

### Verifying each one

    Node.js  http://localhost:3001  -> HTTP 200  <h1>Hello World</h1>
    Python   http://localhost:5001  -> HTTP 200  <h1>Hello World</h1>
    Java     http://localhost:8085  -> HTTP 200  <h1>Hello World</h1>

Browser screenshots for these three are in ../task-5-docker/screenshots.

Note on ports: 3000 and 5000 were already in use on my laptop, so I mapped the Node and
Python apps to 3001 and 5001. Port 8080 is taken by the multi-stage app above, so the
Java app was mapped to 8085. Only the host side of the mapping changed, the applications
still listen on their normal ports inside their containers.

## Cleanup

    docker rm -f multistage-app node-hello py-hello jv-hello
    docker rmi multistage-hello nodejs-hello python-hello java-hello

## What I understood

A multi-stage Dockerfile is several FROM lines in one file. Each FROM starts a new stage
with a clean filesystem, and COPY --from=<stage> pulls specific files out of an earlier
one. Only the last stage becomes the image you ship.

The reason to do this is that the tools you need to build something are usually not the
tools you need to run it. A compiler, a package manager with dev dependencies, and the
source tree are all build time things. Leaving them in the final image makes it bigger
and gives an attacker more to work with.

EXPOSE in the Dockerfile is only documentation. What actually made the app reachable on
port 8080 was -p 8080:3000 on docker run, which reads as host port colon container port.
That is also why the app can listen on 3000 internally and still be served on 8080.
