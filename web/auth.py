import json
import requests
import urllib

from flask import url_for, request, session, redirect, g, abort

from app import app
from functools import wraps


BASE_URL = "http://localhost:8000"
AUTHORIZE_URL = BASE_URL + '/account/o/authorize?'
TOKEN_URL = BASE_URL + '/account/o/token'

# Register these in your oauth provider or update them with different values
CLIENT_ID = "puwrUBe7"
CLIENT_SECRET = "yUnebuweTe4am5sWecA4"

# This is the redirect back to the url of this app
REDIRECT_BASE_URL = "http://localhost:5000"
REDIRECT_URI = REDIRECT_BASE_URL + '/oauth_authorized'


def authenticate():
    print "[authenticate]: in"
    session['auth_next_url'] = request.url
    params = {
        'response_type': 'token',
        'client_id':  CLIENT_ID,
        'secret': CLIENT_SECRET,
        'redirect_uri': REDIRECT_URI
    }
    encoded = urllib.urlencode(params)
    authentication_url = AUTHORIZE_URL + encoded
    print "[authenticate]: redirecting to authentication url: {0}".format(
        authentication_url)
    response = redirect(authentication_url)
    print "[authenticate]: response: {0}".format(response.__dict__)
    return response


def request_token(code=None, refresh_token=None):
    if code is None and refresh_token is None:
        raise TypeError('You must specify either a code or a refresh_token')
    token_args = {
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET,
        'redirect_uri': REDIRECT_URI,
        'scope': ''
    }
    if code:
        token_args.update({
            'grant_type': 'authorization_code',
            'code': code
        })
    elif refresh_token:
        token_args.update({
            'grant_type': 'refresh_token',
            'refresh_token': refresh_token
        })
    print "[request_token]: Before request post"
    r = requests.post(TOKEN_URL, data=token_args)
    print "[request_token]: After request post"
    r.raise_for_status()
    token = json.loads(r.text)
    if token.get('error'):
        raise ValueError(token.get('error_description') or
                         'Token request failed')
    return token


@app.before_request
def get_current_user():
    if request.path.startswith('/static'):
        return
    g.user = None
    token = session.get('token')
    if not token:
        return
    if 'user' in session:
        g.user = session['user']
        return
    #r = requests.get('{0}/me'.format(API_ENDPOINT),
    #    headers={'Authorization': 'Bearer {0}'.format(token['access_token'])})
    #if r.status_code == requests.codes.ok:
    #    g.user = json.loads(r.text)['object']
    #    session['user'] = g.user


def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        print "[requires_auth]: in"
        print "[requires_auth]: g: {0}".format(g)
        if g.user:
            if g.user.get('is_staff') is not True:
                g.user = None
                session.pop('token', None)
                abort(401)
            return f(*args, **kwargs)
        else:
            print "[requires_auth]: no user found"

        if not 'token' in session:
            print "[requires_auth]: no token found in session, authenticating"
            return authenticate()

        try:
            session['token'] = request_token(refresh_token=session['token']['refresh_token'])
            session.permanent = True
        except:
            return authenticate()
            
        get_current_user()
        if not g.user or g.user.get('is_staff') is not True:
            print("Auth error!!!")
            return 'Authentication error'
        print("Blah...")
        return f(*args, **kwargs)
        print "[requires_auth]: out"
    return decorated


@app.route('/logout')
def logout():
    session.pop('token', None)
    return redirect(url_for('index'))


@app.route('/login')
@requires_auth
def login():
    return redirect(request.referrer or url_for('index'))


@app.route('/oauth_authorized')
def oauth_authorized():
    print "In oauth"
    print "request.args.code: {0}".format(request.args.get('code'))
    try:
        if not request.args.get('code') or request.args.get('error'):
            return request.args.get('error_description', "Error")
    except Exception as e:
        return "Error = {0}".format(e)
    try:
        print "before request_token"
        session['token'] = request_token(code=request.args.get('code'))
        session.permanent = True
    except Exception as e:
        return e.message
    print "before redirect"
    return redirect(session.get('auth_next_url') or url_for('index'))
