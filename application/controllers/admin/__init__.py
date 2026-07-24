# -*- coding: utf-8 -*-
import datetime

from flask import redirect, url_for, request
from flask_admin.contrib.mongoengine import ModelView
from flask_admin import BaseView, expose, AdminIndexView
from flask_admin.base import MenuLink
from flask_babel import gettext as _
from flask_login import current_user

import application.models as Models
from application.utils import format_date
from application.extensions import admin
from .dashboard import IndexView
from .i18n import COMMON_LABELS, MODEL_LABELS, CATEGORY_ZH

class Roled(object):

    def is_accessible(self):
        if not current_user.is_authenticated:
            return False
        roles_accepted = getattr(self, '_permission', 'admin')

        m = Models.BackendPermission.objects(
            name=roles_accepted).first()
        if 'ADMIN' in current_user.roles:
            return True
        if m and m.roles:
            accessible = any(
                [role in current_user.roles for role in m.roles]
            )
            return accessible
        return False

    def _handle_view(self, name, *args, **kwargs):
        if not current_user.is_authenticated or not self.is_accessible():
            return redirect(url_for(
                'frontend.login',
                next=url_for(self.endpoint + '.' + name, **request.args)))


class AdminView(Roled, BaseView):
    pass


class PermissionModelView(Roled, ModelView):

    def __init__(self, *args, **kwargs):
        self._permission = kwargs.pop('permission', 'admin')
        return super(PermissionModelView, self).__init__(*args, **kwargs)


class MBModelView(PermissionModelView):
    column_type_formatters = {datetime.datetime:
                              lambda view, value: format_date(value)}

    def __init__(self, model, *args, **kwargs):
        # Set column_labels BEFORE super().__init__ so that
        # _refresh_cache (called inside super) picks up Chinese labels
        # when caching _list_columns via get_column_name.
        self._apply_zh_labels(model)
        super(MBModelView, self).__init__(model, *args, **kwargs)

        # Translate category if in mapping
        if hasattr(self, '_category') and self._category in CATEGORY_ZH:
            self._category = CATEGORY_ZH[self._category]

    def _apply_zh_labels(self, model):
        """Apply Chinese labels from i18n module — unconditional, no silent failure."""
        model_name = model.__name__
        labels = dict(COMMON_LABELS)
        if model_name in MODEL_LABELS:
            labels.update(MODEL_LABELS[model_name])

        field_names = list(model._fields.keys())
        model_labels = {k: v for k, v in labels.items() if k in field_names}

        # Direct overwrite — no isinstance check, no try/except
        self.column_labels = model_labels
        self.form_labels = dict(model_labels)

        # Populate form_args so flask_mongoengine model_form() generates
        # WTForm fields with Chinese labels (Flask-Admin 1.6.1 does NOT
        # auto-merge form_labels into form_args for MongoEngine backends).
        self.form_args = {k: {'label': v} for k, v in model_labels.items()}


class PermissionMenuLink(Roled, MenuLink):
    def __init__(self, *args, **kwargs):
        self.permission = kwargs.pop('permission', 'admin')
        return super(PermissionMenuLink, self).__init__(*args, **kwargs)


class AuthenticatedMenuLink(MenuLink):
    def is_accessible(self):
        return current_user.is_authenticated


class NotAuthenticatedMenuLink(MenuLink):
    def is_accessible(self):
        return not current_user.is_authenticated


from . import models, dashboard, content, order
