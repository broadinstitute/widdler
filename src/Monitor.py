#!/usr/bin/env python
"""Module for persistent monitoring of workflows."""
import logging
import time
import json
import os
from multiprocessing import Pool
from functools import partial
import src.config as c
from src.Cromwell import Cromwell
from src.Messenger import Messenger
from email.mime.text import MIMEText

__author__ = "Amr Abouelleil"

module_logger = logging.getLogger('widdler.Monitor')


def is_user_workflow(host, user, workflow_id):
    """
    A top-level function that returns a workflow if it matches the user workflow. This can't be an instance method
     of Monitor because we run into serializing issues otherwise. See:
     https://stackoverflow.com/questions/26249442/can-i-use-multiprocessing-pool-in-a-method-of-a-class
    :param host: cromwell server
    :param user: user name to monitor
    :param workflow_id: workflow
    :return:  The workflow_id if it's the user owns the workflow. Otherwise None.
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
    A class for monitoring a user's workflows, providing status reports at regular intervals
    as well as e-mail notification.
    """
    def __init__(self, user, host, no_notify, verbose, interval):
        self.host = host
        self.user = user
        self.interval = interval
        self.cromwell = Cromwell(host=host)
        self.messenger = Messenger(self.user)
        self.no_notify = no_notify
        self.verbose = verbose

    def get_user_workflows(self):
        """
        A function for creating a list of workflows owned by a particular user.
        :return: A list of workflow IDs owned by the user.
        """
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
        """
        A function for monitoring a several workflows.
        :return:
        """
        print('Monitoring {}\'s workflows.')
        user_workflows = self.get_user_workflows()
        for workflow in user_workflows:
            self.monitor_workflow(workflow)

    def monitor_workflow(self, workflow_id):
        """
        Monitor the status of a single workflow.
        :param workflow_id: Workflow ID of workflow to monitor.
        :return: returns 0 when workflow reaches terminal state.
        """
        run_states = ['Running', 'Submitted', 'QueuedInCromwell']
        while 0 == 0:
            query_status = self.cromwell.query_status(workflow_id)
            if self.verbose:
                print('Workflow {} | {}'.format(query_status['id'], query_status['status']))
            if query_status['status'] not in run_states:
                if not self.no_notify:
                    filename = '{}.metadata.json'.format(query_status['id'])
                    filepath = os.path.join(c.log_dir, '{}.metadata.json'.format(query_status['id']))
                    jdata = self.cromwell.query_metadata(workflow_id)

                    metadata = open(filepath, 'w+')
                    json.dump(self.cromwell.query_metadata(workflow_id), indent=4, fp=metadata)
                    metadata.close()
                    read_data = open(filepath, 'r')
                    attachment = MIMEText(read_data.read())
                    read_data.close()
                    os.unlink(filepath)
                    attachment.add_header('Content-Disposition', 'attachment', filename=filename)
                    summary = ""
                    if 'start' in jdata:
                        summary += "Started: {}\n".format(jdata['start'])
                    if 'end' in jdata:
                        summary += "Ended: {}\n".format(jdata['end'])
                    if 'Failed' in query_status['status']:
                        summary += "\nFailures: {}".format(json.dumps(jdata['failures'], indent=4))
                    if 'workflowName' in jdata:
                        summary = "Workflow Name: {}\n{}".format(jdata['workflowName'], summary)
                    if 'workflowRoot' in jdata:
                        summary += "\nworkflowRoot: {}".format(jdata['workflowRoot'])
                    email_content = {
                        'user': self.user,
                        'workflow_id': query_status['id'],
                        'status': query_status['status'],
                        'summary': summary,
                    }
                    msg = self.messenger.compose_email(email_content)
                    msg.attach(attachment)
                    self.messenger.send_email(msg)
                return 0
            time.sleep(self.interval)

