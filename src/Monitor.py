#!/usr/bin/env python
"""Module for persistent monitoring of workflows."""
import logging
import time
import json
import os
import re
from dateutil.parser import parse
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

    try:
        j_input = json.loads(metadata['submittedFiles']['inputs'])
        if j_input['user'] == user:
            return workflow_id
    except KeyError:
        return None


class Monitor:
    """
    A class for monitoring a user's workflows, providing status reports at regular intervals
    as well as e-mail notification.
    """
    def __init__(self, user, host, no_notify, verbose, interval, status_filter=None):
        self.host = host
        self.user = user
        self.interval = interval
        self.cromwell = Cromwell(host=host)
        self.messenger = Messenger(self.user)
        self.no_notify = no_notify
        self.verbose = verbose
        self.status_filter = status_filter

    def get_user_workflows(self, raw=False, start_time=None):
        """
        A function for creating a list of workflows owned by a particular user.
        :return: A list of workflow IDs owned by the user.
        """
        print('Determining {}\'s workflows...'.format(self.user))
        user_workflows = []

        results = None
        if self.user == "*":
            results = self.cromwell.query_labels({}, start_time=start_time, status_filter=self.status_filter)
        else:
            results = self.cromwell.query_labels({'username': self.user}, start_time=start_time,
                                                 status_filter=self.status_filter)

        if raw:
            return results

        try:
            for result in results['results']:
                if result['status'] in c.run_states:
                    user_workflows.append(result['id'])
        except KeyError as e:
            print('No user workflows found with username {}.'.format(self.user))
        return user_workflows

    def monitor_user_workflows(self):
        """
        A function for monitoring a several workflows.
        :return:
        """
        print('Monitoring {}\'s workflows.'.format(self.user))
        workflows = self.get_user_workflows()
        if len(workflows) == 0:
            print("User {} has no running workflows.".format(self.user))
        else:
            for workflow in workflows:
                self.monitor_workflow(workflow)

    def monitor_workflow(self, workflow_id):
        """
        Monitor the status of a single workflow.
        :param workflow_id: Workflow ID of workflow to monitor.
        :return: returns 0 when workflow reaches terminal state.
        """

        while 0 == 0:
            query_status = self.cromwell.query_status(workflow_id)
            if self.verbose:
                print('Workflow {} | {}'.format(query_status['id'], query_status['status']))
            if query_status['status'] not in c.run_states:
                if not self.no_notify:
                    filename = '{}.metadata.json'.format(query_status['id'])
                    filepath = os.path.join(c.log_dir, '{}.metadata.json'.format(query_status['id']))
                    metadata = open(filepath, 'w+')
                    json.dump(self.cromwell.query_metadata(workflow_id), indent=4, fp=metadata)
                    metadata.close()
                    email_content = self.generate_content(query_status=query_status, workflow_id=workflow_id)
                    msg = self.messenger.compose_email(email_content)

                    file_dict = {filename: filepath}
                    if 'Failed' in query_status['status']:
                        jdata = self.cromwell.query_metadata(workflow_id)
                        if 'workflowRoot' in jdata:
                            for failure in jdata['failures']:
                                if failure['message'].startswith('Job'):
                                    job_info = failure['message'].split(' ')[1]
                                    (name, job, shard, attempt) = re.split(r"[:.]", job_info)
                                    if 'NA' in shard:
                                        job_path = '{}/call-{}/execution/' \
                                            .format(jdata['workflowRoot'], job, shard)
                                    else:
                                        job_path = '{}/call-{}/shard-{}/execution/'\
                                            .format(jdata['workflowRoot'], job, shard)
                                    stderr = '{}/stderr'.format(job_path)
                                    stdout = '{}stdout'.format(job_path)
                                    file_dict['{}.{}.stderr'.format(job, shard)] = stderr
                                    file_dict['{}.{}.stdout'.format(job, shard)] = stdout

                    attachments = self.generate_attachments(file_dict)
                    for attachment in attachments:
                        if attachment:
                            msg.attach(attachment)
                    self.messenger.send_email(msg)
                    os.unlink(filepath)
                return 0
            else:
                time.sleep(self.interval)

    @staticmethod
    def generate_attachment(filename, filepath):
        """
        Convert a file
        :param filename: The name to assign to the attachment.
        :param filepath: The absolute path of the file including the file itself.
        :return: An attachment object.
        """
        try:
            read_data = open(filepath, 'r')
            attachment = MIMEText(read_data.read())
            read_data.close()
            attachment.add_header('Content-Disposition', 'attachment', filename=filename)
            return attachment
        except IOError as e:
            logging.warn('Unable to generate attachment for {}:\n{}'.format(filename, e))

    def generate_attachments(self, file_dict):
        """
        Generates a list of attachments to be added to an e-mail
        :param file_dict: A dictionary of filename:filepath pairs. Not the name is what the file will be called, and
        does not refer to the name of the file as it exists prior to attaching. That should be part of the filepath.
        :return: A list of attachments
        """
        attachments = list()
        for name, path in file_dict.items():
            attachments.append(self.generate_attachment(name, path))
        return attachments

    def generate_content(self, query_status, workflow_id):
        jdata = self.cromwell.query_metadata(workflow_id)
        summary = ""
        if 'start' in jdata:
            summary += "<br><b>Started:</b> {}".format(jdata['start'])
        if 'end' in jdata:
            summary += "<br><b>Ended:</b> {}".format(jdata['end'])
        if 'start' in jdata and 'end' in jdata:
            start = parse(jdata['start'])
            end = parse(jdata['end'])
            duration = (end - start)
            hours, remainder = divmod(duration.seconds, 3600)
            minutes, seconds = divmod(remainder, 60)
            summary += '<br><b>Duration:</b> {} hours, {} minutes, {} seconds'.format(hours, minutes, seconds)
        if 'Failed' in query_status['status']:
            fail_summary = "<br><b>Failures:</b> {}".format(json.dumps(jdata['failures']))
            fail_summary = fail_summary.replace(',', '<br>')
            summary += fail_summary.replace('\n', '<br>')
        if 'workflowName' in jdata:
            summary = "<b>Workflow Name:</b> {}{}".format(jdata['workflowName'], summary)
        if 'workflowRoot' in jdata:
            summary += "<br><b>workflowRoot:</b> {}".format(jdata['workflowRoot'])
        summary += "<br><b>Timing graph:</b> http://{}:9000/api/workflows/v2/{}/timing".format(self.host,
                                                                                               query_status['id'])
        email_content = {
            'user': self.user,
            'workflow_id': query_status['id'],
            'status': query_status['status'],
            'summary': summary
        }
        return email_content
