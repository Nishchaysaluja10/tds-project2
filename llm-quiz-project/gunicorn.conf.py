# Gunicorn configuration file
import os

# Bind to the port provided by Render (default 10000)
port = os.environ.get("PORT", "10000")
bind = f"0.0.0.0:{port}"

# Worker configuration
workers = 2

# Timeouts
# CRITICAL: Increase timeout to 10 minutes (600s) to handle long quiz chains (16+ steps)
# Default is 30s which causes "WORKER TIMEOUT" crashes at later stages.
timeout = 600
