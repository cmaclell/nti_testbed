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
import socketio
import uuid
import json
import sys
import traceback
import random


#our stuff
#from custom_models import User, Task, Event
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
def on_ (sid, data):
    # assign socket id to psiturk 
    print("join request from " + str(data))
    room = data['id']
    sio.enter_room(sid, room)

    sio.emit("unlockChatBox", room=room)

    # user is reconnecting
    busy = False
    if room in list(connections.values()):
        if room in games:
            if not games[room].finished[room]:

                # probably not the best way of doing this
                if 'first' not in data:
                    games[room].read_instructions[room] = True

                #handle case of refreshing the page
                if 'first' in data and games[room].read_instructions[room]:
                    sio.emit("refresh", room=room)

                games[room].reconnect(room)
                busy = True
                
                
    # user is new
    if not busy:
        if config.getboolean("Task Parameters", "single_player"):
            testing_user(room)
        else:
            register_user(room)

    sio.emit("unlockChatBox", room=room)

    connections[sid] = room
    
@sio.on("sleep_callback")
def sleep_callback(sid, data):
    uid = connections.get(sid, None)
    game = games.get(uid, None)

    if game is not None:
        game.sleep_callback(uid, seconds_remaining=data)


# UNITY WEBSOCKET API ENDPOINTS
@sio.on('action')
@exception
def action(sid, data):
    
    """action(action_info-> as json)
    The unity game sends this function each time it performs an action, which
    could be setting a waypoint, or clicking any of the two to four action
    buttons (go, clear waypoints, pickup object, put down object) Feed this
    JSON back into action() (sent from flask to unity) to make the unity game
    perform this action.  You can also feed just the prior state into load() to
    reset the scene back to how it was before the action was taken.
    """
    data['arguments']['alreadyPlayed'] = True if data['arguments']['alreadyPlayed'] == 'True' else False
    uid = connections.get(sid, None)
    game = games.get(uid, None)

    if game is not None:
        # print("size of action object before: " + str(sys.getsizeof(data)))
        # data["prior state"] = None
        # print("size of action object after: " + str(sys.getsizeof(data)))
        game.event(uid, event_type='action', event_data=data)


@sio.on('initialState')
@exception
def initialState(sid, data):
    """
    initialState(serialized_state-> as json)
    The initial state of the unity game. Called when the unity game first
    connects and each time it reconnects after it resets from the reset button.
    Gives the game state that can be fed into load() to make the game state be
    how it is initially
    """
    uid = connections.get(sid, None)
    game = games.get(uid, None)

    if game is not None:
        if game.student == uid:
            # game.event(uid, event_type='set_initial_state', event_data=data)
            # game.initial_state = data
            # sio.emit('load', game.initial_state, room=game.teacher)
            game.event(uid, event_type='initial_state', event_data=data)


@sio.on('endedAction')
@exception
def endedAction(sid):
    """
    initialState(serialized_state-> as json)
    The initial state of the unity game. Called when the unity game first connects and each time 
    it reconnects after it resets from the reset button. Gives the game state that can be fed into load() 
    to make the game state be how it is initially
    """
    uid = connections.get(sid, None)
    game = games.get(uid, None)
    print("ended action called")

    if game is not None:
        if game.student == uid:
        #game.event(uid, event_type='set_initial_state', event_data=data)
            #game.initial_state = data
            #sio.emit('load', game.initial_state, room=game.teacher)
            game.ended_action(uid)



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

    new_game_commands = {"demonstrate": pattern.HtmlUnityDemonstrate,
                         "apprentice": pattern.HtmlUnityApprentice,
                         "reward": pattern.HtmlUnityReward }

    if data['message'] in new_game_commands.keys():
        if game is not None:   
            new_game = new_game_commands[data['message']](game.sio, game.teacher, game.student)
            games[game.teacher] = new_game
            games[game.student] = new_game
            return
    
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
    new_game = pattern.HtmlUnityTest(sio=sio, user=uid)
    sio.emit("sendTrainingMessage", "* Entering sandbox mode.", room=uid)
    games[uid] = new_game
    arg = {"role" : games[uid].role_string(uid), "pattern" : new_game.__class__.__name__}
    sio.emit("instructions", arg, room=uid)
        

### MODALITY LOGIC ### 
def register_user(uid):
    #todo: validate user (how?)

    if uid not in queue:
        queue.append(uid)

    if len(queue) > 1 and uid not in games:
       
        a = queue.pop(0)
        b = queue.pop(0)

        # randomly assign role
        if random.random() > .5:
            a, b = b, a

        #todo: randomly assing pattern type here
        print("new game created between: " + str(a) + ' and ' + str(b))
        if "demo" in a or "demo" in b:
            new_game = pattern.HtmlUnityDemonstrate(sio=sio, teacher=a, student=b)
        else:
            new_game = pattern.HtmlUnityApprentice(sio=sio, teacher=a, student=b)

        for user in [a, b]:
            games[user] = new_game
            sio.emit("sendTrainingMessage", "* You've been matched as "+ games[user].role_string(user) + ".", room=user)
            arg = {"role" : games[user].role_string(user), "pattern" : new_game.__class__.__name__}
            sio.emit("instructions", arg, room=user)

    else:
        sio.emit("sendTrainingMessage", "* Waiting for a partner.", room=uid)

    # new_user = User.query.filter(User.user_id==uid).first()
    #waiting = User.query.filter(User.task==None).order_by(User.last_active.desc()).first()
    #new_user = User(uid, ip='127.0.0.1')
    #db_session.commit()
  
if __name__=="__main__":
    app = Flask(__name__)
    app.register_blueprint(custom_code)
    app.wsgi_app = socketio.Middleware(sio, app.wsgi_app)
    app.run(host='localhost', port=5000)