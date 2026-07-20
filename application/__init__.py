# -*- coding: utf-8 -*-

# Monkey-patch: flask-mongoengine requires flask.json.JSONEncoder removed in Flask 3.x
import flask.json
import json as _json
flask.json.JSONEncoder = _json.JSONEncoder

# Monkey-patch: MongoEngine sends 'background' on _id index,
# MongoDB Atlas 7.0+ rejects any 'background' field on _id indexes (code 197)
from pymongo.collection import Collection

_original_create_indexes = Collection.create_indexes


def _patched_create_indexes(self, indexes, **kwargs):
    """Strip 'background' from _id index specs to avoid Atlas code 197."""
    fixed = []
    for idx in indexes:
        if isinstance(idx, dict) and idx.get("key", {}).get("_id") is not None:
            idx = {k: v for k, v in idx.items() if k != "background"}
        fixed.append(idx)
    return _original_create_indexes(self, fixed, **kwargs)


Collection.create_indexes = _patched_create_indexes

import configs
from . import models
from . import services
from .app import create_app
