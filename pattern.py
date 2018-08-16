import socketio
import util
import pickle
import traceback
import os

import button_menu

import trollius
from trollius import From, Return

class Modality(object):
    pass

class HtmlUnity(Modality):
    def __init__(self, sio, teacher, student, num_teaching_tasks=2, num_testing_tasks=2):
        #assert isinstance(pattern, LearningPattern)
        assert type(teacher) == unicode
        assert type(student) == unicode
        assert type(sio) == socketio.Server

        #self.pattern = pattern
        self.sio = sio
        self.teacher = teacher
        self.student = student
    
        self.event_dict = {
                            'button': self.__class__.button, 
                            'action': self.__class__.action, 
                            'chat': self.__class__.chat,
                            'initial_state' : self.__class__.initial_state
                        }

        self.action_descriptions = {
                            'go': "move along current waypoints",
                            'set_waypoint': "set a waypoint",
                            'reset': "reset currenty waypoints"
        }
        
        self.unity_lock = {teacher : True, student : True}
        self.html_lock = {teacher : True, student : True}
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
        self.current_task = 0
        self.requesting_finish = False
        self.stale = False
        self.last_action = None
        #self.sio.emit("reset", room=self.teacher)
        #self.sio.emit("reset", room=self.student)
        print("setting floor plan to " + str(self.student))
        
        self.sio.emit("setFloorPlan", {"width" : 6, "height" : 4, "numOfObjects" : 3, "numOfIslands":4, "seed":1000}, room=self.teacher)#room=self.student)
        self.sio.emit("setFloorPlan", {"width" : 6, "height" : 4, "numOfObjects" : 3, "numOfIslands":4, "seed":1000}, room=self.student)#oom=self.teacher)

        #self.sio.emit("reset", self.teacher)
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

    def chat(self, actor, message):
        def stage_file(name):
            return os.path.join(os.path.dirname(os.path.realpath(__file__)), "static", "stages", str(name) +  ".p")
        
        if message[:4]=="load":
            try:
                s = message.split()
                path = stage_file(s[1])
                f = pickle.load(open(path, 'rb'))
                self.current_state = f
                self.initial_state = f
                self.prev_state = None
                self.state_stack = []
                self.emit("load", self.current_state, room=self.teacher)
                self.emit('sendTrainingMessage', "* stage loaded from: " + path, room=self.teacher)

                if self.student!=self.teacher:
                    self.emit("load", self.current_state, room=self.student)
                    self.emit('sendTrainingMessage', "* stage loaded from: " + path, room=self.student)
            except:
                print("error loading state:")
                traceback.print_exc()
            return

        if message[:4]=="save":
            try:
                s = message.split()
                path = stage_file(s[1])
                pickle.dump(self.current_state, open(path, 'wb+'))
                self.emit('sendTrainingMessage', "* stage saved to: " + path, room=actor)
            except:
                print("error saving state:")
                traceback.print_exc()
            return

        if message=="refresh":
            self.emit("load", self.current_state, room=self.teacher)
            self.emit("load", self.current_state, room=self.student)
            return

        if message=="new":
            self.new_task()
            return

        self.emit('sendTrainingMessage', 'YOU: '+ message, room=actor)
        self.emit('sendTrainingMessage', 
            self.role_string(actor) + ': ' + message, 
            room=self.partner(actor))

    def reconnect(self, actor):
        self.emit('load', self.current_state, room=actor)
        self.update_ui(actor)
        print('attempting to reconnect ' + self.role_string(actor))
        #self.emit('sendTrainingMessage', "* Reconnected as "+self.role_string(actor) + " in " + self.__class__.__name__, room=actor)

    def event(self, actor, event_type, event_data):
        print(str(self.event_dict[event_type]))
        self.event_dict[event_type](self, actor, event_data)
        #print("event: " + event_type + ", received by: " + self.role_string(actor))
        # todo: log events here
        self.update_ui(self.teacher)
        self.update_ui(self.student)

    def emit(self, topic, argument=None, room=None):
        #if topic not in self.emissions[room]:
            #self.emissions[room][topic] = []

        #print("emit: " + topic + ", to: " + str(self.role_string(room)))

        #todo: log emissions here
        #self.emissions[room][topic].append(argument)
        self.sio.emit(topic, argument, room=room)

    def update_ui(self, uid):
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

    # event mappings that must be implemented on a pattern-basis
    def action(self, actor, action):
        raise NotImplementedError

    def button(self, actor, action):
        raise NotImplementedError

    def ended_action(self, actor):
        self.waiting = False
        self.update_ui(self.teacher)
        self.update_ui(self.student)

    # can be overwritten
    def initial_state(self, actor, state):
        
        if self.initial_state is None:
            # first initial state submitted is chosen 
            self.initial_state = state
            self.current_state = state
            self.state_stack=[state]
            print("getting initial state from " + self.role_string(actor))
            self.emit('load', self.current_state, room=self.partner(actor))
            #todo log state for training
        else:
            print("sending initial state to " + self.role_string(actor))
            self.emit('load', self.current_state, room=actor)
        self.update_ui(actor)
        
    def sleep_callback(self, player, seconds_remaining=3):
        if seconds_remaining == 0:
            self.waiting=False
            self.emit("reset", player)
        else:
            self.emit("sendTrainingMessage", "* " + str(seconds_remaining) + "..", room=player)
            self.emit("sleep_callback", seconds_remaining-1, room=player)


    def new_task(self):
        
        self.current_task += 1
        self.initial_state = None
        self.current_state = None
        players = []
        
        if self.current_task >= self.num_teaching_tasks + self.num_testing_tasks:
            
            self.emit("complete_hit", "args", room=self.student)
            self.stale = True
            self.finished[self.student] = True
            # todo: cleanup game here
        else:
            players.append(self.student)

        if self.current_task >= self.num_teaching_tasks:
            if self.current_task == self.num_teaching_tasks:
                
                self.emit("complete_hit", "args", room=self.teacher)
                self.finished[self.teacher] = True
                self.test_mode(self.student)

        else:
            players.append(self.teacher)

        self.waiting = True

        print(players)
        if len(players) == 1:
                self.emit("sendTrainingMessage", "* Done with the training phase of the experiment. Now you will be tested on your knowledge. Complete the tasks as before, but you will receive no feedback or assistance. ", room=players[0])
     
        for player in players:
            self.emit("new_task", "testing" if len(players)==1 else "training", room=player)
            self.emit("sendTrainingMessage", "* Current task has been marked complete. Starting a new task in", room=player)            
            self.emit("sleep_callback", 3, room=player)
        
            

    def test_mode(self, user):
        self.event_dict['action'] = HtmlUnityTest.action.__func__
        self.event_dict['button'] = HtmlUnityTest.button.__func__
        
        self.unity_lock[user] = False
        self.html_lock[user] = False
        self.training_buttons[user] = button_menu.test
        self.update_ui(user)

   
class HtmlUnityTest(HtmlUnity):
    def __init__(self, sio, user):
        super(HtmlUnityTest, self).__init__(sio=sio, teacher=user, student=user, num_teaching_tasks=1, num_testing_tasks=1)
        self.init(user)

    def init(self, user):
        self.unity_lock = {user : False}
        self.html_lock = {user : False}
        self.training_buttons[user] = button_menu.test
        # {"identifier":"instructions","buttonText":"instructions"}, 
        self.update_ui(user)


    def action(self, actor, action):
        self.training_buttons[actor] = button_menu.test
        if actor==self.student:
            self.state_stack.append(action['prior state'])
        self.update_ui(actor)

    def button(self, actor, button_id):
        if actor==self.student:
            if button_id == "undo":
                if len(self.state_stack) > 0:
                    self.sio.emit("load", self.state_stack.pop(), room=actor)
            
            if button_id == "instructions":
                self.sio.emit("instructions", "student", room=actor)
            if button_id == "finish":
                self.new_task()
              
class HtmlUnityReward(HtmlUnity):
    def __init__(self, sio, teacher, student):
        super(HtmlUnityReward, self).__init__(sio=sio, teacher=teacher, student=student)
        self.unity_lock[self.student] = False
        self.html_lock[self.student] = False
        self.training_buttons[self.student] = button_menu.reward_student
        self.update_ui(self.student)

    def action(self, actor, action):
        self.last_action = action

        if actor==self.teacher:
            assert False

        if actor==self.student:
            
            question_str = "The student wants to " + self.action_descriptions.get(action['info']['function'], 'DESCRIPTION NOT FOUND') + ", allow it?"
            if action['arguments']['alreadyPlayed']:
                self.emit('action', action, room=self.teacher)
            
            if self.prev_state is None:
                self.prev_state = action['prior state']

            self.emit('sendTrainingMessage', "* " + question_str, room=self.teacher)
            
            self.training_buttons[self.teacher] = button_menu.reward_teacher
            self.training_buttons[self.student] = []
            self.unity_lock[self.student] = True
            self.html_lock[self.student] = True
            self.html_lock[self.teacher] = False

            self.update_ui(self.teacher)
            self.update_ui(self.student)

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

            self.prev_state = None
            self.training_buttons[self.teacher] = []
            self.training_buttons[self.student] = button_menu.reward_student

        self.update_ui(self.teacher)
        self.update_ui(self.student)
        

class HtmlUnityDemonstrate(HtmlUnity):
    def __init__(self, sio, teacher, student):
        super(HtmlUnityDemonstrate, self).__init__(sio=sio, teacher=teacher, student=student)
        self.training_buttons[self.teacher] = button_menu.demonstrate_teacher
        self.unity_lock[self.teacher] = False
        self.html_lock[self.teacher] = False
        self.html_lock[self.student] = True
        self.unity_lock[self.student] = True
        
    def action(self, actor, action):
        if actor==self.student:
            assert False

        if actor==self.teacher:
            self.emit('action', action, room=self.student)
            self.state_stack.append(action['prior state'])
    
    def button(self, actor, button_id):
        if actor==self.teacher:
            if button_id == "finish":
                self.new_task()
        
            if button_id == "undo":
                self.state_stack.pop()
                self.emit('load', self.state_stack[-1], room=self.student)
                self.emit('load', self.state_stack[-1], room=self.teacher)

        self.update_ui(self.teacher)
        self.update_ui(self.student)

class HtmlUnityApprentice(HtmlUnity):
    def __init__(self, sio, teacher, student):
        super(HtmlUnityApprentice, self).__init__(sio=sio, teacher=teacher, student=student)
        self.training_buttons[self.student] = button_menu.apprentice_student
        self.unity_lock[self.student] = False
        self.html_lock[self.student] = False
        self.update_ui(self.teacher)
        self.update_ui(self.student)
        self.demonstrate=False

    def action(self, actor, action):
        if actor==self.teacher:
            if self.demonstrate:
                self.emit('action', action, room=self.student)
                if self.prev_state is None:
                    self.prev_state = action['prior state']
                self.demonstrate=False

                self.training_buttons[self.student] = button_menu.apprentice_student

                self.unity_lock[self.teacher] = True
                self.html_lock[self.teacher] = False
                self.unity_lock[self.student] = False
                self.html_lock[self.student] = False
                self.update_ui(self.teacher)
                self.update_ui(self.student)

        if actor==self.student:
            self.last_action = action
            question_str = "The student wants to " + self.action_descriptions.get(action['info']['function'], 'DESCRIPTION NOT FOUND') + ", allow it?"
            if action['arguments']['alreadyPlayed']:
                print(str(action['info']['function']) + " " + str(action['arguments']))
                self.emit('sendTrainingMessage', "PLAYING ACTION" + action['info']['function'], room=self.teacher)
                self.emit('action', action, room=self.teacher)

            if self.prev_state is None:
                self.prev_state = action['prior state']


            self.emit('sendTrainingMessage', "* " + question_str, room=self.teacher)
           
            self.training_buttons[self.teacher] = button_menu.apprentice_teacher
            self.training_buttons[self.student] = []
            self.unity_lock[self.student] = True
            self.html_lock[self.student] = True
            self.html_lock[self.teacher] = False

            self.update_ui(self.teacher)
            self.update_ui(self.student)

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

            self.prev_state = None
            self.training_buttons[self.teacher] = []
            self.training_buttons[self.student] = button_menu.apprentice_student

        self.update_ui(self.teacher)
        self.update_ui(self.student)


if __name__ == "__main__":
    HtmlUnityReward(sio="sio", teacher="teacher", student="student")
    #HtmlUnityDemonstrate(sio="sio", teacher="teacher", student="student")



        

    


