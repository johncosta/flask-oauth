from flask import request, session, render_template, redirect, url_for

from auth import requires_auth, request_token
from app import app


@app.route('/', methods=['GET', 'POST'])
@requires_auth
def index():

    if 'user' in session:
        user = session['user']
        print user
    else:
        user = None

    if request.method == 'POST':
        # post
        pass

    data = {
        'user': user,
        'is_staff': user['is_staff'],
    }

    return render_template('index.html', **data)
