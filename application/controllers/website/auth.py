# -*- coding: utf-8 -*-
import json
import urllib
import uuid
import os
import time
import re
from itertools import chain
from uuid import uuid4
import application.models as Models
from flask import Blueprint, request, jsonify, current_app, redirect, render_template
from flask_login import current_user, login_user, logout_user, \
    login_required
from flask_babel import gettext as _

from socialoauth import SocialSites, SocialAPIError
from configs.settings import SOCIALOAUTH_SITES

from application.extensions import redis
import application.services.jobs as Jobs
import application.services.json_tmpl as Json
from application.services.user import add_oauth
from application.services.cache import cached

auth = Blueprint('auth', __name__, url_prefix='/api/auth')

# Supported OAuth platforms
SUPPORTED_OAUTH_PLATFORMS = ['google', 'facebook', 'instagram', 'twitter']

def get_oauth_token(sitename, code):
    if not code or code == 'authdeny':
        return None, 'No code'

    socialsites = SocialSites(SOCIALOAUTH_SITES)
    s = socialsites.get_site_object_by_name(sitename)
    try:
        s.get_access_token(code)
    except SocialAPIError as e:
        current_app.logger.error(
            'SocialAPIError. sitename: {}; url: {}; msg: {}'.format(
                e.site_name, e.url, e.error_msg))
        return None, e.error_msg
    else:
        return s, ''


# GET /auth/logged_in
@auth.route('/user_info', methods=['GET'])
def user_info():
    if not current_user.is_authenticated:
        return jsonify(message='Failed', logged_in=False)

    info = Json.get_user_info(current_user)
    return jsonify(message='OK', logged_in=True, user=info)


# GET /auth/logout
@auth.route('/logout', methods=['GET'])
def logout():
    if current_user.is_authenticated:
        logout_user()
    return jsonify(message='OK')


@auth.route('/oauth/links', methods=['GET'])
@cached(21600)
def oauth_links():
    def _link(site_class):
        _s = socialsites.get_site_object_by_name(site_class)
        a_content = _s.site_name
        return (_s.authorize_url, a_content)

    socialsites = SocialSites(SOCIALOAUTH_SITES)
    links = map(_link, SUPPORTED_OAUTH_PLATFORMS)
    return jsonify(message="OK", links=list(links))


@auth.route('/oauth/<sitename>', methods=['GET'])
def callback(sitename):
    from application.models import SocialOAuth

    code = request.args.get('code')
    s, msg = get_oauth_token(sitename, code)
    app = 'MOBILEWEB'

    if s is None:
        print(msg)
        return jsonify(message='Failed', error=msg)

    oauth = SocialOAuth.objects(site_uid=s.uid).first()

    if not oauth:
        oauth = SocialOAuth.create(
            s.site_name, s.uid, s.name, s.access_token,
            s.expires_in, s.refresh_token,
            app=app,
            gender=s.gender)

        path = 'avatar/{}/{}.jpeg'.format(
            oauth.user.id, str(time.time()).replace('.', ''))
        Jobs.image.save_avatar('maybi-img', path, url=s.avatar_large,
                               save_original=True)
        url = "http://assets.maybi.cn/%s" % path
        oauth.update_avatar(url)
        user_id = str(oauth.user.id)
        login_user(oauth.user, remember=True)
        return jsonify(message='OK', login=False, user_id=user_id)

    else:
        oauth.re_auth(s.access_token, s.expires_in, s.refresh_token, None)
        if oauth.user.account.is_email_verified:
            login_user(oauth.user, remember=True)
            return jsonify(message='OK', login=True,
                           remember_token=oauth.user.generate_auth_token(),
                           user=Json.get_user_info(oauth.user))
        else:
            user_id = str(oauth.user.id)
            return jsonify(message='OK', login=False,
                           user_id=user_id)


# POST /login_email  DATA: email, password
@auth.route('/login_email', methods=['POST'])
def login_email():
    data = request.json
    email = (data.get('email') or '').strip().lower()
    password = data.get('password', '')

    # Validate input
    if not email or len(email) > 254:
        return jsonify(message='Failed', error='Please enter a valid email address')
    if not password or len(password) > 128:
        return jsonify(message='Failed', error='Invalid email or password')

    user, authenticated = Models.User.authenticate(
        email=email, password=password)
    if not authenticated:
        return jsonify(message='Failed', error='Invalid email or password')
    login_user(user, remember=True)
    return jsonify(message='OK', user=Json.get_user_info(user),
                   remember_token=user.generate_auth_token())


@auth.route('/login_with_token', methods=['POST'])
def login_with_token():
    data = request.json
    token = data.get('token', '')
    user = Models.User.verify_auth_token(token)
    if not user:
        return jsonify(message='Failed')
    login_user(user, remember=True)
    return jsonify(message='OK', user=Json.get_user_info(user),
                   remember_token=user.generate_auth_token())


@auth.route('/signup', methods=['POST'])
def email_signup():
    data = request.json
    email = (data.get('email') or '').strip().lower()
    password = data.get('password', '')
    confirm_password = data.get('confirm_password', '')
    name = (data.get('name') or '').strip()

    # Validate email format
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not email or not re.match(email_pattern, email):
        return jsonify(message='Failed', error='Please enter a valid email address')

    # Validate email length
    if len(email) > 254:
        return jsonify(message='Failed', error='Email address is too long')

    # Validate password strength: min 8 chars, must contain uppercase, lowercase, digit
    if not password or len(password) < 8:
        return jsonify(message='Failed',
                       error='Password must be at least 8 characters')
    if len(password) > 128:
        return jsonify(message='Failed', error='Password is too long')
    if not re.search(r'[A-Z]', password):
        return jsonify(message='Failed',
                       error='Password must contain at least one uppercase letter')
    if not re.search(r'[a-z]', password):
        return jsonify(message='Failed',
                       error='Password must contain at least one lowercase letter')
    if not re.search(r'[0-9]', password):
        return jsonify(message='Failed',
                       error='Password must contain at least one digit')

    # Validate confirm password
    if password != confirm_password:
        return jsonify(message='Failed', error='Passwords do not match')

    # Validate name
    if name and len(name) > 100:
        return jsonify(message='Failed', error='Name is too long')

    # Check email uniqueness
    if Models.User.objects(account__email=email):
        return jsonify(message='Failed', error='This email has already been registered')

    if not name:
        name = 'User' + str(time.time()).replace('.', '')[:10]

    user = Models.User.create(email=email, password=password, name=name)

    login_user(user, remember=True)
    return jsonify(message='OK', user=Json.get_user_info(user),
                   remember_token=user.generate_auth_token())


@auth.route('/bind_email', methods=['POST'])
def bind_email():
    email = request.json.get('email')
    user_id = request.json.get('user_id')
    if not email:
        return jsonify(message='Failed', error=_('no email'))
    if Models.User.objects(account__email=email):
        return jsonify(message='Failed', error=_('The email already exists'))
    u = Models.User.objects(id=user_id).first()
    u.account.email = email
    u.account.is_email_verified = True
    u.save()
    login_user(u, remember=True)

    return jsonify(message='OK', user=Json.get_user_info(u),
                   remember_token=u.generate_auth_token())


@auth.route('/change_password', methods=['POST'])
@login_required
def change_password():
    original_password = request.json.get('original_password', '')
    user = current_user._get_current_object()
    if not user.account.check_password(original_password):
        return jsonify(message='Failed', error=_('Wrong password'))
    password = request.form.get('password', '')
    if not password.isalnum():
        return jsonify(message='Failed',
                       error=_('Password contains illegal characters'))
    if len(password) < 6:
        return jsonify(message='Failed', error=_('Password is too short'))
    update_password(user, password)
    return jsonify(message='OK')


@auth.route('/forgot_password', methods=['POST'])
def forgot_password():
    email = request.json.get('email')
    if not email:
        return jsonify(message='Failed',
                       error=_('Please correct the email format'))
    user = Models.User.objects(account__email=email).first()
    if not user:
        return jsonify(message='Failed',
                       error=_('Sorry, no user found for that email address'))

    user.account.activation_key = str(uuid4())
    user.save()
    url = "http://account.may.bi/account/confirm_reset_password?activation_key=%s&email=%s" % \
        (user.account.activation_key, user.account.email)
    html = render_template('admin/user/_reset_password.html',
                           username=user.name, url=url)
    Jobs.noti.send_mail.delay([user.account.email],
                              _('Reset your password in ') + 'Maybi',
                              html)
    return jsonify(message='OK')
