__author__ = 'paulcao'

from sqlalchemy import Column, ForeignKey, Integer, String, DateTime, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine

import config
import datetime
import json

Base = declarative_base()

class Workflow(Base):
    __tablename__ = 'workflow'
    id = Column(String(60), primary_key=True)
    name = Column(String(250), nullable=True)
    status = Column(String(30), nullable=False)
    start = Column(DateTime(), nullable=True)
    end = Column(DateTime, nullable=True)
    person_id = Column(String(250), nullable=True)
    notified = Column(Boolean, nullable=False)

    @staticmethod
    def parse_time(dt_str):
            return datetime.datetime.strptime(dt_str.split(".")[0], "%Y-%m-%dT%H:%M:%S") if dt_str else None

    @staticmethod
    def get_or_none(field, dict):
        return dict[field] if field in dict else None

    @staticmethod
    def get_person_id(metadata):
        if 'labels' in metadata and 'username' in metadata['labels']:
            return metadata['labels']['username']
        else:
            if 'submittedFiles' in metadata and 'labels' in metadata['submittedFiles']:
                if 'username' in json.loads(metadata['submittedFiles']['labels']):
                    return json.loads(metadata['submittedFiles']['labels'])['username']

        return None

    def __init__(self, cromwell, w_id):
        metadata = cromwell.query_metadata(w_id)
        self.id = metadata["id"]
        self.name = self.get_or_none("workflowName", metadata)
        self.status = metadata["status"]
        self.start = self.parse_time(self.get_or_none("start", metadata))
        self.notified = False
        self.person_id = self.get_person_id(metadata)
        self.cached_metadata = metadata

        #super(Workflow, self).__init__(id=metadata["id"], name=self.get_or_none("workflowName", metadata),
        #                        status=metadata["status"], start=self.parse_time(self.get_or_none("start")),
        #                        notified=False, person_id=self.get_person_id(metadata))

    def update_status(self, status):
        self.status = status
        self.notified = True

# Create an engine that stores data in the local directory's
# sqlalchemy_example.db file.
engine = create_engine('sqlite:///' + config.workflow_db)

# Create all tables in the engine. This is equivalent to "Create Table"
# statements in raw SQL.
Base.metadata.create_all(engine)