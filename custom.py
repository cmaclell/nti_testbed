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
from coordinator import Coordinator
import uuid
import json

from custom_models import User, ActiveTask
#from database import db_session, init_db



# load the configuration options
config = PsiturkConfig()
config.load_config()
myauth = PsiTurkAuthorization(config)  # if you want to add a password protect route use this


custom_code = Blueprint('custom_code', __name__, template_folder='templates', static_folder='static')

# modified psiturk will look for sio to inject as WSGI middleware
sio = socketio.Server(logger=True)


# @custom_code.route('/Build/<path:path>')
# def send_Build(path):
#     print("serving " + str(path))
#     return send_from_directory('Build', path)



@custom_code.route('/TemplateData/<path:path>')
def send_Build(path):
    return send_from_directory('static/TemplateData', path)

@custom_code.route('/Build/<path:path>')
def send_template(path):   
    return send_from_directory('static/Build', path)

@custom_code.record
def record(state):
    try:
        u = User('127.0.0.1')
        db_session.add(u)
        db_session.commit()
    except Exception as e:
        print(e)

    print("custom.py blueprint registered")


#client gets socket.io.js from the web, webgl client gets it here
@custom_code.route('/js/socket.io.js', methods=['GET', 'POST'])
def get_siojs():
    with open("static/js/socket.io.js") as fin:
        data = fin.read()
        return data, 200, {'Content-Type': 'application/javascript; charset=utf-8'}

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

@sio.on('htmlMessage')
def html_message(message, data):
    print('html message: ' + str(data))

@sio.on('new_session')
def new_user(message, data):
    ip = data['ip'] 
    print('new user request receieved')
    # query checks if user is already in user table
    if True: #not User.query.filter(User.ip == ip).count() > 0:

        u = User(ip)
        #query gets a waiting user
        waiting = User.query.filter(User.assigned_task==False).order_by(User.last_active.desc()).first()
        if waiting is not None:
            #if random.random() < .5:\
            print("found match, creating game")
            t = ActiveTask(teacher = waiting.user_id, student = u.user_id)
            db_session.add(t)
            waiting.assigned_task = True
            u.assigned_task = True
        else:
            print("no waiting user, waiting") 

        db_session.add(u)
        db_session.commit()
    else:
        print("user already has requested new session, probably a bug")

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

@sio.on('action')
def test_connect(sid, environ):
    print("action received")
    

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
    init_db()
    new_user(None, {'ip':'127.0.0.1'})
    new_user(None, {'ip':'127.0.0.2'})
    # app = Flask(__name__)
    # app.register_blueprint(custom_code)
    # app.wsgi_app = socketio.Middleware(sio, app.wsgi_app)
    # app.config['SECRET_KEY'] = 'secret!'
    # app.run(host='localhost', port=22361)