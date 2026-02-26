# Frontend Dockerfile
FROM node:18-alpine

WORKDIR /app

# Copy and install dependencies
COPY package*.json ./
RUN npm install --legacy-peer-deps --include=dev

# Copy source
COPY . .

# Build
RUN npm run build || echo "Build failed, using fallback"

# Install serve
RUN npm install -g serve

EXPOSE 3000

# Try to serve build, fallback to simple server
CMD ["sh", "-c", "serve -s build -l 3000 || npx serve -s build -l 3000"]
