FROM node:20-alpine

WORKDIR /app

# Copy the package files first so this layer is cached
# and npm install only re-runs when dependencies change
COPY package.json ./
RUN npm install --omit=dev

COPY server.js ./

EXPOSE 3000
CMD ["npm", "start"]
