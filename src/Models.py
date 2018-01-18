__author__ = 'paulcao'

from sqlalchemy import Column, ForeignKey, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine

import config

Base = declarative_base()

class Workflow(Base):
    __tablename__ = 'workflow'
    id = Column(String(60), primary_key=True)
    name = Column(String(250), nullable=False)
    status = Column(String(30), nullable=False)
    start = Column(DateTime(), nullable=False)
    end = Column(DateTime, nullable=True)
    person_id = Column(String(250), nullable=True)

# Create an engine that stores data in the local directory's
# sqlalchemy_example.db file.
engine = create_engine('sqlite:///' + config.workflow_db)

# Create all tables in the engine. This is equivalent to "Create Table"
# statements in raw SQL.
Base.metadata.create_all(engine)