# this file imports custom routes into the experiment server

from flask import Blueprint, render_template, request, jsonify, Response, abort, current_app, flash, Flask, send_from_directory
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
import uuid
import json

from custom_models import User, Task, State


# load the configuration options
config = PsiturkConfig()
config.load_config()
myauth = PsiTurkAuthorization(config)  # if you want to add a password protect route use this


custom_code = Blueprint('custom_code', __name__, template_folder='templates', static_folder='static')

# modified psiturk will look for attribute "sio" to inject as WSGI middleware
sio = socketio.Server(logger=True)


@custom_code.route('/TemplateData/<path:path>')
def send_Build(path):
    return send_from_directory('static/TemplateData', path)

@custom_code.route('/Build/<path:path>')
def send_template(path):   
    return send_from_directory('static/Build', path)

@custom_code.record
def record(state):
    # try:
    #     u = User('127.0.0.1')
    #     db_session.add(u)
    #     db_session.commit()
    # except Exception as e:
    #     print(e)

    print("custom.py blueprint registered")


#client gets socket.io.js from the web, webgl client gets it here
@custom_code.route('/js/socket.io.js', methods=['GET', 'POST'])
def get_siojs():
    with open("static/js/socket.io.js") as fin:
        data = fin.read()
        return data, 200, {'Content-Type': 'application/javascript; charset=utf-8'}


@sio.on('new_user')
def new_user(message, data):

    #sio.on(data).emit("initialize", {"actor":"trainer","id":data})
    #return

    uid = data#.get('uid', 'uid-not-found')
    user = User.query.filter(User.user_id==uid).first()
    exists = False

    print('new user request receieved')
    
    if user is None:
        user = User(uid, ip='127.0.0.1')
        db_session.add(user)

    #query gets a waiting user
    waiting = User.query.filter(User.task==None).order_by(User.last_active.desc()).first()

    if waiting is not None:
        #if random.random() < .5:\
        print("found match, creating game")
        t = ActiveTask()
        waiting.task = t
        user.task = t
        waiting.role = 'teacher'
        user.role = 'student'
        
        db_session.add(t)

        sio.on(waiting.user_id).emit("initialize", {"actor":"trainer","id":waiting.user_id})
        sio.on(user.user_id).emit("initialize", {"actor":"student","id":user.user_id})
        
    else:
        print("no waiting user, waiting") 

    db_session.commit()

    return "new user response"

    
@sio.on('button')
def button(sid, data):
    print("button click: ", str(data), 'now query: ')
    print("lock buttons")
    sio.emit("lockButtons")
    sio.emit("lock")
    try:
        q = User.query.all()
        print(q)
    except Exception as e:
        print(e)
    
    sio.emit('push', {'func' : 'action'})

@sio.on('user_id')
def user_id(sid, data):
    print("user id connected: " + str(data))
    sio.emit("init", "session-225")

@sio.on('action')
def test_connect(sid, environ):
    print("action received")
    

@sio.on('connect')
def test_connect(sid, environ):
    print("flask-socketio connection established")


@custom_code.route("/")
def blah():
    print("/")
    #print(current_app.config)
    return "blah"

@custom_code.teardown_request
def shutdown_session(exception=None):
    db_session.remove()


if __name__=="__main__":
    init_db()
    new_user(None, 'tempid12')
    new_user(None, 'tempid13')
    # app = Flask(__name__)
    # app.register_blueprint(custom_code)
    # app.wsgi_app = socketio.Middleware(sio, app.wsgi_app)
    # app.config['SECRET_KEY'] = 'secret!'
    # app.run(host='localhost', port=22361)