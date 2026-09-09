#!/bin/bash
set -e

echo "Waiting for PostgreSQL to accept connections..."
python -c '
import socket, time
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
while True:
    try:
        s.connect(("db", 5432))
        s.close()
        break
    except socket.error:
        time.sleep(0.5)
'

echo "Running Database Migrations (Alembic)..."
alembic upgrade head

echo "Starting ChainTrace-I4C FastAPI Application..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload