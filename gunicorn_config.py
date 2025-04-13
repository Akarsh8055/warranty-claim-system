import os

# Get port from environment variable
port = int(os.environ.get("PORT", 10000))

# Bind to all interfaces
bind = f"0.0.0.0:{port}"

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

# Keep-alive
keepalive = 5

# Maximum requests per worker
max_requests = 1000
max_requests_jitter = 50 