#!/bin/bash

echo "Starting the application..."

# Create required directories
mkdir -p uploads
mkdir -p vector_db

# Kill any gunicorn processes if running
pkill -f gunicorn || true

# Run the application with Python directly to use eventlet properly
echo "Starting Flask application with SocketIO..."
python -u main.py
