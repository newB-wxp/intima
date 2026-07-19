# -*- coding: utf-8 -*-
"""
Bibi Project - Gunicorn Configuration
======================================
Production WSGI server configuration.

Usage:
    gunicorn -c gunicorn.conf.py wsgi:app
"""

import os
import multiprocessing

# ===========================================
# Server Socket
# ===========================================
bind = os.environ.get("GUNICORN_BIND", "0.0.0.0:8000")
backlog = 2048

# ===========================================
# Worker Processes
# ===========================================
# Recommended: (2 * CPU cores) + 1
_cores = multiprocessing.cpu_count()
workers = int(os.environ.get("GUNICORN_WORKERS", min(_cores * 2 + 1, 4)))
worker_class = "sync"
worker_connections = 1000
max_requests = 1000
max_requests_jitter = 50
timeout = int(os.environ.get("GUNICORN_TIMEOUT", 120))
graceful_timeout = 30
keepalive = 5

# ===========================================
# Preload
# ===========================================
# Preload app before forking workers (saves memory, but disables live reload)
preload_app = True

# ===========================================
# Logging
# ===========================================
accesslog = os.environ.get("GUNICORN_ACCESS_LOG", "logs/gunicorn-access.log")
errorlog = os.environ.get("GUNICORN_ERROR_LOG", "logs/gunicorn-error.log")
loglevel = os.environ.get("GUNICORN_LOG_LEVEL", "info")
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# ===========================================
# Process Naming
# ===========================================
proc_name = "bibi"

# ===========================================
# Server Mechanics
# ===========================================
daemon = False
pidfile = None
umask = 0
user = None
group = None
tmp_upload_dir = None

# ===========================================
# SSL (uncomment when certificate available)
# ===========================================
# keyfile = "/etc/ssl/private/bibi.shop.key"
# certfile = "/etc/ssl/certs/bibi.shop.crt"
