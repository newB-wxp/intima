#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Bibi Application Entry Point (Flask CLI compatible)
Usage:
    flask run                          # development server
    flask run --host=0.0.0.0 --port=5000
    gunicorn wsgi:app                  # production

Environment variables:
    FLASK_APP=manage.py
    FLASK_ENV=development|production|test
"""
import os
from application.app import create_app

# Determine environment from FLASK_ENV (Flask 2.3 still reads this)
flask_env = os.environ.get('FLASK_ENV', 'development')
app = create_app(config=flask_env)

if __name__ == '__main__':
    app.run()
