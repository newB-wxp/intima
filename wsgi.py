#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
WSGI Entry Point for Gunicorn
Usage: gunicorn wsgi:app -w 3 -b 0.0.0.0:5000
"""
import os
import json as _json

# Monkey-patch: flask-mongoengine 1.0.0 needs flask.json.JSONEncoder,
# which was removed in Flask 2.3+. Inject it before any app import.
import flask.json as _flask_json
import datetime as _datetime
from bson import ObjectId as _ObjectId

class _JSONEncoder(_json.JSONEncoder):
    def default(self, o):
        if isinstance(o, _ObjectId):
            return str(o)
        if isinstance(o, _datetime.datetime):
            return o.isoformat()
        try:
            return super().default(o)
        except TypeError:
            return str(o)

_flask_json.JSONEncoder = _JSONEncoder

from application.app import create_app

flask_env = os.environ.get('FLASK_ENV', 'production')
app = create_app(config=flask_env)
