import socketio
import util


class Modality(object):
    pass

class HtmlUnity(Modality):
    def __init__(self, sio, teacher, student):
        #assert isinstance(pattern, LearningPattern)
        assert type(teacher) == unicode
        assert type(student) == unicode
        assert type(sio) == socketio.Server

        #self.pattern = pattern
        self.sio = sio
        self.teacher = teacher
        self.student = student
    
        self.event_dict = {
                            'button': self.button, 
                            'action': self.action, 
                            'chat': self.chat,
                            'initial_state' : self.initial_state
                        }
        
        self.unity_lock = {teacher : True, student : True}
        self.html_lock = {teacher : True, student : True}
        self.training_buttons = {}
        self.emissions = {teacher : {}, student : {}}
        self.initial_state = None
        self.current_state = None
        self.actions = []

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
        self.event_dict[event_type](actor, event_data)
        print("event: " + event_type + ", received by: " + self.role_string(actor))
        # todo: log events here
        self.update_ui(self.teacher)
        self.update_ui(self.student)

    def emit(self, topic, argument=None, room=None):
        if topic not in self.emissions[room]:
            self.emissions[room][topic] = []

        print("emit: " + topic + ", to: " + str(self.role_string(room)))

        #todo: log emissions here
        self.emissions[room][topic].append(argument)
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
            #self.emit('load', self.current_state, room=self.student)
            self.emit('load', self.current_state, room=self.teacher)
            self.unity_lock[self.student] = False
            self.update_ui(self.teacher)
            self.update_ui(self.student)

class HtmlUnityTest(HtmlUnity):
    def __init__(self, sio, user):
        super(HtmlUnityTest, self).__init__(sio=sio, teacher=user, student=user)
        self.unity_lock = {user : False}
        self.html_lock = {user : False}
        self.training_buttons[user] = [{"identifier":"instructions","buttonText":"instructions"}, {"identifier":"finish","buttonText":"finish"}]
        self.update_ui(user)

    def action(self, actor, action):
        self.emit('sendTrainingMessage', "SYSTEM: You performed action " + str(action['info']['function']), room=actor)

    def button(self, actor, button_id):
        self.emit('sendTrainingMessage', "SYSTEM: You clicked button labeled " + str(button_id), room=actor)
        if button_id == "instructions":
            self.sio.emit("instructions", "student", room=actor)
        if button_id == "finish":
            self.sio.emit("complete_hit", "args", room=actor)

    def initial_state(self, actor, state):
        pass

class HtmlUnityReward(HtmlUnity):
    def action(self, actor, action):
        if actor==self.teacher:
            print("teachers should not be able to make actions")
            return

        if actor==self.student:
            self.emit('action', action, room=self.teacher)
            if self.prev_state is None:
                self.prev_state = action['prior state']
            if action['info']['function'] == 'set_waypoint':
                pass
            elif action['info']['function'] == 'reset':
                pass # simply allow the action
            else:
                self.emit('sendTrainingMessage', "SYSTEM: Is the students' action ok?", room=self.teacher)
                #self.prev_state = action['prior state']
                self.control = self.teacher
                self.training_buttons[self.teacher] = [{"identifier":"yes","buttonText":"yes"}, 
                        {"identifier":"no","buttonText":"no"}]
                self.unity_lock[self.student] = True
                self.html_lock[self.teacher] = False

                self.update_ui(self.teacher)
                self.update_ui(self.student)

    def button(self, actor, button_id):
        if actor==self.student:
            print("students should not be able to press buttons")
            return

        if actor==self.teacher:
            self.control = self.student
            self.unity_lock[self.student] = False
            self.html_lock[self.teacher] = True
            

            if button_id == "yes":
                self.emit('sendTrainingMessage', 'SYSTEM: The teacher allowed your action.', room=self.student)
                
            if button_id == "no": 
                self.emit('load', self.prev_state, room=self.student)
                self.emit('load', self.prev_state, room=self.teacher)
                self.emit('sendTrainingMessage', 'SYSTEM: The teacher disallowed your action. Try again.', room=self.student)

            self.prev_state = None
            self.training_buttons[self.teacher] = []

            self.update_ui(self.teacher)
            self.update_ui(self.student)
            
    
            
def HtmlUnityReward(HtmlUnity):
    def action(self, actor, action):
        pass

    def button(self, actor, action):
        pass

def HtmlUnityApprentice(HtmlUnity):
    def action(self, actor, action):
        pass

    def button(self, actor, action):
        pass





        

    


