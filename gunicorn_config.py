import os

# Get port from environment variable or use default
port = int(os.environ.get("PORT", 5001))

# Bind to all interfaces
bind = f"0.0.0.0:{port}"

# Worker configuration
workers = 4
threads = 2
timeout = 120
worker_class = "sync"

# Logging configuration
accesslog = "-"
errorlog = "-"
capture_output = True
enable_stdio_inheritance = True

# Worker timeout
graceful_timeout = 120

# Keep-alive
keepalive = 5

# Maximum requests per worker
max_requests = 1000
max_requests_jitter = 50 