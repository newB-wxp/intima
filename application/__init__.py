# -*- coding: utf-8 -*-

# Monkey-patch: flask-mongoengine requires flask.json.JSONEncoder removed in Flask 3.x
import flask.json
import json as _json
flask.json.JSONEncoder = _json.JSONEncoder

import configs
from . import models
from . import services
from .app import create_app
