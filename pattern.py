import socketio
import util
import pickle
import traceback
import os
import time
import json

import button_menu

from psiturk.db import db_session, init_db
from custom_models import Session, Task, Emission, User

class Modality(object):
    pass

class HtmlUnity(Modality):
    def __init__(self, sio, teacher, student, num_teaching_tasks=2, num_testing_tasks=2):

        #self.pattern = pattern
        self.sio = sio
        self.teacher = teacher
        self.student = student

        new_session = Session(pattern=self.__class__.__name__)
        db_session.add(new_session)
        db_session.commit()
        print("inserting session with pattern + " +  new_session.pattern + " and id: " + str(new_session.session_id))
        self.session_id = new_session.session_id
        #self.session = db_session.query(Session).filter(Session.session_id==new_session.session_id).one()
        

        self.current_task_id = None
    
        self.event_dict = {
                            'button': self.__class__.button, 
                            'action': self.__class__.action, 
                            'chat': self.__class__.chat,
                            'initial_state' : self.__class__.initial_state,
                            'game_state' : self.__class__.game_state
                        }

        self.good_levels = []

        self.action_descriptions = {
                            'go': "move along current waypoints",
                            'set_waypoint': "move to point",
                            'extraAction' : "pick up or put down object",

                            'reset': "reset current waypoints"
        }
        
        self.unity_lock = {teacher : True, student : True}
        self.html_lock = {teacher : True, student : True}
        self.init_unity_lock = {teacher : True, student : False}
        self.init_html_lock = {teacher : True, student : False}

        self.training_buttons = {teacher : [], student : []}
        self.read_instructions = {teacher : False, student : False}
        self.emissions = {teacher : {}, student : {}}
        self.finished = {teacher : False, student : False}
        self.initial_state = None
        self.current_state = None
        self.prev_state = None
        self.state_stack = []
        self.actions = []
        self.num_teaching_tasks = num_teaching_tasks
        self.num_testing_tasks = num_testing_tasks
        self.current_task = -1
        self.requesting_finish = False
        self.stale = False
        self.last_action = None
        
        #print("setting floor plan to " + str(self.student))
        
        #self.emit("setFloorPlan", {"width" : 6, "height" : 4, "numOfObjects" : 3, "numOfIslands":4, "seed":1000}, room=self.teacher)#room=self.student)
        #self.emit("setFloorPlan", {"width" : 6, "height" : 4, "numOfObjects" : 3, "numOfIslands":4, "seed":1000}, room=self.student)#oom=self.teacher)
        self.waiting = False
        

    def partner(self, actor):
        if actor==self.student:
            return self.teacher
        if actor==self.teacher:
            return self.student
        assert False
        
    def role_string(self, actor):
        if self.student == self.teacher:
            return "sandbox"
        if actor==self.student:
            return "student"
        if actor==self.teacher:
            return "teacher"
        assert False

    #blocks
    def playback(self, task_id, room, use_student=True, fast=False):
        task = db_session.query(Task).filter(Task.task_id==task_id).one()
        user_room = task.student if use_student else task.teacher
        prev_time = task.timestamp

        for emission in task.emissions:
            if user_room in emission.room: # == user_room or emission.room == 'playback'+user_room:
                if emission.topic == 'action' or emission.topic == 'load' or emission.topic == 'sendTrainingMessage':

                    dt = (emission.timestamp - prev_time).total_seconds()
                    prev_time = emission.timestamp

                    if fast:
                        time.sleep(.25)
                    else:
                        time.sleep(dt)

                    data = json.loads(emission.data)
 
                    print("playback " + emission.topic + " @t " + str(prev_time))
                    self.sio.emit(emission.topic, data, room=room)

        #time.sleep(1)
        #self.sio.emit('load', json.loads(task.final_state), room=room)

    def chat(self, actor, message):
        def stage_file(name):
            return os.path.join(os.path.dirname(os.path.realpath(__file__)), "static", "stages", str(name) +  ".p")

        if message[:4]=="emit":
            try:
                s = message.split()
                self.emit(s[1], None, room=actor)
            except:
                print("error loading state:")
                traceback.print_exc()
            return

        if message[:8]=="playback":
            try:
                s = message.split()
                task_id = s[1]
                self.playback(task_id=task_id, room=actor)
            except:
                print("error playing back task " + str(task_id))
                traceback.print_exc()
            return

        if message[:4]=="load":
            try:
                s = message.split()
                path = stage_file(s[1])

                f = pickle.load(open(path, 'rb'))
                self.current_state = f
                self.initial_state = f
                self.prev_state = f
                self.state_stack = []
                self.emit("load", self.current_state, room=self.teacher)
                self.emit('sendTrainingMessage', "* stage loaded from: " + path, room=self.teacher)

                if self.student!=self.teacher:
                    self.emit("load", self.current_state, room=self.student)
                    self.emit('sendTrainingMessage', "* stage loaded from: " + path, room=self.student)
            except:
                print("error loading state from: " + path + " // ")
                traceback.print_exc()
            return

        if message[:4]=="save":
            try:
                s = message.split()
                path = stage_file(s[1])
                init_path = stage_file(s[1]+"_init")

                pickle.dump(self.current_state, open(path, 'wb+'))
                pickle.dump(self.initial_state, open(init_path, 'wb+'))
                self.emit('sendTrainingMessage', "* stage saved to: " + path, room=actor)
            except:
                print("error saving state:")
                traceback.print_exc()
            return

        if message=="refresh":
            if self.current_state is not None:
                self.emit("load", self.current_state, room=actor)
            self.update_ui(actor)
            return

        if message=="new":
            self.new_task()
            return

        self.emit('sendTrainingMessage', 'YOU: '+ message, room=actor)
        self.emit('sendTrainingMessage', 
            self.role_string(actor) + ': ' + message, 
            room=self.partner(actor))

    def reconnect(self, actor):
        print('attempting to reconnect ' + self.role_string(actor))


        if self.current_state is not None:
            self.emit('load', self.current_state, room=actor)

        self.waiting = False
        self.update_ui(actor)
            
        #self.emit('sendTrainingMessage', "* Reconnected as "+self.role_string(actor) + " in " + self.__class__.__name__, room=actor)

    def event(self, actor, event_type, event_data):
        if event_type=='action':
            pass
            #print("action: " + str(event_data['info']))


        self.event_dict[event_type](self, actor, event_data)
       

        self.update_ui()

    def emit(self, topic, argument=None, room=None):
        #log emissions to current task in database for future analysis/playback
        if topic == 'load':
            argument['waypoints'] = {}


        if self.current_task_id is not None and topic != "sleep_callback":
            try:
                argument_string = json.dumps(argument)

                record = Emission(topic, argument_string, room)
                
                task = db_session.query(Task).filter(Task.task_id==self.current_task_id).one()
                task.emissions.append(record)
                db_session.commit()
            except Exception as e:
                print("problem logging emission: " + str(topic) + ": " + str(e) + " on task " + str(self.current_task_id))

        if topic == 'action':
            argument['prior state'] = None


        if argument is None:
            self.sio.emit(topic, room=room)
        else:
            self.sio.emit(topic, argument, room=room)

    def update_ui(self, uid=None):
        if uid is None:
            for uid in self.finished.keys():
                if not self.finished[uid]:
                    self.update_ui(uid)
            return

        """ update the ui to reflect the current state of the game """
        if self.unity_lock[uid] or self.waiting:
            self.emit('lock', room=uid)
        else:
            self.emit('unlock', room=uid)

        if self.html_lock[uid] or self.waiting:
            self.emit('lockButtons', room=uid)
        else:
            self.emit('unlockButtons', room=uid)
        
        if uid in self.training_buttons:
            if self.training_buttons[uid] is not None:
                self.emit('getTrainingButtons', self.training_buttons[uid], room=uid)

    def action(self, actor, action):
        raise NotImplementedError

    def button(self, actor, action):
        raise NotImplementedError

    def ended_action(self, actor):
        self.waiting = False
        self.update_ui()

    def game_state(self, actor, state):
        if state is not None:
            if self.initial_state is None:
                self.initial_state(actor, state)
            else:
                pass
                #self.current_state = state

    # can be overwritten
    def initial_state(self, actor, state):
        """ handles an initial_state coming from an actor, or call with predefined level to """
        if self.initial_state is None:

            new_task = Task(init_state=state)
            session_record = db_session.query(Session).filter(Session.session_id==self.session_id).one()
            session_record.tasks.append(new_task)
            

            new_task.student = self.student #db_session.query(User).filter(User.user_id == self.student).one()
            new_task.teacher = self.teacher #db_session.query(User).filter(User.user_id == self.teacher).one()
            new_task.init_state = json.dumps(state)

            db_session.commit()
            print("task_id " + str(new_task.task_id))
            self.current_task_id = new_task.task_id
            
            # first initial state submitted is chosen 
            self.initial_state = state
            self.current_state = state
            self.prev_state = state
            self.state_stack=[state]
    
            self.emit('load', self.current_state, room=actor)
            self.emit('load', self.current_state, room=self.partner(actor))
        else:
            self.emit('load', self.current_state, room=actor)
        self.update_ui(actor)
        
    def sleep_callback(self, actor, seconds_remaining=3):
        """ terrible, terrible workaround for being able to sleep """ 
        if seconds_remaining == 0:
            if actor==self.student:
                self.initial_state = None
                self.waiting=False
                if len(self.good_levels) > 0:
                    self.initial_state(actor, random.choice(self.good_levels))
                else:
                    print("setting floor plan for " + str(actor))
                    self.emit("setFloorPlan", {"width" : 6, "height" : 4, "numOfObjects" : 3, "numOfIslands":4, "seed":1000}, room=actor)
                   
            self.update_ui(actor)
        else:
            if seconds_remaining==1:
                self.emit("reset", room=actor)
            self.emit("sendTrainingMessage", "* " + str(seconds_remaining) + "..", room=actor)
            self.emit("sleep_callback", seconds_remaining-1, room=actor)


    def new_task(self):

        if self.current_task_id is not None:
            prev_task = db_session.query(Task).filter(Task.task_id==self.current_task_id).one()
            prev_task.final_state = json.dumps(self.current_state)

        
        self.current_task += 1
        self.initial_state = None
        self.current_state = None
        actors = []
        
        if self.current_task >= self.num_teaching_tasks + self.num_testing_tasks:
            print("student finished")
            self.emit("complete_hit", "args", room=self.student)
            self.stale = True
            self.finished[self.student] = True
            # todo: cleanup game here
        else:
            actors.append(self.student)

        if self.current_task >= self.num_teaching_tasks:
            if self.current_task == self.num_teaching_tasks:
                self.emit("sendTrainingMessage", "* Done with the training phase of the experiment. Now you will be tested on your knowledge. Complete the tasks as before, but you will receive no feedback or assistance. ", room=self.student)
     
                print("teacher finished")
                self.emit("complete_hit", "args", room=self.teacher)
                self.finished[self.teacher] = True
                self.test_mode(self.student)

        else:
            actors.append(self.teacher)

        self.waiting = True
 
        self.html_lock = self.init_html_lock
        self.unity_lock = self.init_unity_lock

        actors = list(set(actors))

        for actor in actors:
            self.emit("new_task", "testing" if len(actors)==1 else "training", room=actor)
            if self.current_task_id is not None:
                self.emit("sendTrainingMessage", "* Current task has been marked complete. Starting a new task in:", room=actor)            
                self.emit("sleep_callback", 3, room=actor)
            else:
                self.emit("sendTrainingMessage", "* Starting your first task.", room=actor)            
                self.emit("sleep_callback", 0, room=actor)
            self.update_ui(actor)

    def test_mode(self, user):
        self.event_dict['action'] = HtmlUnityTest.action.__func__
        self.event_dict['button'] = HtmlUnityTest.button.__func__
    
        self.init_unity_lock = {user : False}
        self.init_html_lock = {user : False}

        self.training_buttons[user] = button_menu.test
        self.update_ui(user)

   
class HtmlUnityTest(HtmlUnity):
    def __init__(self, sio, user, tasks=2):
        super(HtmlUnityTest, self).__init__(sio=sio, teacher=user, student=user, num_teaching_tasks=tasks-1, num_testing_tasks=1)
        self.init(user)

    def init(self, user):
        self.unity_lock = {user : False}
        self.html_lock = {user : False}
        self.training_buttons[user] = button_menu.test
        # {"identifier":"instructions","buttonText":"instructions"}, 
        self.update_ui(user)


    def action(self, actor, action):
        self.training_buttons[actor] = button_menu.test

        if action['info']['function'] == 'set_waypoint':
            self.emit("action", action, room='playback'+actor)
            action['info']['function'] = 'go'
            action['arguments']['alreadyPlayed'] = False

        if not action['arguments']['alreadyPlayed']:
            self.emit("action", action, room=actor)

        #self.training_buttons[actor] = button_menu.test

        if actor==self.student:

            self.state_stack.append(action['prior state'])
            
        self.update_ui(actor)

    def button(self, actor, button_id):
        if actor==self.student:
            if button_id == "undo":
                if len(self.state_stack) > 0:
                    self.emit("load", self.state_stack.pop(), room=actor)
            
            if button_id == "instructions":
                self.emit("instructions", "student", room=actor)
            if button_id == "finish":
                self.new_task()
              
class HtmlUnityReward(HtmlUnity):
    def __init__(self, sio, teacher, student):
        super(HtmlUnityReward, self).__init__(sio=sio, teacher=teacher, student=student)
        self.unity_lock[self.student] = False
        self.html_lock[self.student] = False
        self.training_buttons[self.student] = button_menu.reward_student
        self.update_ui()

    def action(self, actor, action):
        self.last_action = action

        if actor==self.teacher:
            assert False

        if actor==self.student:
            
            question_str = "The student wants to " + self.action_descriptions.get(action['info']['function'], 'DESCRIPTION NOT FOUND') + ", allow it?"
            if action['arguments']['alreadyPlayed']:
                self.emit('action', action, room=self.teacher)
            
            #if self.prev_state is None:
                
            #self.prev_state = action['prior state']

            self.emit('sendTrainingMessage', "* " + question_str, room=self.teacher)
            
            self.training_buttons[self.teacher] = button_menu.reward_teacher
            self.training_buttons[self.student] = []
            self.unity_lock[self.student] = True
            self.html_lock[self.student] = True
            self.html_lock[self.teacher] = False

            self.update_ui()
 
    def button(self, actor, button_id):
        if actor==self.student:
            if button_id == "finish:request":
                self.unity_lock[self.student] = True
                self.html_lock[self.teacher] = False
                self.html_lock[self.student] = True
                self.emit('sendTrainingMessage', "* The student believes they are finished, allow progress to the next task?", room=self.teacher)
                self.training_buttons[self.teacher] = button_menu.confirm_finished
                self.training_buttons[self.student] = []
                

        if actor==self.teacher:
            self.control = self.student
            self.unity_lock[self.student] = False
            self.html_lock[self.teacher] = True
            self.html_lock[self.student] = False

            if button_id == "finish:yes":
                self.new_task()

            if button_id == "finish:no":
                self.emit('sendTrainingMessage', r"* The teacher does not think you're finished, try to figure out what you've forgotten.", room=self.student)
                self.emit('load', self.prev_state, room=self.student)
                self.emit('load', self.prev_state, room=self.teacher)

            if button_id == "action:yes":
                if self.last_action['info']['function'] == 'set_waypoint':
                        self.emit("action", self.last_action, room='playback'+actor)
                        self.last_action['arguments']['alreadyPlayed'] = False
                        self.last_action['info']['function'] = 'go'

                if not self.last_action['arguments']['alreadyPlayed']:
                    if self.last_action['info']['function'] == 'go':
                        self.waiting = True
                    
                    self.emit('action', self.last_action, room=self.teacher)
                    self.emit('action', self.last_action, room=self.student)
                    self.last_action['arguments']['alreadyPlayed'] = True
    
                self.emit('sendTrainingMessage', '* The teacher allowed your action.', room=self.student)
                
            if button_id == "action:no": 
                self.emit('load', self.prev_state, room=self.student)
                self.emit('load', self.prev_state, room=self.teacher)

                self.emit('sendTrainingMessage', '* The teacher disallowed your action. Try again.', room=self.student)

            #self.prev_state = None
            self.training_buttons[self.teacher] = []
            self.training_buttons[self.student] = button_menu.reward_student

        self.update_ui()
        

class HtmlUnityDemonstrate(HtmlUnity):
    def __init__(self, sio, teacher, student):
        super(HtmlUnityDemonstrate, self).__init__(sio=sio, teacher=teacher, student=student)
        self.training_buttons[self.teacher] = button_menu.demonstrate_teacher
    
        self.init_unity_lock = {teacher : False, student : True}
        self.init_html_lock = {teacher : False, student : True}
        self.update_ui(teacher)

        
    def action(self, actor, action):
        if actor==self.student:
            print("student shouldn't be able to take actions")

        if actor==self.teacher:
            if action['info']['function'] == 'set_waypoint':
                self.emit("action", action, room='playback'+actor)
                self.emit("action", action, room=self.student)
                action['arguments']['alreadyPlayed'] = False
                action['info']['function'] = 'go'

            if not action['arguments']['alreadyPlayed']:
                self.emit("action", action, room=actor)
                self.emit("action", action, room=self.student)

            self.emit('action', action, room=self.student)
            self.prev_state = action['prior state']
            #self.state_stack.append(action['prior state'])
    
    def button(self, actor, button_id):
        if actor==self.teacher:
            if button_id == "finish":
                self.new_task()
        
            if button_id == "undo":
                self.state_stack.pop()
                self.emit('load', self.state_stack[-1], room=self.student)
                self.emit('load', self.state_stack[-1], room=self.teacher)

        self.update_ui()

class HtmlUnityApprentice(HtmlUnity):
    def __init__(self, sio, teacher, student):
        super(HtmlUnityApprentice, self).__init__(sio=sio, teacher=teacher, student=student)
        self.training_buttons[self.student] = button_menu.apprentice_student
        
        self.update_ui()
        self.demonstrate=False

    def action(self, actor, action):
        if actor==self.teacher:
            if self.demonstrate:
                if action['info']['function'] == 'set_waypoint':
                    self.emit("action", action, room='playback'+actor)
                    self.emit("action", action, room=self.student)
                    action['arguments']['alreadyPlayed'] = False
                    action['info']['function'] = 'go'

                if not action['arguments']['alreadyPlayed']:
                    self.emit("action", action, room=actor)
                
                
                self.emit('action', action, room=self.student)
                #if self.prev_state is None:
                    
                #self.prev_state = action['prior state']

                self.demonstrate=False

                self.training_buttons[self.student] = button_menu.apprentice_student

                self.unity_lock[self.teacher] = True
                self.html_lock[self.teacher] = False
                self.unity_lock[self.student] = False
                self.html_lock[self.student] = False
                self.update_ui()

        if actor==self.student:
            self.last_action = action
            question_str = "The student wants to " + self.action_descriptions.get(action['info']['function'], 'DESCRIPTION NOT FOUND') + ", allow it?"

            if action['arguments']['alreadyPlayed']:
                #print(str(action['info']['function']) + " " + str(action['arguments']))
                #self.emit('sendTrainingMessage', "PLAYING ACTION" + action['info']['function'], room=self.teacher)
                self.emit('action', action, room=self.teacher)

            #if self.prev_state is None:
                
            #self.prev_state = action['prior state']


            self.emit('sendTrainingMessage', "* " + question_str, room=self.teacher)
           
            self.training_buttons[self.teacher] = button_menu.apprentice_teacher
            self.training_buttons[self.student] = []
            self.unity_lock[self.student] = True
            self.html_lock[self.student] = True
            self.html_lock[self.teacher] = False

            self.update_ui()

    def button(self, actor, button_id):
        if actor==self.student:
            if button_id == "finish:request":
                self.unity_lock[self.student] = True
                self.html_lock[self.teacher] = False
                self.html_lock[self.student] = True
                self.emit('sendTrainingMessage', "* The student believes they are finished, allow progress to the next task?", room=self.teacher)
                self.training_buttons[self.teacher] = button_menu.confirm_finished
                self.training_buttons[self.student] = []
            if button_id == "help:request":
                self.unity_lock[self.student] = True
                self.html_lock[self.student] = True
                self.emit('sendTrainingMessage', "* The student is unsure of what to do next, take a single move to give them a hint.", room=self.teacher)
                self.unity_lock[self.teacher] = False
                self.demonstrate = True
                self.training_buttons[self.student] = []
                self.training_buttons[self.teacher] = button_menu.demonstrate_teacher

        if actor==self.teacher:
            self.control = self.student
            self.unity_lock[self.student] = False
            self.html_lock[self.teacher] = True
            self.html_lock[self.student] = False

            if button_id == "finish":
                self.emit('sendTrainingMessage', r"* The teacher indicated you finished with the task", room=self.student)
                self.new_task()

            if button_id == "finish:yes":
                self.emit('sendTrainingMessage', r"* The teacher agreed that you are finished with the task", room=self.student)
                self.new_task()

            if button_id == "finish:no":
                self.emit('sendTrainingMessage', r"* The teacher does not think you're finished, try to figure out what you've forgotten.", room=self.student)
                self.emit('load', self.prev_state, room=self.student)
                self.emit('load', self.prev_state, room=self.teacher)

            if button_id == "action:yes":
                if self.last_action['info']['function'] == 'set_waypoint':
                    self.emit("action", self.last_action, room='playback'+actor)
                    self.last_action['arguments']['alreadyPlayed'] = False
                    self.last_action['info']['function'] = 'go'

                if not self.last_action['arguments']['alreadyPlayed']:
                    if self.last_action['info']['function'] == 'go':
                        self.waiting = True
                    self.emit('action', self.last_action, room=self.teacher)
                    self.emit('action', self.last_action, room=self.student)
                    self.last_action['arguments']['alreadyPlayed'] = True

                self.emit('sendTrainingMessage', '* The teacher allowed your action.', room=self.student)
                
            if button_id == "action:no": 
                self.emit('load', self.prev_state, room=self.student)
                self.emit('load', self.prev_state, room=self.teacher)
                self.emit('sendTrainingMessage', '* The teacher disallowed your action. Try again.', room=self.student)

            #self.prev_state = None
            self.training_buttons[self.teacher] = []
            self.training_buttons[self.student] = button_menu.apprentice_student

        self.update_ui()


if __name__ == "__main__":

    
    HtmlUnityReward(sio="sio", teacher="teacher", student="student")
    #HtmlUnityDemonstrate(sio="sio", teacher="teacher", student="student")



        

    


