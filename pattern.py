import socketio
import util
from functools import partial

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
        
        self.unity_lock = {teacher : True, student : True}
        self.html_lock = {teacher : True, student : True}
        self.training_buttons = {}
        
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
        self.sio.emit("reset", self.student)
        self.sio.emit("reset", self.teacher)
        

    def partner(self, actor):
        if actor==self.student:
            return self.teacher
        if actor==self.teacher:
            return self.student
        assert False
        
    def role_string(self, actor):
        if self.student == self.teacher:
            return "single player"
        if actor==self.student:
            return "student"
        if actor==self.teacher:
            return "teacher"
        assert False

    def chat(self, actor, message):
        #todo: remove these
        if message=="refresh":
            self.emit("load", self.current_state, room=self.teacher)
            self.emit("load", self.current_state, room=self.student)

        if message=="new":
            self.new_task()

        self.emit('sendTrainingMessage', 'YOU: '+ message, room=actor)
        self.emit('sendTrainingMessage', 
            self.role_string(self.partner(actor)) + ': ' + message, 
            room=self.partner(actor))

    def reconnect(self, actor):
        self.emit('load', self.current_state, room=actor)
        self.update_ui(actor)
        print('attempting to reconnect ' + self.role_string(actor))
        self.emit('sendTrainingMessage', "SYSTEM: Reconnected as "+self.role_string(actor), room=actor)

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
        if self.unity_lock[uid]:
            self.emit('lock', room=uid)
        else:
            self.emit('unlock', room=uid)

        if self.html_lock[uid]:
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

    # can be overwritten
    def initial_state(self, actor, state):
        if self.initial_state is None:
            # first initial state submitted is chosen 
            self.initial_state = state
            self.current_state = state
            self.state_stack=[state]
            self.unity_lock[self.student] = False
            print("getting initial state from " + self.role_string(actor))
            self.emit('load', self.current_state, room=self.partner(actor))
            #todo log state for training
        else:
            print("sending initial state to " + self.role_string(actor))
            self.emit('load', self.current_state, room=actor)
        self.update_ui(actor)
            
    def new_task(self):
        self.current_task += 1
        self.initial_state = None
        self.current_state = None
        if self.current_task >= self.num_teaching_tasks + self.num_testing_tasks:
            self.emit("complete_hit", "args", room=self.student)
            self.stale = True
            self.finished[self.student] = True
            # todo: cleanup game here

        if self.current_task >= self.num_teaching_tasks:
            self.emit("reset", room=self.student)
            if self.current_task == self.num_teaching_tasks:
                self.emit("complete_hit", "args", room=self.teacher)
                self.finished[self.teacher] = True
                self.emit("sendTrainingMessage", "SYSTEM: Done with the training phase of the experiment. Now you will be tested on your knowledge. Complete the tasks as before, but you will receive no feedback or assistance.", room=self.student)
                self.test_mode(self.student)
            else:
                self.emit("sendTrainingMessage", "SYSTEM: Starting a new testing task. ", room=self.student)

        else:
            self.emit("reset", room=self.teacher)
            self.emit("reset", room=self.student)
            self.emit("sendTrainingMessage", "SYSTEM: Starting a new teaching task.", room=self.teacher)
            self.emit("sendTrainingMessage", "SYSTEM: Starting a new teaching task.", room=self.student)
        #todo: save prior game and state to list of tasks in this game

    def test_mode(self, user):
        self.event_dict['action'] = HtmlUnityTest.action.__func__
        self.event_dict['button'] = HtmlUnityTest.button.__func__

        #self.button = partial(HtmlUnityTest.initial_state, self)
        
        self.unity_lock[user] = False
        self.html_lock[user] = False
        self.training_buttons[user] = [{"identifier":"finish","buttonText":"finished"}, {"identifier":"undo","buttonText":"undo"}]
        self.update_ui(user)

   
class HtmlUnityTest(HtmlUnity):
    def __init__(self, sio, user):
        super(HtmlUnityTest, self).__init__(sio=sio, teacher=user, student=user, num_teaching_tasks=1, num_testing_tasks=1)
        self.init()

    def init(self):
        self.unity_lock = {user : False}
        self.html_lock = {user : False}
        self.training_buttons[user] = [{"identifier":"finish","buttonText":"finished"}, {"identifier":"undo","buttonText":"undo"}]
        # {"identifier":"instructions","buttonText":"instructions"}, 
        self.update_ui(user)


    def action(self, actor, action):
        print("test action")
        self.training_buttons[actor] = [{"identifier":"finish","buttonText":"finished"}, {"identifier":"undo","buttonText":"undo"}]
        if actor==self.student:
            self.state_stack.append(action['prior state'])
            #self.emit('sendTrainingMessage', "SYSTEM: You performed action " + str(action['info']['function']), room=actor)
        self.update_ui(actor)

    def button(self, actor, button_id):
        print("test button")
        if actor==self.student:
            #self.emit('sendTrainingMessage', "SYSTEM: You clicked button labeled " + str(button_id), room=actor)
            if button_id == "undo":
                if len(self.state_stack) > 0:
                    self.sio.emit("load", self.state_stack.pop(), room=actor)
            
            if button_id == "instructions":
                self.sio.emit("instructions", "student", room=actor)
            if button_id == "finish":
                self.new_task()
                #self.sio.emit("complete_hit", None, room=actor)
                #self.stale = True


    # def initial_state(self, actor, state):
    #     if actor==self.student:
    #         pass #todo: log state for testing

class HtmlUnityReward(HtmlUnity):
    def __init__(self, sio, teacher, student):
        super(HtmlUnityReward, self).__init__(sio=sio, teacher=teacher, student=student)
        self.unity_lock[self.student] = False
        self.html_lock[self.student] = False
        self.training_buttons[self.student] = [{"identifier":"finish:request","buttonText":"finished"}]
        self.update_ui(self.student)

    def action(self, actor, action):
        if actor==self.teacher:
            assert False

        if actor==self.student:
            # if action['info']['function'] == go:
            #     question_str = "Is the students planned path "
            # else:
            question_str = "Is the students last action good?"
            self.emit('action', action, room=self.teacher)

            if self.prev_state is None:
                self.prev_state = action['prior state']

            if action['info']['function'] == 'reset000':
                pass
            elif action['info']['function'] == 'set_waypoint000':
                pass
            else:
                self.emit('sendTrainingMessage', "SYSTEM: " + question_str, room=self.teacher)
                #self.prev_state = action['prior state']
                #self.control = self.teacher
                self.training_buttons[self.teacher] = [{"identifier":"action:yes","buttonText":"yes"}, 
                        {"identifier":"action:no","buttonText":"no"}]
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
                self.emit('sendTrainingMessage', "SYSTEM: The student believes they are finished, allow progress to the next task?", room=self.teacher)
                self.training_buttons[self.teacher] = [{"identifier":"finish:yes","buttonText":"yes"}, 
                        {"identifier":"finish:no","buttonText":"no"}]
                self.training_buttons[self.student] = []
                

        if actor==self.teacher:
            self.control = self.student
            self.unity_lock[self.student] = False
            self.html_lock[self.teacher] = True
            self.html_lock[self.student] = False

            if button_id == "finish:yes":
                self.new_task()

            if button_id == "finish:no":
                self.emit('sendTrainingMessage', r"SYSTEM: The teacher does not think you're finished, try to figure out what you've forgotten.", room=self.student)
                self.emit('load', self.prev_state, room=self.student)
                self.emit('load', self.prev_state, room=self.teacher)

            if button_id == "action:yes":
                self.emit('sendTrainingMessage', 'SYSTEM: The teacher allowed your action.', room=self.student)
                
            if button_id == "action:no": 
                self.emit('load', self.prev_state, room=self.student)
                self.emit('load', self.prev_state, room=self.teacher)
                self.emit('sendTrainingMessage', 'SYSTEM: The teacher disallowed your action. Try again.', room=self.student)

            self.prev_state = None
            self.training_buttons[self.teacher] = []
            self.training_buttons[self.student] = [{"identifier":"finish:request","buttonText":"finished"}]

        self.update_ui(self.teacher)
        self.update_ui(self.student)
        

def HtmlUnityDemonstrate(HtmlUnity):
    def __init__(self, sio, teacher, student):
        super(HtmlUnityDemonstrate, self).__init__(sio=sio, teacher=teacher, student=student)
        self.training_buttons[self.teacher] = [{"identifier":"finish:request","buttonText":"finished"}, {"identifier":"undo","buttonText":"undo"}]
        self.unity_lock[self.teacher] = False
        self.html_lock[self.teacher] = False
        
    def action(self, actor, action):
        if actor==self.student:
            assert False

        if actor==self.teacher:
            self.emit('action', action, room=self.student)
            self.state_stack.append(action['prior state'])
    
    def button(self, actor, action):
        if actor==self.teacher:
            if button_id == "finish:request":
                self.new_task()
        
            if button_id == "undo":
                self.state_stack.pop()
                self.emit('load', self.state_stack[-1], room=self.student)
                self.emit('load', self.state_stack[-1], room=self.teacher)

        self.update_ui(self.teacher)
        self.update_ui(self.student)

def HtmlUnityApprentice(HtmlUnity):
    def action(self, actor, action):
        pass

    def button(self, actor, action):
        pass





        

    


