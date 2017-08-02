#!/usr/bin/env python
"""Module for persistent monitoring of workflows."""
import logging
import time
import getpass
from Cromwell import Cromwell
from Messenger import Messenger
__author__ = "Amr Abouelleil"

module_logger = logging.getLogger('widdler.Monitor')


class Monitor:
    """
    A class for monitoring a user's workflows, providing status reports at regular intervals.
    """
    def __init__(self, user, host, port=9000):
        self.user = user
        self.cromwell = Cromwell(host=host, port=port)
        self.messenger = Messenger(self.user)

    # def get_user_workflows(self, user, query_dict):
    #     result = self.cromwell.query(query_dict)
    #     user_results = dict()
    #     results = (result['results'])
    #     for result in results:
    #         print(result)
    # # get all workflows using query function to subset by values supported by the API
    # # filter results to include those specific to the user.

    def monitor_workflow(self, workflow_id, interval):
        run_states = ['Running', 'Submitted']
        finished = False
        while not finished:
            query_status = self.cromwell.query_status(workflow_id)
            print(query_status)
            if query_status['status'] not in run_states:
                email_content = {
                    'user': self.user,
                    'name': 'test',
                    'workflow_id': query_status['id'],
                    'status': query_status['status'],
                    'metadata': self.cromwell.query_metadata(workflow_id)
                }
                msg = self.messenger.compose_email(email_content)
                self.messenger.send_email(msg)
                finished = True
            time.sleep(interval)

