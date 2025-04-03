#!/bin/bash
# Start the Flask application with gunicorn and eventlet worker
# This ensures the WebSocket support works properly
exec gunicorn --worker-class eventlet --bind 0.0.0.0:5000 --reuse-port --reload main:application