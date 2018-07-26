import socketio

class LearningPattern:
    pass
   
class Observe(LearningPattern):
    def init(self):
        self.control = self.student_id

    def student_event(self, event_type, event_data):
        if self.control is self.student_id:
            self.control = self.teacher_id
        else:
            print("student requested action but doesn't have control")
        

    def teacher_event(self, event_type, event_data):
        if self.control is self.teacher_id:
            self.control = self.student_id
            
        else:
            print("teacher requested action but doesn't have control")


class HtmlUnityModality:
    """ contains logic for mapping htmlunity experiment inputs to learning pattern api """ 
    def __init__(self, pattern, sio, teacher, student):
        assert isinstance(pattern, LearningPattern)
        assert type(teacher) == unicode
        assert type(student) == unicode
        assert type(sio) == socketio.Server

        self.pattern = pattern
        self.sio = sio
        self.teacher = teacher
        self.student = student
        self.sio.emit('getTrainingButtons', [{"identifier":"ok","buttonText":"ok"}], room=self.teacher)
        self.sio.emit('lock', room=self.teacher)

        self.event_dict = {'button': self.button, 'action': self.action}

    def event(self, actor, event_type, event_data):
        self.event_dict[event_type](actor, event_data)

    def button(self, actor, id):
        if actor==self.teacher:
            pass

        if actor==self.student:
            pass

    def action(self, actor, state):
        if actor==self.teacher:
            pass

        if actor==self.student:
            pass
        





        

    


