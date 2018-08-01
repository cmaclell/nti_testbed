from flask import Blueprint, session, render_template, request, jsonify, Response, abort, current_app, flash, Flask, send_from_directory
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

import datetime
import flask_socketio
import socketio
import uuid
import json
import sys
import traceback

#our stuff
from custom_models import User, Task, Event
from util import exception
import pattern

#psiturk looks for this blueprint to register endpoints
custom_code = Blueprint('custom_code', __name__, template_folder='templates', static_folder='static')

# modified psiturk looks for this attribute to inject as WSGI middleware into the flask app
sio = socketio.Server(logger=True)

# load the configuration options
config = PsiturkConfig()
config.load_config()
myauth = PsiTurkAuthorization(config)  # if you want to add a password protect route use this


connections = {} # map: socket-id -> user-id
games = {} # map: user-id -> task object (both user-ids)
queue = [] # list of unmatched user-ids


### SETUP/TEARDOWN ###
@custom_code.record
@exception
def record(state):
    pass # fires on blueprint registration

@custom_code.teardown_request
@exception
def shutdown_session(exception=None):
    db_session.remove()

### HTTP API ###
@custom_code.route('/TemplateData/<path:path>')
@exception
def send_Build(path):
    print('serving template data')
    return send_from_directory('static/TemplateData', path)

@custom_code.route('/Build/<path:path>')
@exception
def send_template(path):   
    return send_from_directory('templates/Build', path)

@custom_code.route('/js/<path:path>', methods=['GET', 'POST'])
@exception
def get_siojs(path):
    with open("static/js/" + path) as fin:
        data = fin.read()
        return data, 200, {'Content-Type': 'application/javascript; charset=utf-8'}

### STANDARD WEBSOCKET API ###
@sio.on('connect')
@exception
def connected(sid, environ):
    pass # print("new socket connection")
    
@sio.on('disconnect')
@exception
def disconnect(sid):
    pass # print("socket connection closed")

@sio.on('join')
@exception
def on_join(sid, data):
    # assign socket id to psiturk 

    room = data['id']
    sio.enter_room(sid, room)

    # user is reconnecting
    if room in list(connections.values()):
        if room in games:
            games[room].reconnect(room)

    # user is new
    else:
        room = data['id']
        if config.getboolean("Task Parameters", "single_player"):
            testing_user(room)
        else:
            register_user(room)

    # emit instructions corresponding to users role"
    if "first" in data:
        sio.emit("instructions", games[room].role_string(room))
        
    connections[sid] = room
    

### UNITY WEBSOCKET API ENDPOINTS ###
@sio.on('action')
@exception
def action(sid, data):
    
    """action(action_info-> as json)
    The unity game sends this function each time it performs an action, which could be setting a waypoint, 
    or clicking any of the two to four action buttons (go, clear waypoints, pickup object, put down object) 
    Feed this JSON back into action() (sent from flask to unity) to make the unity game perform this action. 
    You can also feed just the prior state into load() to reset the scene back to how it was before the action was taken.
    """
    uid = connections.get(sid, None)
    game = games.get(uid, None)

    if game is not None:
        #print("size of action object before: " + str(sys.getsizeof(data)))
        #data["prior state"] = None
        #print("size of action object after: " + str(sys.getsizeof(data)))
        game.event(uid, event_type='action', event_data=data)
        
   
@sio.on('initialState')
@exception
def initialState(sid, data):
    """
    initialState(serialized_state-> as json)
    The initial state of the unity game. Called when the unity game first connects and each time 
    it reconnects after it resets from the reset button. Gives the game state that can be fed into load() 
    to make the game state be how it is initially
    """
    uid = connections.get(sid, None)
    game = games.get(uid, None)

    if game is not None:
        if game.student == uid:
        #game.event(uid, event_type='set_initial_state', event_data=data)
            #game.initial_state = data
            #sio.emit('load', game.initial_state, room=game.teacher)
            game.event(uid, event_type='initial_state', event_data=data)


   

### HTML API ENDPOINTS ###
@sio.on('getChatMessage')
@exception
def getChatMessage(sid, data):
    """
    getChatMessage({'message': "-",'id': "-"})
    Sends a message typed into the chat box to the server. It is called when the user presses the 
    send button next to the chat box. The text is in message, and the id is the id of the user gotten 
    from the psiturk id (the same id used in join as shown below)
    """
    uid = connections.get(sid, None)
    game = games.get(uid, None)

    if game is not None:
        game.event(uid, event_type='chat', event_data=data['message'])

@sio.on('onTrainingButtonPress')
@exception
def onTrainingButtonPress(sid, data):
    """
    onTrainingButtonPress(({'identifier': "-",'id': "-"})
    The html interface calls this function when the user clicks any of the buttons that the html interface 
    was sent with the function getTrainingButtons(). The identifier is the identifier that was sent with 
    the button and the id is the id of the user gotten from the psiturk id (the same id used in join as shown below)
    """
    uid = connections.get(sid, None)
    game = games.get(uid, None)

    if game is not None:
        game.event(uid, event_type='button', event_data=data['identifier'])

    print("training button pressed: ", data['identifier'])

def testing_user(uid):
    if uid not in games:
        new_game = pattern.HtmlUnityTest(sio=sio, user=uid)
        sio.emit("sendTrainingMessage", "SYSTEM: Entering sandbox mode.", room=uid)
        games[uid] = new_game

### MODALITY LOGIC ### 
def register_user(uid):
    if uid not in queue:
        queue.append(uid)

    if len(queue) > 1 and uid not in games:
       
        a = queue.pop(0)
        b = queue.pop(0)

        new_game = pattern.HtmlUnityObserve(sio=sio, teacher=a, student=b)

        games[a] = new_game
        games[b] = new_game
        
        print("new game created between: " + str(a) + ' and ' + str(b))
        sio.emit("sendTrainingMessage", "SYSTEM: You've been matched as teacher.", room=a)
        sio.emit("sendTrainingMessage", "SYSTEM: You've been matched as student.", room=b)
    else:
        sio.emit("sendTrainingMessage", "SYSTEM: Waiting for a partner.", room=uid)

    # new_user = User.query.filter(User.user_id==uid).first()
    #waiting = User.query.filter(User.task==None).order_by(User.last_active.desc()).first()
    #new_user = User(uid, ip='127.0.0.1')
    #db_session.commit()
  
if __name__=="__main__":
    app = Flask(__name__)
    app.register_blueprint(custom_code)
    app.wsgi_app = socketio.Middleware(sio, app.wsgi_app)
    app.run(host='localhost', port=5000)