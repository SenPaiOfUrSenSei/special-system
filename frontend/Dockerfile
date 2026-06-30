FROM node:20-alpine

WORKDIR /app

# Copy package files and install dependencies
COPY package*.json ./
RUN npm ci

# Copy application files
COPY . .

# Expose Vite dev server port
EXPOSE 5173

# Start Vite dev server with host flag to allow Docker interface binding
CMD ["npm", "run", "dev", "--", "--host"]
