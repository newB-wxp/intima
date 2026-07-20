# -*- coding: utf-8 -*-

# Monkey-patch: flask-mongoengine requires flask.json.JSONEncoder removed in Flask 3.x
import flask.json
import json as _json
flask.json.JSONEncoder = _json.JSONEncoder

# Monkey-patch: MongoEngine sends 'background' on _id index,
# MongoDB Atlas 7.0+ rejects any 'background' field on _id indexes (code 197)
from pymongo.collection import Collection

_original_create_index = Collection.create_index
_original_create_indexes = Collection.create_indexes


def _strip_background_from_id(index_or_indexes):
    """Remove 'background' from _id index specs (both single dict and list)."""
    if isinstance(index_or_indexes, list):
        return [
            {k: v for k, v in idx.items() if k != "background"}
            if isinstance(idx, dict) and idx.get("key", {}).get("_id") is not None
            else idx
            for idx in index_or_indexes
        ]
    if isinstance(index_or_indexes, dict) and index_or_indexes.get("key", {}).get("_id") is not None:
        return {k: v for k, v in index_or_indexes.items() if k != "background"}
    return index_or_indexes


def _patched_create_index(self, keys, **kwargs):
    return _original_create_index(self, _strip_background_from_id(keys), **kwargs)


def _patched_create_indexes(self, indexes, **kwargs):
    return _original_create_indexes(self, _strip_background_from_id(indexes), **kwargs)


Collection.create_index = _patched_create_index
Collection.create_indexes = _patched_create_indexes

import configs
from . import models
from . import services
from .app import create_app
