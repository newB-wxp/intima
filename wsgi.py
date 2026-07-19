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

# Monkey-patch: Flask 3.x removed app.json_encoder property,
# but flask-mongoengine's override_json_encoder still uses it.
import flask as _flask_pkg

def _json_encoder_getter(self):
    if not hasattr(self, '_json_encoder') or self._json_encoder is None:
        return _JSONEncoder
    return self._json_encoder

def _json_encoder_setter(self, value):
    self._json_encoder = value

_flask_pkg.Flask.json_encoder = property(_json_encoder_getter, _json_encoder_setter)

from application.app import create_app

flask_env = os.environ.get('FLASK_ENV', 'production')
app = create_app(config=flask_env)
