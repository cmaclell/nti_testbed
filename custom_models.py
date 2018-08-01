from psiturk.db import Base, db_session, init_db
from sqlalchemy import or_, Column, Integer, String, DateTime, Boolean, Float, Text, ForeignKey, func, event, JSON
from sqlalchemy.orm import relationship, backref
from sqlalchemy.ext.orderinglist import ordering_list

import uuid, datetime


class Task(Base):
    __tablename__ ='task'
    task_id = Column(Integer, primary_key=True)
    last_active = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())
    pattern = Column(String(80))
    init_state = Column(JSON)
    event = relationship("Event", order_by="Event.timestamp", collection_class=ordering_list('timestamp'))
    def __init__(self, pattern):
        self.pattern = pattern

class User(Base):
    __tablename__ = 'user'
    user_id = Column(String(80), primary_key=True)

    ip = Column(String(80))
    role = Column(String(80))

    task_id = Column(Integer, ForeignKey(Task.task_id), nullable=True)
    task = relationship("Task", uselist=False, foreign_keys=[task_id], post_update=True)

    last_active = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())

    def __init__(self, uid, ip='unknown'):
        self.user_id = uid
        self.ip = ip
        self.role = 'unassigned'
        self.task_id = None

class Event(Base):
    """ events from the user """
    __tablename__ = 'event'
    event_id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, nullable=False, server_default=func.now())

    task_id = Column(Integer, ForeignKey('task.task_id'), nullable=False)
    task = relationship("Task", uselist=True, foreign_keys=[task_id], post_update=True)

    user_id = Column(Integer, ForeignKey('user.user_id'), nullable=False)
    user = relationship("User", uselist=False, foreign_keys=[user_id], post_update=True)

    event_type = Column(String(80))
    event_data = Column(JSON) # needs to be json blob

    def __init__(self, event_data):
        self.event_data = event_data



    
if __name__=="__main__":
    pass


# @event.listens_for(ActiveTask, "after_update")
# def insert_order_to_printer(mapper, connection, target):
#     print("active task updated":, mapper, connection, target)