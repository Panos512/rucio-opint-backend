from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy import MetaData, Enum, Boolean, Column, Integer, String, Float, ForeignKey, DateTime
from sqlalchemy import create_engine
import datetime

meta = MetaData()
Base = declarative_base()


class Error(Base):
    __tablename__ = 'error'
    id = Column(Integer, primary_key=True, nullable=True)
    category_id = Column(Integer, ForeignKey('error_category.id'))
    message = Column(String)
    src_site = Column(String)
    dst_site = Column(String)
    amount = Column(Integer)
    failure_type = Column(String)
    created_at = Column(DateTime, default=datetime.datetime.now())
    status = Column(Enum('new', 'ongoing', 'resolved'), nullable=False, default='new', server_default='new')


class Issue(Base):
    __tablename__ = 'issue'
    id = Column(Integer, primary_key=True)
    text = Column(String)
    created_at = Column(DateTime, default=datetime.datetime.now())

    error_category = relationship('Error_category')
    error_reason_solution = relationship('Error_reason_solution')


class Action(Base):
    __tablename__ = 'action'
    id = Column(Integer, primary_key=True)
    text = Column(String)
    created_at = Column(DateTime, default=datetime.datetime.now())


class Error_category(Base):
    __tablename__ = 'error_category'
    id = Column(Integer, primary_key=True)
    issue_id = Column(Integer, ForeignKey('issue.id'), nullable=True)
    total_amount = Column(Integer)
    regular_expression = Column(String)
    created_at = Column(DateTime, default=datetime.datetime.now())

    error = relationship('Error')


class Error_reason_solution(Base):
    __tablename__ = 'error_reason_solution'
    id = Column(Integer, primary_key=True)
    category_id = Column(Integer, ForeignKey('error_category.id'))
    proposed_action_id = Column(Integer, ForeignKey('action.id'), nullable=True)
    real_solution_id = Column(Integer, ForeignKey('action.id'), nullable=True)
    issue_id = Column(Integer, ForeignKey('issue.id'))
    probability = Column(Float, nullable=True)
    score = Column(Boolean, nullable=True)
    affected_site = Column(Enum('dst_site', 'src_site', 'site_unknown'), nullable=False, default='site_unknown', server_default='site_unknown')
    created_at = Column(DateTime, default=datetime.datetime.now())

    proposed_action = relationship('Action', foreign_keys='Error_reason_solution.proposed_action_id')
    real_solution = relationship('Action', foreign_keys='Error_reason_solution.real_solution_id')


def getsess(db_file):
    Session = sessionmaker()
    engine = create_engine(db_file, echo=True)
    Base.metadata.create_all(engine)
    Session.configure(bind=engine)
    return Session()
