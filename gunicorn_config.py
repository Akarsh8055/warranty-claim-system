import os

# Get port from environment variable
bind = "0.0.0.0:10000"

# Worker configuration
workers = 2
threads = 1
worker_class = 'sync'
worker_connections = 1000
timeout = 30
keepalive = 2

# Logging
accesslog = '-'
errorlog = '-'
loglevel = 'info'

# SSL Configuration (if needed)
keyfile = None
certfile = None

# Server mechanics
daemon = False
pidfile = None
umask = 0
user = None
group = None
tmp_upload_dir = None

# Debugging
reload = False
reload_engine = 'auto'
spew = False
check_config = False

# Worker configuration - reduce for Render's free tier
workers = 2
threads = 1
timeout = 120
worker_class = "sync"

# Logging configuration
accesslog = "-"
errorlog = "-"
loglevel = "info"
capture_output = True
enable_stdio_inheritance = True

# Worker timeout
graceful_timeout = 60

# Maximum requests per worker
max_requests = 1000
max_requests_jitter = 50 