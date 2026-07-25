# -*- coding: utf-8 -*-
import datetime

from flask import redirect, url_for, request
from flask_admin.contrib.mongoengine import ModelView
from flask_admin import BaseView, expose, AdminIndexView
from flask_admin.base import MenuLink
from flask_babel import gettext as _
from flask_login import current_user
from mongoengine import ReferenceField, ListField

import application.models as Models
from application.utils import format_date
from application.extensions import admin
from .dashboard import IndexView
from .i18n import COMMON_LABELS, MODEL_LABELS, CATEGORY_ZH

class Roled(object):

    def is_accessible(self):
        if not current_user.is_authenticated:
            return False
        if 'ADMIN' in current_user.roles:
            return True

        roles_accepted = getattr(self, '_permission', 'admin')
        m = Models.BackendPermission.objects(
            name=roles_accepted).first()
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

        # Exclude heavy ListField(ReferenceField) from list columns
        # to avoid massive N+1 queries on list view.
        self._optimize_ref_columns(model)

        # Replace full objects.all() dropdowns with AJAX search for
        # ReferenceField in create/edit forms.  This prevents the form
        # from loading the entire referenced collection (thousands of
        # Order / User / Post documents) into a <select> widget.
        self._setup_form_ajax_refs(model)

        super(MBModelView, self).__init__(model, *args, **kwargs)

        # Translate category if in mapping
        if hasattr(self, '_category') and self._category in CATEGORY_ZH:
            self._category = CATEGORY_ZH[self._category]

    # ------------------------------------------------------------------
    # ReferenceField N+1 query optimizations
    # ------------------------------------------------------------------

    def _detect_ref_fields(self, model=None):
        """Return (scalar_refs, list_refs) where each is {field_name: model_cls}.

        Accepts an optional ``model`` parameter to support calling before
        ``super().__init__()`` has set ``self.model`` (during startup).
        When omitted, falls back to ``self.model`` (available at runtime).
        """
        _model = model or self.model
        scalar = {}
        list_refs = {}
        for name, field in _model._fields.items():
            if isinstance(field, ReferenceField):
                scalar[name] = field.document_type_obj
            elif (isinstance(field, ListField)
                  and hasattr(field, 'field')
                  and isinstance(field.field, ReferenceField)):
                list_refs[name] = field.field.document_type_obj
        return scalar, list_refs

    def _optimize_ref_columns(self, model):
        """Auto-exclude ListField(ReferenceField) from column_list."""
        _, list_refs = self._detect_ref_fields(model=model)
        if list_refs:
            existing = set(self.column_exclude_list or ())
            self.column_exclude_list = list(existing | set(list_refs.keys()))

    def _setup_form_ajax_refs(self, model):
        """Replace ReferenceField <select> dropdowns with AJAX-search widgets.

        Without this, every ReferenceField in a create/edit form renders an
        ``<select>`` containing *every* document from the referenced
        collection (e.g. thousands of Orders / Users).  ``form_ajax_refs``
        tells Flask-Admin to use a Select2 widget that lazy-loads results
        via an AJAX endpoint instead.
        """
        refs, _ = self._detect_ref_fields(model=model)
        if not refs:
            return

        # Build sensible default search fields per referenced model.
        # Sub-classes can override by setting their own form_ajax_refs
        # before calling super().__init__().
        existing = dict(getattr(self, 'form_ajax_refs', {}) or {})
        for field_name in refs:
            if field_name in existing:
                continue
            existing[field_name] = {'fields': ['name', 'title', 'id']}

        if existing:
            self.form_ajax_refs = existing

    def get_list(self, page, sort_field, sort_desc, search, filters,
                 page_size=None):
        count, data = super(MBModelView, self).get_list(
            page, sort_field, sort_desc, search, filters, page_size)

        if not data:
            return count, data

        # Batch pre-fetch all scalar ReferenceField values to avoid
        # per-row lazy-load queries (N+1). We read from _data (raw DBRef)
        # to avoid triggering the lazy load, then inject the pre-fetched
        # object back into _data so subsequent getattr() finds it directly.
        refs, _ = self._detect_ref_fields()
        for field_name, ref_model in refs.items():
            # Collect (ref_id, [rows]) mapping from raw _data
            rid_map = {}
            for row in data:
                raw = row._data.get(field_name)
                if raw is not None:
                    rid = raw.id if hasattr(raw, 'id') else raw
                    rid_map.setdefault(rid, []).append(row)

            if not rid_map:
                continue

            # Single batch query for all referenced objects
            objects = list(ref_model.objects(id__in=list(rid_map.keys())))
            obj_map = {str(obj.id): obj for obj in objects}

            # Inject pre-fetched objects into _data to skip lazy load
            for rid, rows in rid_map.items():
                obj = obj_map.get(str(rid))
                if obj is not None:
                    for row in rows:
                        row._data[field_name] = obj

        return count, data

    # ------------------------------------------------------------------
    # Chinese label support
    # ------------------------------------------------------------------

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
