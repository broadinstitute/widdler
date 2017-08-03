#!/usr/bin/env python
"""Module for persistent monitoring of workflows."""
import logging
import time
import json
from multiprocessing import Pool
from functools import partial
from src.Cromwell import Cromwell
from src.Messenger import Messenger
__author__ = "Amr Abouelleil"

module_logger = logging.getLogger('widdler.Monitor')


def is_user_workflow(host, user, workflow_id):
    """
     A top-level function that returns a workflow if it matches the user workflow. This can't be an instance method
     of Monitor because we run into serializing issues otherwise. See:
     https://stackoverflow.com/questions/26249442/can-i-use-multiprocessing-pool-in-a-method-of-a-class
    """
    metadata = Cromwell(host=host).query_metadata(workflow_id)

    j_input = json.loads(metadata['submittedFiles']['inputs'])
    try:
        if j_input['user'] == user:
            return workflow_id
    except KeyError:
        return None


class Monitor:
    """
    A class for monitoring a user's workflows, providing status reports at regular intervals.
    """
    def __init__(self, user, host, notify, verbose, interval):
        self.host = host
        self.user = user
        self.interval = interval
        self.cromwell = Cromwell(host=host)
        self.messenger = Messenger(self.user)
        self.notify = notify
        self.verbose = verbose

    def get_user_workflows(self):
        print('Determining {}\'s workflows. This could take a while...'.format(self.user))
        workflows = []
        results = self.cromwell.query(query_dict={})
        for result in results['results']:
            workflows.append(result['id'])
        # With the list of workflows, query metadata for each one
        p = Pool()
        func = partial(is_user_workflow, self.host, self.user)
        results = p.map(func, workflows)
        p.close()
        p.join()
        user_workflows = ([x for x in results if x is not None])
        return user_workflows

    def monitor_user_workflows(self):
        print('Monitoring {}\'s workflows.')
        user_workflows = self.get_user_workflows()
        for workflow in user_workflows:
            self.monitor_workflow(workflow)

    def monitor_workflow(self, workflow_id):
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
            time.sleep(self.interval)

