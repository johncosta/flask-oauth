import json
import requests
from functools import wraps

from flask import url_for, request, session, redirect, g, abort

from app import app

# TODO add your base url for example it might be:
BASE_URL = "http://localhost:8000"
AUTHORIZE_URL = BASE_URL + '/api/v1/o/authorize/?client_id={client_id}&response_type=code'
TOKEN_URL = BASE_URL + '/api/v1/o/token/'

# TODO get these from the environment
# TODO set these by registering them with the application
CLIENT_ID = ''
CLIENT_SECRET = ''

# This is the redirect back to the url of this app
REDIRECT_BASE_URL = ""
REDIRECT_URI = REDIRECT_BASE_URL + '/oauth_authorized'

API_ENDPOINT = BASE_URL + '/api/v1/user_info/'


def authenticate():
    session['auth_next_url'] = request.url
    return redirect(AUTHORIZE_URL.format(client_id=CLIENT_ID))

def request_token(code=None, refresh_token=None):
    if code is None and refresh_token is None:
        raise TypeError('You must specify either a code or a refresh_token')
    token_args = {
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET,
        'redirect_uri': REDIRECT_URI,
        'scopes': '',
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
    print "Before request post"
    r = requests.post(TOKEN_URL, data=token_args)
    print "After request post"
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
    r = requests.get(
        API_ENDPOINT,
        headers={'Authorization': 'Bearer {0}'.format(token['access_token'])}
    )
    if r.status_code == requests.codes.ok:
       g.user = json.loads(r.text)
       session['user'] = g.user


def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if g.user:
            if g.user.get('is_staff') is not True:
                g.user = None
                session.pop('token', None)
                abort(401)
            return f(*args, **kwargs)
        if not 'token' in session:
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
