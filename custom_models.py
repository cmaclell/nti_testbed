from psiturk.db import Base, db_session, init_db
from sqlalchemy import or_, Column, Integer, String, DateTime, Boolean, Float, Text, ForeignKey, func, event, ForeignKeyConstraint
from sqlalchemy.orm import relationship, backref
from sqlalchemy.ext.orderinglist import ordering_list
#from sqlalchemy.ext.compiler import compiles
#from sqlalchemy.sql.functions import FunctionElement
from datetime import datetime, date

import uuid, json

class Session(Base):
    __tablename__ = 'session'
    session_id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, nullable=False)
    last_active = Column(DateTime, nullable=True, onupdate=func.now())
    pattern = Column(String(40))
   
    tasks = relationship("Task", order_by="Task.timestamp", collection_class=ordering_list('timestamp'))
    
    def __init__(self, pattern):
        self.pattern = pattern
        self.timestamp = datetime.now()

class Task(Base):
    __tablename__ ='task'
    session_id = Column(Integer, ForeignKey('session.session_id'), primary_key=True)
    task_number = Column(Integer, primary_key=True)
    
    timestamp = Column(DateTime, nullable=False)
    last_active = Column(DateTime, nullable=True, onupdate=func.now())
    init_state = Column(Text)
    final_state = Column(Text)
    level_path = Column(String(80))

    
    session = relationship("Session", uselist=True, foreign_keys=[session_id], post_update=True)
    emissions = relationship("Emission", order_by="Emission.timestamp", collection_class=ordering_list('timestamp'))

    student = Column(String(40))
    teacher = Column(String(40))
    #student = relationship("User", uselist=False, post_update=True)
    #teacher = relationship("User", uselist=False, post_update=True)

    def __init__(self, session_id, task_number, init_state=""):
        init_state = json.dumps(init_state)
        self.init_state=init_state
        self.timestamp = datetime.now()
        self.session_id = session_id
        self.task_number = task_number

class User(Base):
    __tablename__ = 'user'
    user_id = Column(String(30), primary_key=True)

    ip = Column(String(80))
    role = Column(String(20))

    #task_id = Column(Integer, ForeignKey(Task.task_id), nullable=True)
    #task = relationship("Task", uselist=False, foreign_keys=[task_id], post_update=True)

    last_active = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())

    def __init__(self, uid, ip='unknown', role=None):
        self.user_id = uid
        self.ip = ip
        self.role = 'unassigned'

class Emission(Base):
    """ events from the user """
    __tablename__ = 'emission'
    emit_id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, nullable=False)

    session_id = Column(Integer, nullable=False) #ForeignKey('Task.session_id'))
    task_number = Column(Integer, nullable=False) #ForeignKey('Task.task_number'))


    #task_id = Column(Integer, ForeignKey('task.task_id'), nullable=True)
    task = relationship("Task", uselist=True, foreign_keys=[session_id, task_number], post_update=True)

    user_id = Column(Integer, ForeignKey('user.user_id'), nullable=True)
    user = relationship("User", uselist=False, foreign_keys=[user_id], post_update=True)

    topic = Column(String(80))
    data = Column(Text) 
    room = Column(String(80))

    __table_args__ = (ForeignKeyConstraint([session_id, task_number], [Task.session_id, Task.task_number]),)

    def __init__(self,  topic, data, room):
        #session_id, task_number,
        #self.session_id = session_id
        #self.task_number = task_number
        self.topic = topic
        self.data = data
        self.room = room
        self.timestamp = datetime.now()
        
# class Event(Base):
#     """ events from the user """
#     __tablename__ = 'event'
#     event_id = Column(Integer, primary_key=True)
#     timestamp = Column(DateTime, nullable=False, server_default=func.now())

#     task_id = Column(Integer, ForeignKey('task.task_id'), nullable=False)
#     task = relationship("Task", uselist=True, foreign_keys=[task_id], post_update=True)

#     user_id = Column(Integer, ForeignKey('user.user_id'), nullable=False)
#     user = relationship("User", uselist=False, foreign_keys=[user_id], post_update=True)

#     event_type = Column(String(80))
#     event_data = Column(Text) # needs to be json blob

#     def __init__(self, event_data):
#         self.event_data = event_data



    
if __name__=="__main__":
    pass


# @event.listens_for(ActiveTask, "after_update")
# def insert_order_to_printer(mapper, connection, target):
#     print("active task updated":, mapper, connection, target)