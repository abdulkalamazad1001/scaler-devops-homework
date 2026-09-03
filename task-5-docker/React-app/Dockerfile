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
