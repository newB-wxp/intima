# -*- coding: utf-8 -*-
"""
Bibi OAuth Module — Authlib-based Google + Facebook authentication.

Supports:
  - Google OAuth 2.0
  - Facebook OAuth 2.0

Routes:
  GET /api/auth/oauth/google/login     → redirect to Google
  GET /api/auth/oauth/google/callback  → handle Google callback
  GET /api/auth/oauth/facebook/login   → redirect to Facebook
  GET /api/auth/oauth/facebook/callback → handle Facebook callback
"""

import json

from flask import Blueprint, request, jsonify, redirect, url_for, current_app, session
from flask_login import login_user
from authlib.integrations.flask_client import OAuth

import application.models as Models
from application.services.json_tmpl import get_user_info


oauth_bp = Blueprint('oauth_bp', __name__, url_prefix='/api/auth/oauth')

oauth = OAuth()


def init_oauth(app):
    """Initialize OAuth with the Flask app. Call during app creation."""
    oauth.init_app(app)

    oauth.register(
        name='google',
        client_id=app.config.get('GOOGLE_CLIENT_ID', ''),
        client_secret=app.config.get('GOOGLE_CLIENT_SECRET', ''),
        authorize_url='https://accounts.google.com/o/oauth2/v2/auth',
        authorize_params=None,
        access_token_url='https://oauth2.googleapis.com/token',
        access_token_params=None,
        refresh_token_url=None,
        redirect_uri=None,
        client_kwargs={'scope': 'openid email profile'},
        server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    )

    oauth.register(
        name='facebook',
        client_id=app.config.get('FACEBOOK_APP_ID', ''),
        client_secret=app.config.get('FACEBOOK_APP_SECRET', ''),
        authorize_url='https://www.facebook.com/v18.0/dialog/oauth',
        authorize_params=None,
        access_token_url='https://graph.facebook.com/v18.0/oauth/access_token',
        access_token_params=None,
        refresh_token_url=None,
        redirect_uri=None,
        client_kwargs={'scope': 'email public_profile'},
    )


def _handle_oauth_callback(provider_name: str):
    """
    Shared OAuth callback handler.

    Flow:
      1. Exchange authorization code for token
      2. Fetch user profile from provider
      3. Find or create SocialOAuth record
      4. Find or create User
      5. Log user in, return JWT
    """
    try:
        oauth_client = getattr(oauth, provider_name, None)
        if not oauth_client:
            return jsonify(message='Failed', error=f'Unknown provider: {provider_name}'), 400

        token = oauth_client.authorize_access_token()

        if not token:
            return jsonify(message='Failed', error='Failed to obtain access token'), 400

        # Fetch user profile
        if provider_name == 'google':
            userinfo = oauth_client.get(
                'https://openidconnect.googleapis.com/v1/userinfo'
            ).json()
            provider_uid = userinfo.get('sub', '')
            email = userinfo.get('email', '')
            name = userinfo.get('name', '')
            avatar = userinfo.get('picture', '')

        elif provider_name == 'facebook':
            userinfo = oauth_client.get(
                'https://graph.facebook.com/v18.0/me?fields=id,name,email,picture'
            ).json()
            provider_uid = userinfo.get('id', '')
            email = userinfo.get('email', '')
            name = userinfo.get('name', '')
            avatar = userinfo.get('picture', {}).get('data', {}).get('url', '')

        else:
            return jsonify(message='Failed', error=f'Unsupported provider: {provider_name}'), 400

        if not email:
            return jsonify(message='Failed', error='Email not available from provider'), 400

        # Find or create SocialOAuth record
        social = Models.SocialOAuth.objects(
            provider=provider_name,
            provider_uid=provider_uid,
        ).first()

        if social:
            user = social.user
        else:
            # Check if user with this email already exists
            user = Models.User.objects(account__email=email, is_deleted=False).first()

            if not user:
                user = Models.User.create(
                    email=email,
                    name=name,
                    password=None,  # OAuth users have no password
                )

            # Create SocialOAuth record
            Models.SocialOAuth(
                user=user,
                provider=provider_name,
                provider_uid=provider_uid,
                avatar=avatar,
            ).save()

        login_user(user, remember=True)
        auth_token = user.generate_auth_token()

        return jsonify(
            message='OK',
            user=get_user_info(user),
            remember_token=auth_token,
        )

    except Exception as e:
        current_app.logger.error(f'OAuth {provider_name} error: {e}')
        return jsonify(message='Failed', error='Authentication failed. Please try again.'), 500


@oauth_bp.route('/google/login')
def google_login():
    """Redirect user to Google OAuth consent screen."""
    redirect_uri = url_for('oauth_bp.google_callback', _external=True)
    return oauth.google.authorize_redirect(redirect_uri)


@oauth_bp.route('/google/callback')
def google_callback():
    """Handle Google OAuth callback."""
    return _handle_oauth_callback('google')


@oauth_bp.route('/facebook/login')
def facebook_login():
    """Redirect user to Facebook OAuth consent screen."""
    redirect_uri = url_for('oauth_bp.facebook_callback', _external=True)
    return oauth.facebook.authorize_redirect(redirect_uri)


@oauth_bp.route('/facebook/callback')
def facebook_callback():
    """Handle Facebook OAuth callback."""
    return _handle_oauth_callback('facebook')
