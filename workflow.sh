#!/bin/bash

# Start the application with Gunicorn using eventlet worker
# This setup is optimized for WebSocket connections with Socket.IO

export PYTHONUNBUFFERED=1

# Run with eventlet worker
gunicorn \
  --bind 0.0.0.0:5000 \
  --worker-class eventlet \
  --workers 1 \
  --log-level debug \
  --access-logfile - \
  --error-logfile - \
  --timeout 120 \
  main:application