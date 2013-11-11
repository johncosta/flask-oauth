import json

from flask import session

from auth import requires_auth
from app import app


@app.route('/', methods=['GET'])
@requires_auth
def index():

    if 'user' in session:
        user = session['user']
        print user
    else:
        user = None

    return json.dumps(user)
