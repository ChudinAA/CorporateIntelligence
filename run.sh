#!/bin/bash
# Start the Flask application with gunicorn and eventlet worker
# This ensures the WebSocket support works properly
# The worker class eventlet is required for WebSocket support with Socket.IO
# Use only 1 worker for WebSocket proper functionality
exec gunicorn --worker-class eventlet -w 1 --bind 0.0.0.0:5000 --reuse-port --reload main:application