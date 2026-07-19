# -*- coding: utf-8 -*-
"""
Shim package to provide JSONEncoder for flask-mongoengine 1.0.0 compatibility.
flask-mongoengine expects `from flask_json import JSONEncoder`, but the real
flask-json package no longer exports this class.
"""
import json
import datetime
from bson import ObjectId


class JSONEncoder(json.JSONEncoder):
    """JSON encoder with mongoengine/BSON type support."""
    def default(self, o):
        if isinstance(o, ObjectId):
            return str(o)
        if isinstance(o, datetime.datetime):
            return o.isoformat()
        try:
            return super().default(o)
        except TypeError:
            return str(o)
