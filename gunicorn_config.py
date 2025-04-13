import os

# Get port from environment variable
port = int(os.environ.get("PORT", 10000))
bind = f"0.0.0.0:{port}"

# Worker configuration
workers = 2
threads = 1
worker_class = 'sync'
timeout = 120

# Logging
accesslog = '-'
errorlog = '-'
loglevel = 'info'
capture_output = True
enable_stdio_inheritance = True

# Server mechanics
daemon = False
pidfile = None
umask = 0
user = None
group = None

# Keep-alive
keepalive = 2

# Maximum requests per worker
max_requests = 1000
max_requests_jitter = 50

# SSL Configuration (if needed)
keyfile = None
certfile = None

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

# Server mechanics
tmp_upload_dir = None

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