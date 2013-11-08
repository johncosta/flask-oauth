from flask import Flask

app = Flask(__name__)
app.config.from_object(__name__)
app.secret_key = "add this"

if __name__ == '__main__':
    import auth
    from controller import *

    #http://tech.nickserra.com/2011/11/16/django-runserver-and-gevent-
    # notimplementederror-gevent-is-only-usable-from-a-single-thread/
    from gevent import monkey
    monkey.patch_all()
    
    # Development keys
    auth.REDIRECT_URI = 'http://localhost:5000/oauth_authorized'
    auth.CLIENT_ID = ""
    auth.CLIENT_SECRET = ""

    params = {"debug": True,
              "host":"0.0.0.0",}

    app.run(**params)