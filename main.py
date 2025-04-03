# Eventlet monkey patching is already applied in app.py
import logging
from app import app, socketio
import chat
import auth

# Configure logger
logger = logging.getLogger(__name__)
logger.info("Starting application with Socket.IO support via eventlet")

# For gunicorn, we need to expose both app and socketio 
# Create application variable for gunicorn to use
# To properly handle WebSocket connections, we need to use eventlet worker class
# e.g. gunicorn --worker-class eventlet -w 1 main:app
application = app  # For gunicorn

# For direct execution with python
if __name__ == "__main__":
    # Using socketio.run with eventlet for WebSocket support
    socketio.run(app, host="0.0.0.0", port=5000, debug=True, use_reloader=True, log_output=True)
