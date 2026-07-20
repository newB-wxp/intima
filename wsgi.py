#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
WSGI Entry Point for Gunicorn
Usage: gunicorn wsgi:app -w 3 -b 0.0.0.0:5000
"""

# ============================================================
# CRITICAL: Must patch pymongo BEFORE any other import touches it.
# MongoEngine sends 'background' on _id index, which MongoDB
# Atlas 7.0+ rejects with code 197 (InvalidIndexSpecificationOption).
# ============================================================
import pymongo.collection as _pm_col

_orig_create_index = _pm_col.Collection.create_index
_orig_create_indexes = _pm_col.Collection.create_indexes


def _strip_background_from_id(idx):
    """Remove 'background' from _id index specs."""
    if isinstance(idx, list):
        return [_strip_background_from_id(i) for i in idx]
    if isinstance(idx, dict) and idx.get("key", {}).get("_id") is not None:
        return {k: v for k, v in idx.items() if k != "background"}
    return idx


def _patched_create_index(self, keys, **kwargs):
    return _orig_create_index(self, _strip_background_from_id(keys), **kwargs)


def _patched_create_indexes(self, indexes, **kwargs):
    return _orig_create_indexes(self, _strip_background_from_id(indexes), **kwargs)


_pm_col.Collection.create_index = _patched_create_index
_pm_col.Collection.create_indexes = _patched_create_indexes
# ============================================================

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
