# -*- coding: utf-8 -*-

import os
import re
import shutil

# Force-clear stale bytecode cache to ensure latest .py is loaded
_app_dir = os.path.dirname(os.path.abspath(__file__))
for root, dirs, files in os.walk(_app_dir):
    if '__pycache__' in dirs:
        shutil.rmtree(os.path.join(root, '__pycache__'), ignore_errors=True)
from redis import ConnectionPool
from datetime import datetime
from itsdangerous import TimestampSigner
from werkzeug.middleware.proxy_fix import ProxyFix
from flask import Flask, request, jsonify, g, session, current_app, redirect, render_template
from flask_principal import PermissionDenied, identity_loaded
from flask_babel import gettext as _

from application.extensions import (
    db, mail, cache, admin, login_manager,
    principal, bcrypt, babel, toolbar, assets,
    redis, session_redis, mongo_inventory, csrf
)
import configs.config as ConfigsModel
from application.services.permission import principal_on_identity_loaded
from application.redis_session_interface import RedisSessionInterface

from application.utils import format_date, timesince, timeuntil, size_normal, \
    url_for_other_page, get_session_key
from application.utils.sentry import init_sentry
from application.utils.rate_limit import init_limiter


# For import *
__all__ = ['create_app']


def create_app(config=None, app_name=None, blueprints=None):
    """Create a Flask app."""

    if app_name is None:
        app_name = ConfigsModel.BaseConfig.PROJECT

    if app_name != ConfigsModel.APP_NAME.worker:
        import application.controllers as Controllers

    app = Flask(app_name,
                static_folder='application/static',
                template_folder='application/templates')

    configure_app(app, config)
    init_sentry(app)
    configure_hook(app, app_name)
    configure_extensions(app)
    configure_blueprints(app, app_name, blueprints)
    configure_logging(app)
    configure_template_filters(app)
    configure_error_handlers(app)
    if app_name != ConfigsModel.APP_NAME.worker:
        configure_admin(app)
        configure_oauth(app)

    from application.commands import register_commands
    register_commands(app)

    app.wsgi_app = ProxyFix(app.wsgi_app)
    return app


def configure_app(app, config):
    """
    Configure app from object, parameter and env.
    @config the config of application
        - is either an string ['test','production','staging', 'development']
        - or an configuration object
    """
    BaseConfig = ConfigsModel.BaseConfig

    config = ConfigsModel.get_config_from_host(app.name)
    app.config.from_object(config)

    # Override setting by env var without touching codes.
    app.config.from_envvar(
        '%s_APP_CONFIG' % BaseConfig.PROJECT.upper(), silent=True)


def configure_extensions(app):
    # flask-MongoEngine
    db.init_app(app)
    db.register_connection(**app.config.get('ORDER_DB_CONFIG'))
    db.register_connection(**app.config.get('INVENTORY_DB_CONFIG'))
    db.register_connection(**app.config.get('CART_DB_CONFIG'))
    db.register_connection(**app.config.get('CONTENT_DB_CONFIG'))
    db.register_connection(**app.config.get('LOG_DB_CONFIG'))

    mongo_inventory.init_app(app, uri=app.config.get('MONGO_INVENTORY_URI'))


    redis_url = app.config.get('REDIS_URL', 'redis://localhost:6379')
    redis.connection_pool = ConnectionPool.from_url(redis_url)
    session_redis.connection_pool = ConnectionPool.from_url(
        redis_url,
        encoding='utf-8',
        encoding_errors='strict',
        decode_responses=False,
    )

    # server side session
    app.session_interface = RedisSessionInterface(session_redis)

    # flask-mail
    mail.init_app(app)
    mail.app = app

    # flask-cache
    cache.init_app(app)

    # flask-bcrypt
    bcrypt.init_app(app)

    # Force Chinese locale for admin routes; use browser preference for frontend
    def get_locale():
        if request.path.startswith('/admin'):
            return 'zh_Hans_CN'
        return request.accept_languages.best_match(
            app.config.get('ACCEPT_LANGUAGES', ['zh', 'en']),
            app.config.get('BABEL_DEFAULT_LOCALE', 'zh'))

    # flask-babel 4.0: locale_selector must be passed to init_app, not as decorator
    babel.init_app(app, locale_selector=get_locale)

    # flask-assets
    assets.init_app(app)

    # flask-wtf CSRF
    csrf.init_app(app)

    # flask-talisman (security headers)
    if app.config.get('TALISMAN_ENABLED'):
        from flask_talisman import Talisman
        Talisman(app, **app.config.get('TALISMAN_CONFIG', {}))

    # flask_debugtoolbar
    toolbar.init_app(app)

    # flask-login (not configured will raise 401 error)
    login_manager.login_view = 'frontend.login'
    # login_manager.refresh_view = 'frontend.reauth'

    @login_manager.user_loader
    def load_user(id):
        import application.models as Models
        return Models.User.objects(id=id, is_deleted=False).first()

    login_manager.init_app(app)
    login_manager.login_message = _('Please log in to access this page.')
    login_manager.needs_refresh_message = _(
        'Please reauthenticate to access this page.')

    # flask-principal (must be configed after flask-login!!!)
    principal.init_app(app)

    @identity_loaded.connect_via(app)
    def on_identity_loaded(sender, identity):
        principal_on_identity_loaded(sender, identity)


def configure_blueprints(app, app_name, blueprints):
    """Configure blueprints in views."""

    if app_name == ConfigsModel.APP_NAME.worker:
        return

    import application.controllers as Controllers

    if app_name == ConfigsModel.APP_NAME.maybi:
        blueprints = Controllers.default_blueprints

    elif app_name == ConfigsModel.APP_NAME.admin:
        blueprints = [Controllers.frontend.frontend]

    else:
        blueprints = Controllers.default_blueprints

    if blueprints:
        for blueprint in blueprints:
            app.register_blueprint(blueprint)


def configure_template_filters(app):
    from flask_login import current_user
    app.jinja_env.globals['current_user'] = current_user
    app.jinja_env.globals['url_for_other_page'] = url_for_other_page
    app.jinja_env.globals['hasattr'] = hasattr

    # Context processor: inject cart_count into all templates
    @app.context_processor
    def inject_cart_count():
        count = 0
        try:
            if (current_user and hasattr(current_user, 'is_authenticated')
                    and current_user.is_authenticated):
                from application.models import Cart
                cart = Cart.objects(user_id=current_user.id).first()
                if cart and hasattr(cart, 'items'):
                    count = sum(getattr(item, 'quantity', 0) for item in cart.items)
        except Exception:
            pass
        return dict(cart_count=count)

    # Context processor: inject categories into all templates
    @app.context_processor
    def inject_categories():
        try:
            from application.utils.categories import get_all_categories
            categories = get_all_categories()
            return dict(categories=categories)
        except Exception:
            return dict(categories=[])

    filters = app.jinja_env.filters

    filters['timesince'] = timesince
    filters['timeuntil'] = timeuntil
    filters['format_date'] = format_date


def configure_logging(app):
    """Initialize unified logging via application.utils.logger."""
    from application.utils.logger import init_app_logger
    init_app_logger(app)

    # Register request logging (DEV_MODE only)
    from application.utils.request_logger import register_request_logging
    register_request_logging(app)


def configure_hook(app, name):

    @app.before_request
    def before_request():
        pass


def configure_error_handlers(app):

    @app.errorhandler(PermissionDenied)
    def permission_error(error):
        ''' permission denied exception from flask principal'''
        return jsonify(
            message='Failed', code=403, error=_('Permission Denied'))

    @app.errorhandler(401)
    def login_required_page(error):
        ''' exception thrown out by flask login'''
        return jsonify(message='Failed', code=401, error=_('Login required'))

    @app.errorhandler(404)
    def page_not_found(error):
        '''Render friendly 404 page for HTML requests.'''
        if request.path.startswith('/api/'):
            return jsonify(message='Not Found', code=404, error=_('Resource not found'))
        return render_template('errors/404.html'), 404

    @app.errorhandler(500)
    def internal_server_error(error):
        '''Render friendly 500 page for HTML requests.'''
        if request.path.startswith('/api/'):
            return jsonify(message='Server Error', code=500, error=_('Internal server error'))
        return render_template('errors/500.html'), 500

    # Enhanced error handlers (500 stack trace logging, friendly error pages)
    from application.utils.error_handler import register_error_handlers
    register_error_handlers(app)


def configure_admin(app):
    # flask-admin
    import logging
    logger = logging.getLogger(__name__)
    from application.controllers.admin.dashboard import IndexView
    from flask_admin.base import MenuLink

    # Diagnostic: dump all registered views
    view_list = [(v.name, getattr(v, '_category', '-'), v.__class__.__name__)
                 for v in admin._views]
    logger.warning(f"[ADMIN-DIAG] Total views registered: {len(view_list)}")
    for i, (name, cat, cls) in enumerate(view_list):
        logger.warning(f"[ADMIN-DIAG]   [{i}] {cls}: name='{name}' category='{cat}'")

    admin.name = u"Maybi后台"
    admin.base_template = 'admin/master2.html'
    admin.template_mode = 'bootstrap3'

    # Chinese menu links
    admin.add_link(MenuLink(name='返回首页', url='/', target='_blank'))
    admin.add_link(MenuLink(name='修改密码', endpoint='frontend.change_password'))
    admin.add_link(MenuLink(name='退出登录', endpoint='frontend.logout'))

    admin.init_app(app, index_view=IndexView(name="仪表盘"))


def configure_oauth(app):
    """Initialize Authlib OAuth (Google + Facebook)."""
    from application.utils.oauth import oauth_bp, init_oauth
    init_oauth(app)
    app.register_blueprint(oauth_bp)
