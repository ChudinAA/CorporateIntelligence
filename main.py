# No need for eventlet monkey patching with Threading mode
# We'll use the standard threading approach which works with gunicorn's sync worker

from app import app, socketio
import chat
import auth

# This is the variable that gunicorn expects - the WSGI application
# Using the Flask app directly as the WSGI application
app = app  # Explicit variable setting for clarity

# For direct execution with python
if __name__ == "__main__":
    # Use eventlet worker with socketio
    socketio.run(app, host="0.0.0.0", port=5000, debug=True, use_reloader=True, log_output=True)
