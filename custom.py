# this file imports custom routes into the experiment server

from flask import Blueprint, render_template, request, jsonify, Response, abort, current_app, flash, Flask
from jinja2 import TemplateNotFound
from functools import wraps
from sqlalchemy import or_, and_
from sqlalchemy.orm.exc import NoResultFound

from psiturk.psiturk_config import PsiturkConfig
from psiturk.experiment_errors import ExperimentError
from psiturk.user_utils import PsiTurkAuthorization, nocache

# # Database setup
from psiturk.db import db_session, init_db
from psiturk.models import Participant

from json import dumps, loads

import datetime
import socketio
from coordinator import Coordinator
import uuid
import json

from custom_models import User
#from database import db_session, init_db



# load the configuration options
config = PsiturkConfig()
config.load_config()
myauth = PsiTurkAuthorization(config)  # if you want to add a password protect route use this


custom_code = Blueprint('custom_code', __name__, template_folder='templates', static_folder='static')

# modified psiturk will look for sio to inject as WSGI middleware
sio = socketio.Server(logger=True)


@custom_code.record
def record(state):
    try:
        u = User('admin', 'admin@localhost')
        db_session.add(u)
        db_session.commit()
    except Exception as e:
        print(e)

    print("custom.py blueprint registered")
    

#currently unnecessary as client gets socket.io.js from the web
@custom_code.route('/socket.io/socket.io.js')
def get_siojs():
    print('trying to serve socketio file')
    with open('static/socket.io/socket.io.js') as fin:
        data = fin.read()
        return data, 200, {'Content-Type': 'application/javascript; charset=utf-8'}
    # return app.send_static_file('socket.io/socket.io.js')

@custom_code.route("/test", methods=['GET', 'POST'])
def test5():
    data =  json.dumps({'success':True, 'apple':'orange'})
    print(data)
    response = Response(
        response=data,
        status=200,
        mimetype='application/json'
    )
    
    return response

@sio.on('test')
def save(message, data):
    print(str(args))
    print("socket test received by flask")
    data =  json.dumps({'success':True, 'func' : 'save'})
    response = Response(
        response=data,
        status=200,
        mimetype='application/json'
    )
    
    return response

@sio.on('new_user')
def new_user(message, data):
    print('new user request receieved')
    c.register_user(id)
    return "new user response"

    
@sio.on('button')
def button(sid, data):
    print("button click: ", str(data), 'now query: ')

    try:
        q = User.query.all()
        print(q)
    except Exception as e:
        print(e)
    
    sio.emit('push', {'func' : 'action'})


@sio.on('connect')
def test_connect(sid, environ):
    print("flask-socketio connected")
    sio.emit('test_response', {'data': 'Connected'})


@custom_code.route("/")
def blah():
    print("/")
    #print(current_app.config)
    return "blah"

@custom_code.teardown_request
def shutdown_session(exception=None):
    db_session.remove()


    
if __name__=="__main__":
    app = Flask(__name__)
    app.register_blueprint(custom_code)
    app.wsgi_app = socketio.Middleware(sio, app.wsgi_app)
    app.config['SECRET_KEY'] = 'secret!'
    app.run(host='localhost', port=22361)