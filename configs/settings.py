# -*- coding: utf-8 -*-

SOCIALOAUTH_SITES = (
    ('google', 'socialoauth.sites.google.Google', 'Google',
        {
          'redirect_uri': 'http://m.maybi.cn/account/oauth/google',
          'client_id': '',
          'client_secret': '',
          'scope': 'email profile openid'
        }
    ),
    ('facebook', 'socialoauth.sites.facebook.Facebook', 'Facebook',
        {
          'redirect_uri': 'http://m.maybi.cn/account/oauth/facebook',
          'client_id': '',
          'client_secret': '',
        }
    ),
    ('instagram', 'socialoauth.sites.instagram.Instagram', 'Instagram',
        {
          'redirect_uri': 'http://m.maybi.cn/account/oauth/instagram',
          'client_id': '',
          'client_secret': '',
        }
    ),
    ('twitter', 'socialoauth.sites.twitter.XTwitter', 'X (Twitter)',
        {
          'redirect_uri': 'http://m.maybi.cn/account/oauth/twitter',
          'client_id': '',
          'client_secret': '',
        }
    ),
)


AWS_ACCESS_KEY_ID = ''
AWS_SECRET_ACCESS_KEY = ''

OPENEXCHANGERATES_APPID = ""

FOURPX_TOKEN = ""

BING_APPID = ''
BING_APPSECRET = '='


GOOGLE_APIKEY = ""
