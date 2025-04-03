# Apply eventlet monkey patching at the very beginning
try:
    import eventlet
    eventlet.monkey_patch()
    print("Eventlet monkey patching applied")
    async_mode = 'eventlet'
except ImportError:
    print("Eventlet not available, using threading mode")
    async_mode = 'threading'

import logging
import os
from app import app, socketio
import chat
import auth

# Configure logger
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# For gunicorn, we need to expose both app and socketio
# This is the WSGI application variable that gunicorn will use
app = app  # For gunicorn

# For direct execution with python
if __name__ == "__main__":
    # Using socketio.run with eventlet for WebSocket support
    port = int(os.environ.get("PORT", 5000))
    logger.info(f"Starting server on port {port} with {async_mode} mode")
    socketio.run(
        app, 
        host="0.0.0.0", 
        port=port, 
        debug=True, 
        use_reloader=True, 
        log_output=True
    )
