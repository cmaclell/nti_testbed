from psiturk.db import Base, db_session, init_db
from sqlalchemy import or_, Column, Integer, String, DateTime, Boolean, Float, Text, ForeignKey, func, event
from sqlalchemy.orm import relationship, backref
import uuid, datetime

# class Queue(Base):
#   __tablename__ = 'queue'
#   user_id = Column(Integer, primary_key=True, ForeignKey("user.user_id"))
#   timestamp = Column(DateTime, default=datetime.datetime.utcnow)

#   def __init__(self, fid):
#       self.user_id = fid



class Task(Base):
    __tablename__ = 'task'
    task_id = Column(Integer, primary_key=True)
    task_name = Column(String(80))
    task_description = Column(String(255))

class User(Base):
    __tablename__ = 'user'
    user_id = Column(Integer, primary_key=True)
    ip = Column(String(80))
    assigned_task = Column(Boolean, default=False)
    #last_active = last_time = Column(TIMESTAMP, server_default=func.now(), onupdate=func.current_timestamp())
    last_active = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())
    
    def __init__(self, ip='unknown'):
        self.ip = ip

    def __repr__(self):
        return '<User %r>' % (self.ip)


class ActiveTask(Base):
    __tablename__ ='active_task'
    task_id = Column(Integer, primary_key=True)
    teacher_id = Column(Integer, ForeignKey("user.user_id"))
    student_id = Column(Integer, ForeignKey("user.user_id"))
    #task_type = Column(Integer, ForeignKey("task.task_id"))
    #last_active = Column(DateTime, default=datetime.datetime.utcnow)
    last_active = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())

    def __init__(self, teacher, student, type=0):
        self.teacher_id = teacher
        self.student_id = student
        #self.task_type = type

# @event.listens_for(ActiveTask, "after_update")
# def insert_order_to_printer(mapper, connection, target):
#     print("active task updated":, mapper, connection, target)