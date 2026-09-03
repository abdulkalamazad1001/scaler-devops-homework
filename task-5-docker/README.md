# Docker Homework: Hello World Applications

Name: T. Abdul Kalam Azad

Roll number: 24BCS10053

Six Hello World web apps, each in its own folder with its own Dockerfile. All of them
were built and run, and the Hello World page was checked in a browser. The screenshots
are in the screenshots folder.

## Folder structure

    task-5-docker/
      nodejs-app/     Node.js and Express
      python-app/     Python and Flask
      java-app/       Java, using the HTTP server built into the JDK
      Apache-app/     Apache HTTP server serving a static page
      React-app/      React built with Vite, served by Nginx
      nginx-app/      Nginx serving a static page
      screenshots/    browser screenshots of each app
      README.md

## Summary of all six

    App          Base image                  Container port   Host port used
    nodejs-app   node:20-alpine              3000             3001
    python-app   python:3.12-slim            5000             5001
    java-app     eclipse-temurin:21 (2 stage) 8080            8080
    Apache-app   httpd:2.4-alpine            80               8081
    nginx-app    nginx:1.27-alpine           80               8082
    React-app    node build, nginx runtime   80               8083

Ports 3000 and 5000 were already in use on my laptop, so I mapped the Node and Python
apps to 3001 and 5001 instead. The container port stays the same, only the host side
changes.

## 1. nodejs-app

An Express server that returns a Hello World page.

Files: package.json, server.js, Dockerfile, .dockerignore

The Dockerfile:

    FROM node:20-alpine

    # Tells Express and the npm packages to run in production mode
    ENV NODE_ENV=production

    WORKDIR /app

    COPY package.json ./
    RUN npm install --omit=dev

    COPY server.js ./

    # The node image ships an unprivileged "node" user.
    # Running as it means a bug in the app does not get root inside the container.
    USER node

    EXPOSE 3000
    CMD ["npm", "start"]

Why package.json is copied before the source code: Docker caches each layer, so if only
server.js changes, the npm install layer is reused and the build is much faster.

Build and run:

    $ docker build -t nodejs-hello nodejs-app
    $ docker run -d --name node-hello -p 3001:3000 nodejs-hello

    $ docker logs node-hello
    > node server.js
    Node.js app listening on port 3000

    $ curl -s -o /dev/null -w "%{http_code}\n" http://localhost:3001
    200

Screenshot: screenshots/nodejs-app.png

## 2. python-app

A Flask app that returns the same page.

Files: requirements.txt, app.py, Dockerfile, .dockerignore

The Dockerfile:

    FROM python:3.12-slim

    # Send stdout and stderr straight through, so docker logs shows the
    # Flask output immediately instead of holding it in a buffer.
    ENV PYTHONUNBUFFERED=1
    # Do not litter the image with .pyc files
    ENV PYTHONDONTWRITEBYTECODE=1

    WORKDIR /app

    COPY requirements.txt ./
    RUN pip install --no-cache-dir -r requirements.txt

    COPY app.py ./

    # Run as an unprivileged user rather than root.
    # Port 5000 is above 1024, so no special privilege is needed to bind it.
    RUN useradd --create-home appuser
    USER appuser

    EXPOSE 5000
    CMD ["python", "app.py"]

One thing that matters: the app binds to 0.0.0.0 and not 127.0.0.1. If it bound to
localhost it would only be reachable from inside the container and the port mapping
would appear to do nothing.

Build and run:

    $ docker build -t python-hello python-app
    $ docker run -d --name py-hello -p 5001:5000 python-hello

    $ docker logs py-hello
     * Running on http://172.17.0.8:5000
    192.168.65.1 - - [01/Sep/2026 12:21:30] "GET / HTTP/1.1" 200 -

Screenshot: screenshots/python-app.png

## 3. java-app

A small server using com.sun.net.httpserver, which comes with the JDK, so there is no
Maven or Gradle and no external library.

Files: HelloWorld.java, Dockerfile

The Dockerfile uses two stages:

    # Stage 1: compile the class file with the full JDK
    FROM eclipse-temurin:21-jdk-alpine AS build
    WORKDIR /src
    COPY HelloWorld.java ./
    RUN javac HelloWorld.java

    # Stage 2: run it on the smaller JRE image, without the compiler
    FROM eclipse-temurin:21-jre-alpine
    WORKDIR /app
    COPY --from=build /src/HelloWorld.class ./

    EXPOSE 8080
    CMD ["java", "HelloWorld"]

The point of the two stages is that the compiler is only needed at build time. The final
image carries the compiled class and a JRE, not the whole JDK.

Build and run:

    $ docker build -t java-hello java-app
    $ docker run -d --name jv-hello -p 8080:8080 java-hello

    $ docker logs jv-hello
    Java app listening on port 8080

Screenshot: screenshots/java-app.png

## 4. Apache-app

No application code at all, just a static page dropped into the Apache image.

Files: index.html, Dockerfile

    FROM httpd:2.4-alpine

    # htdocs is the folder Apache serves by default
    COPY index.html /usr/local/apache2/htdocs/index.html

    EXPOSE 80

There is no CMD because the base image already starts Apache in the foreground. Adding
one would only override what already works.

Build and run:

    $ docker build -t apache-hello Apache-app
    $ docker run -d --name ap-hello -p 8081:80 apache-hello

Screenshot: screenshots/Apache-app.png

## 5. nginx-app

The same idea as Apache, only the folder Nginx serves from is different.

Files: index.html, Dockerfile

    FROM nginx:1.27-alpine

    COPY index.html /usr/share/nginx/html/index.html

    EXPOSE 80

Build and run:

    $ docker build -t nginx-hello nginx-app
    $ docker run -d --name ng-hello -p 8082:80 nginx-hello

Screenshot: screenshots/nginx-app.png

## 6. React-app

A real React app created with Vite, built into static files and served by Nginx.

Files: package.json, vite.config.js, index.html, src/main.jsx, src/App.jsx, Dockerfile,
.dockerignore

The Dockerfile:

    # Stage 1: build the React app into static files
    FROM node:20-alpine AS build
    WORKDIR /app
    COPY package.json ./
    RUN npm install
    COPY . .
    RUN npm run build

    # Stage 2: serve those static files with Nginx.
    # A React build is just HTML, CSS and JS, so no Node is needed at runtime.
    FROM nginx:1.27-alpine
    COPY --from=build /app/dist /usr/share/nginx/html

    EXPOSE 80

This is the most useful pattern of the six. Node with all the npm packages is only needed
to produce the dist folder. Once that exists, the app is plain static files, so the final
image is Nginx plus a few kilobytes, 76 MB instead of the 200 MB plus a Node runtime
image would cost.

Build and run:

    $ docker build -t react-hello React-app
    $ docker run -d --name rc-hello -p 8083:80 react-hello

One thing I noticed while checking this one: curl on the React app returns an almost
empty page with just a div and a script tag, because React builds the page in the
browser. So curl is not enough to verify it, you have to open it in a browser. The
screenshot confirms it renders.

Screenshot: screenshots/react-app.png

## Running everything at once

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

### The images that were built

    REPOSITORY      TAG       SIZE
    react-hello     latest    76.1MB
    nginx-hello     latest    75.9MB
    apache-hello    latest    105MB
    java-hello      latest    286MB
    python-hello    latest    234MB
    nodejs-hello    latest    209MB

### The running containers

    NAMES        IMAGE           STATUS          PORTS
    py-hello     python-hello    Up 3 seconds    0.0.0.0:5001->5000/tcp
    node-hello   nodejs-hello    Up 3 seconds    0.0.0.0:3001->3000/tcp
    rc-hello     react-hello     Up 28 seconds   0.0.0.0:8083->80/tcp
    ng-hello     nginx-hello     Up 28 seconds   0.0.0.0:8082->80/tcp
    ap-hello     apache-hello    Up 28 seconds   0.0.0.0:8081->80/tcp
    jv-hello     java-hello      Up 28 seconds   0.0.0.0:8080->8080/tcp

### Verifying all six

    $ for app in "Node.js 3001" "Python 5001" "Java 8080" \
                 "Apache 8081" "Nginx 8082" "React 8083"; do
        set -- $app
        echo "=== $1  http://localhost:$2 ==="
        code=$(curl -s -o /dev/null -w '%{http_code}' http://localhost:$2)
        body=$(curl -s http://localhost:$2 | grep -o '<h1>.*</h1>')
        echo "HTTP status: $code   $body"
      done

    === Node.js  http://localhost:3001 ===
    HTTP status: 200   <h1>Hello World</h1>

    === Python  http://localhost:5001 ===
    HTTP status: 200   <h1>Hello World</h1>

    === Java  http://localhost:8080 ===
    HTTP status: 200   <h1>Hello World</h1>

    === Apache  http://localhost:8081 ===
    HTTP status: 200   <h1>Hello World</h1>

    === Nginx  http://localhost:8082 ===
    HTTP status: 200   <h1>Hello World</h1>

    === React  http://localhost:8083 ===
    HTTP status: 200   (rendered in the browser, see the screenshot)

### Cleanup

    docker rm -f node-hello py-hello jv-hello ap-hello ng-hello rc-hello
    docker rmi nodejs-hello python-hello java-hello apache-hello nginx-hello react-hello

## Improvements made after the first run

Two of the Dockerfiles were tightened up after the six apps were first built and
screenshotted.

nodejs-app now sets ENV NODE_ENV=production and ends with USER node, so the container
runs as the unprivileged node user the official image already provides, instead of as
root. Nothing in the app needs root, so there is no reason to hand it over.

python-app now sets PYTHONUNBUFFERED=1, so docker logs shows Flask output as it happens
rather than holding it in a buffer, and PYTHONDONTWRITEBYTECODE=1 so no .pyc files are
baked into the image. It also creates an appuser account and switches to it with USER.
Port 5000 is above 1024, so binding it does not need root. A .dockerignore was added as
well, matching the one the Node app already had.

The Apache and Nginx images were left alone on purpose. Those base images start a root
master process only to bind port 80 and then run their worker processes as an
unprivileged user, so the privilege drop is already built in. The Java image keeps its
two stage JDK to JRE build, which is the same idea applied to image size rather than to
privilege.

The command output recorded above is from the original run, before these two edits. The
edits change who the process runs as and how its output is flushed, not what the apps
serve or which ports they listen on.

## What I understood from doing this

A Dockerfile is just the setup steps you would run by hand, written down. Pick a base
image, copy the code in, install what it needs, say which port it uses, and give the
command that starts it.

EXPOSE is documentation only, it does not publish anything. The -p flag on docker run is
what actually opens the port, and it reads as host port colon container port.

The app has to listen on 0.0.0.0 rather than 127.0.0.1, otherwise it is only reachable
from inside its own container.

Layer order matters. Copying the dependency file and installing before copying the source
means edits to the source do not force a reinstall.

Multi stage builds make a real difference. The React image ended up at 76 MB because only
the finished static files were kept, while the Node image that still needs a runtime is
209 MB.

The two static apps, Apache and Nginx, need no CMD at all, since their base images
already start the server. The three application images need a CMD because nothing would
run otherwise.
