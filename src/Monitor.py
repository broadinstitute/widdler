#!/usr/bin/env python
"""Module for persistent monitoring of workflows."""
import logging
import time
import json
from src.Cromwell import Cromwell
from src.Messenger import Messenger
__author__ = "Amr Abouelleil"

module_logger = logging.getLogger('widdler.Monitor')


class Monitor:
    """
    A class for monitoring a user's workflows, providing status reports at regular intervals.
    """
    def __init__(self, user, host, notify, verbose):
        self.user = user
        self.cromwell = Cromwell(host=host)
        self.messenger = Messenger(self.user)
        self.notify = notify
        self.verbose = verbose
    # def get_user_workflows(self, user, query_dict):
    #     result = self.cromwell.query(query_dict)
    #     user_results = dict()
    #     results = (result['results'])
    #     for result in results:
    #         print(result)
    # # get all workflows using query function to subset by values supported by the API
    # # filter results to include those specific to the user.

    def monitor_user_workflows(self):
        workflows = []
        results = self.cromwell.query(query_dict={})
        print(results['results'])
        for result in results['results']:
            workflows.append(result['id'])
        print(workflows)

    def monitor_workflow(self, workflow_id, interval):
        run_states = ['Running', 'Submitted']
        while 0 == 0:
            query_status = self.cromwell.query_status(workflow_id)
            if self.verbose:
                print('Workflow {} | {}'.format(query_status['id'], query_status['status']))
            if query_status['status'] not in run_states:
                if self.notify:
                    email_content = {
                        'user': self.user,
                        'workflow_id': query_status['id'],
                        'status': query_status['status'],
                        'metadata': json.dumps(self.cromwell.query_metadata(workflow_id), indent=4)
                    }
                    msg = self.messenger.compose_email(email_content)
                    self.messenger.send_email(msg)
                return 0
            time.sleep(interval)

