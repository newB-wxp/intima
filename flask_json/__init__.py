# -*- coding: utf-8 -*-
"""
Shim package for flask-mongoengine 1.0.0 compatibility.
flask-mongoengine imports JSONEncoder from both flask_json and flask.json,
but neither provides it in modern Flask/Python environments.
"""
import json as _json
import datetime as _datetime
from bson import ObjectId


class JSONEncoder(_json.JSONEncoder):
    """JSON encoder with mongoengine/BSON type support."""
    def default(self, o):
        if isinstance(o, ObjectId):
            return str(o)
        if isinstance(o, _datetime.datetime):
            return o.isoformat()
        try:
            return super().default(o)
        except TypeError:
            return str(o)


# Patch flask.json.JSONEncoder which was removed in Flask 2.3+
import flask.json as _flask_json
_flask_json.JSONEncoder = JSONEncoder
