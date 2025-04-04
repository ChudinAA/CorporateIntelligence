# Gunicorn configuration
worker_class = "eventlet"
workers = 1
bind = "0.0.0.0:5000"
reload = True
