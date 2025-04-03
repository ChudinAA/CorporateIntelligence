from app import app, socketio
import chat 

# This is required for gunicorn to find the app
application = app

if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=5000, debug=True)
