FROM node:20-alpine

# Tells Express and the npm packages to run in production mode
ENV NODE_ENV=production

WORKDIR /app

# Copy the package files first so this layer is cached
# and npm install only re-runs when dependencies change
COPY package.json ./
RUN npm install --omit=dev

COPY server.js ./

# The node image ships an unprivileged "node" user.
# Running as it means a bug in the app does not get root inside the container.
USER node

EXPOSE 3000
CMD ["npm", "start"]
