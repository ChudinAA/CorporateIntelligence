
#!/bin/bash

echo "Starting the application..."

# Create required directories
mkdir -p uploads
mkdir -p vector_db

# Run the application
echo "Starting Flask application with gunicorn..."
gunicorn --worker-class eventlet --workers 1 --bind 0.0.0.0:5000 --reuse-port --reload main:app
