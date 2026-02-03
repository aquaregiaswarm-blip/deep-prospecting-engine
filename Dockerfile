# --- Stage 1: Frontend build ---
FROM node:20-slim AS frontend-builder

WORKDIR /app/frontend

COPY frontend/package.json frontend/package-lock.json* ./
RUN npm install --frozen-lockfile 2>/dev/null || npm install

COPY frontend/ .
RUN npm run build

# --- Stage 2: Python API ---
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential curl \
    && rm -rf /var/lib/apt/lists/*

# Install Node.js for Next.js standalone server
RUN curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/*

# Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Copy built frontend
COPY --from=frontend-builder /app/frontend/.next/standalone ./frontend-standalone
COPY --from=frontend-builder /app/frontend/.next/static ./frontend-standalone/.next/static
COPY --from=frontend-builder /app/frontend/public ./frontend-standalone/public

# Create directories
RUN mkdir -p data/chromadb output

# Expose ports: FastAPI (8000) + Next.js (3000)
EXPOSE 8000 3000

# Start script
COPY docker-entrypoint.sh /docker-entrypoint.sh
RUN chmod +x /docker-entrypoint.sh

HEALTHCHECK CMD curl --fail http://localhost:8000/api/health || exit 1

CMD ["/docker-entrypoint.sh"]
