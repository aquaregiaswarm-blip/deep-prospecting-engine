#!/bin/bash
set -e

# Start FastAPI backend
uvicorn src.api.main:app --host 0.0.0.0 --port 8000 &

# Start Next.js frontend
cd /app/frontend-standalone
HOSTNAME="0.0.0.0" PORT=3000 node server.js &

# Wait for either process to exit
wait -n
exit $?
