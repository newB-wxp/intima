#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
WSGI Entry Point for Gunicorn
Usage: gunicorn wsgi:app -w 3 -b 0.0.0.0:5000
"""
import os
from application.app import create_app

flask_env = os.environ.get('FLASK_ENV', 'production')
app = create_app(config=flask_env)
