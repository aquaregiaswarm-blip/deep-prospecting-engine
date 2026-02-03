FROM node:20-slim AS builder

WORKDIR /app

# Copy package files
COPY package.json ./
COPY package-lock.json* ./

# Install dependencies
RUN if [ -f package-lock.json ]; then npm ci; else npm install; fi

# Copy source
COPY . .

# API URL baked in at build time
ENV NEXT_PUBLIC_API_URL=https://dpe-backend-841327020312.us-east1.run.app

# Build
RUN npx next build

# --- Production ---
FROM node:20-slim

WORKDIR /app

COPY --from=builder /app/.next/standalone ./
COPY --from=builder /app/.next/static ./.next/static
COPY --from=builder /app/public ./public/

EXPOSE 3000

ENV PORT=3000
ENV HOSTNAME="0.0.0.0"

CMD ["node", "server.js"]
