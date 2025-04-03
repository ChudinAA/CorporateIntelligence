#!/usr/bin/env python3
# A custom startup script that runs the app using eventlet worker for WebSocket support

import subprocess
import sys
import os

def main():
    """
    Start the gunicorn server with eventlet worker for proper WebSocket support.
    """
    # Set environment variables for proper operation
    os.environ['PYTHONUNBUFFERED'] = '1'
    os.environ['EVENTLET_NO_GREENDNS'] = 'yes'
    
    # Command to run gunicorn with the proper worker class
    cmd = [
        'gunicorn',
        '--worker-class', 'eventlet',
        '--workers', '1',
        '--bind', '0.0.0.0:5000',
        '--timeout', '120',
        '--log-level', 'debug',
        '--access-logfile', '-',
        '--error-logfile', '-',
        '--reload',
        'main:application'
    ]
    
    # Execute the command
    try:
        print("Starting server with eventlet worker for WebSocket support...")
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error starting server: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("Server stopped by user")
        sys.exit(0)

if __name__ == '__main__':
    main()