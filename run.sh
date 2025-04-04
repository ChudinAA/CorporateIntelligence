
#!/bin/bash

echo "Starting the application..."

# Create required directories
mkdir -p uploads
mkdir -p vector_db

# Run the application with eventlet worker
echo "Starting Flask application with gunicorn..."
gunicorn --worker-class eventlet -w 1 --bind 0.0.0.0:5000 --reload main:app
