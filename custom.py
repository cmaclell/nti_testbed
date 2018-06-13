# this file imports custom routes into the experiment server

from flask import Blueprint, render_template, request, jsonify, Response, abort, current_app, flash
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

# load the configuration options
config = PsiturkConfig()
config.load_config()
myauth = PsiTurkAuthorization(config)  # if you want to add a password protect route use this

# explore the Blueprint
custom_code = Blueprint('custom_code', __name__, template_folder='templates', static_folder='static')

sio = socketio.Server(logger=True)

thread = None

@sio.on('test')
def save(*args):
    print(str(args))
    print("connected")

@sio.on('save')
def save(sid):
    print("save" + str(sid))
    
@sio.on('requestGameState')
def requestGameState(sid):
    print("requestGameState")
    
@sio.on('action')
def action(sid):
    print("action")

@sio.on('connect', namespace='/test')
def test_connect(sid, environ):
    sio.emit('my response', {'data': 'Connected', 'count': 0}, room=sid,
             namespace='/test')

@custom_code.route('/')
def index():
    print "\nkitchen sink log\n"
    #global thread
    # thread is None:
       #thread = sio.start_background_task(background_thread)
    return "kitchen sink response"

    
# if __name__=="__main__":
#     app = Flask(__name__)
#     app.wsgi_app = socketio.Middleware(sio, app.wsgi_app)
#     app.config['SECRET_KEY'] = 'secret!'
#