from psiturk.db import Base, db_session, init_db
from sqlalchemy import or_, Column, Integer, String, DateTime, Boolean, Float, Text, ForeignKey, func, event
from sqlalchemy.orm import relationship, backref
from sqlalchemy.ext.orderinglist import ordering_list
import uuid, datetime


class Task(Base):
    __tablename__ ='task'
    task_id = Column(Integer, primary_key=True)
    last_active = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())
    pattern = Column(String(80))
    state = relationship("State", order_by="State.timestamp", collection_class=ordering_list('timestamp'))
 
    def __init__(self, pattern):
        self.pattern = pattern

class State(Base):
    __tablename__ = 'state'
    state_id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, nullable=False, server_default=func.now())
    task_id = Column(Integer, ForeignKey('task.task_id'), nullable=False)
    payload = Column(String(80)) # needs to be json blob

    def __init__(self, payload):
        self.payload = payload


class User(Base):
    __tablename__ = 'user'
    user_id = Column(String(80), primary_key=True)

    ip = Column(String(80))
    role = Column(String(80))

    task_id = Column(Integer, ForeignKey(Task.task_id), nullable=True)
    task = relationship("Task", uselist=False, foreign_keys=[task_id], post_update=True)

    partner_id = Column(String(80), ForeignKey('user.user_id'), nullable=True)
    partner = relationship('User', remote_side = [user_id], foreign_keys=[partner_id])

    last_active = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())

    def __init__(self, uid, ip='unknown'):
        self.user_id = uid
        self.ip = ip
        self.role = 'unassigned'
        self.task_id = None
        self.partner_id = None
        

    def __repr__(self):
        return '<User %r>' % (self.user_id)


if __name__=="__main__":
    u1, u2 = User(5), User(23)
    #u1.partner = u2

    #print(u1.partner.user_id)

    t = Task()
   
    t.state.append(State("2"))
    t.state.append(State("3"))
    t.state.append(State("4"))

    print(t.state)



# @event.listens_for(ActiveTask, "after_update")
# def insert_order_to_printer(mapper, connection, target):
#     print("active task updated":, mapper, connection, target)