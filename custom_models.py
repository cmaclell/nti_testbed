from psiturk.db import Base, db_session, init_db
from sqlalchemy import or_, Column, Integer, String, DateTime, Boolean, Float, Text, ForeignKey
from sqlalchemy.orm import relationship, backref


class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    name = Column(String(50), unique=True)
    email = Column(String(120), unique=True)

    def __init__(self, name=None, email=None):
        self.name = name
        self.email = email

    def __repr__(self):
        return '<User %r>' % (self.name)

class LegitWorker(Base):
	"""
	DB for tracking workers who need compensation
	"""
	__tablename__ = 'legit_worker'
	index = Column(Integer, primary_key=True, unique=True)
	amt_worker_id = Column(String(128))
	completion_code = Column(String(128))
	status = Column(String(128))
	bonus = Column(Float)

	def __init__(self, workerid):
		self.amt_worker_id = workerid
		self.status = 'owed'
		
	def set_bonus(self, bonus):
		self.bonus = bonus

	def submitted(self):
		self.status = 'submitted'

	def paid(self):
		self.status = 'paid'
