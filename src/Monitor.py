#!/usr/bin/env python
"""Module for persistent monitoring of workflows."""
import logging
import time
import json
import os
from dateutil.parser import parse
import src.config as c
from src.Cromwell import Cromwell
from src.Messenger import Messenger
from email.mime.text import MIMEText
import pytz

import config
import datetime
from Models import Workflow,Base
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from EmailNotification import EmailNotification
from SystemTestNotification import SystemTestNotification
from Download import Download
from SystemTestDownload import SystemTestDownload

import traceback
import calendar

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

def get_iso_datestr(dt):
    return pytz.timezone("US/Eastern").localize(dt).isoformat()


class Monitor:
    """
    A class for monitoring a user's workflows, providing status reports at regular intervals
    as well as e-mail notification.
    """
    def __init__(self, user, host, no_notify, verbose, interval, workflow_id=None):
        self.host = host
        self.user = user
        self.interval = interval
        self.cromwell = Cromwell(host=host)
        self.messenger = Messenger(self.user)
        self.no_notify = no_notify
        self.verbose = verbose
        self.workflow_id = workflow_id
        self.event_subscribers = [EmailNotification(self.cromwell), SystemTestDownload(), Download()]

        engine = create_engine("sqlite:///" + config.workflow_db)
        Base.metadata.bind = engine
        DBSession = sessionmaker()
        DBSession.bind = engine
        self.session = DBSession()

    def get_user_workflows(self, raw=False, start_time=None, silent=False):
        """
        A function for creating a list of workflows owned by a particular user.
        :return: A list of workflow IDs owned by the user.
        """
        if not silent:
            print('Determining {}\'s workflows...'.format(self.user))

        user_workflows = []
        results = None
        if self.user == "*":
            results = self.cromwell.query_labels({}, start_time=start_time, running_jobs=True)
        else:
            results = self.cromwell.query_labels({'username': self.user}, start_time=start_time)

        if raw:
            return results

        try:
            for result in results['results']:
                if result['status'] in c.run_states:
                    user_workflows.append(result['id'])
        except Exception as e:
            logging.error(str(e))
            print('No user workflows found with username {}.'.format(self.user))
        return user_workflows

    def process_events(self, workflow):
        for event_subscriber in self.event_subscribers:
            metadata = self.cromwell.query_metadata(workflow.id) #get final metadata
            try:
                event_subscriber.on_changed_workflow_status(workflow, metadata, self.host)
            except Exception as e:
                logging.error(str(e))
                print("Event processing error occurred above.")

    def run(self):
        while True:
            try:
                one_day_ago = datetime.datetime.now() - datetime.timedelta(days=int(1))
                db_workflows = dict( (d.id, d) for d in self.session.query(Workflow).filter(Workflow.start > one_day_ago) )
                cromwell_workflows = dict( (c["id"], c) for c in self.get_user_workflows(raw=True, start_time=get_iso_datestr(one_day_ago), silent=True)['results'] )

                new_workflows = map(lambda c: Workflow(self.cromwell, c["id"]), filter(lambda w: w["id"] not in db_workflows, cromwell_workflows.values()))
                [self.session.add(w) for w in new_workflows]

                changed_workflows = filter(lambda d: d.id in cromwell_workflows and d.status != cromwell_workflows[d.id]["status"], db_workflows.values())
                [w.update_status(cromwell_workflows[w.id]["status"]) for w in changed_workflows]

                workflows_to_notify = new_workflows + changed_workflows
                [self.process_events(w) for w in workflows_to_notify]

                self.session.flush()
                self.session.commit()
            except Exception:
                traceback.print_exc()

            time.sleep(self.interval)

    def get_user_workflows(self, raw=False, start_time=None, silent=False):
        """
        A function for creating a list of workflows owned by a particular user.
        :return: A list of workflow IDs owned by the user.
        """
        if not silent:
            print('Determining {}\'s workflows...'.format(self.user))

        user_workflows = []
        results = None
        if self.user == "*":
            results = self.cromwell.query_labels({}, start_time=start_time, running_jobs=False)
        else:
            results = self.cromwell.query_labels({'username': self.user}, start_time=start_time)

        if raw:
            return results

        try:
            for result in results['results']:
                if result['status'] in c.run_states:
                    user_workflows.append(result['id'])
        except Exception as e:
            logging.error(str(e))
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
                        for task, call in jdata['calls'].items():
                            for shard in call:
                                if 'Failed' in shard['executionStatus']:
                                    attach_prefix = "{}.{}".format(task, shard['shardIndex'])
                                    stdout = "{}.stdout".format(attach_prefix)
                                    stderr = "{}.stderr".format(attach_prefix)
                                    try:
                                        file_dict[stdout] = shard['stdout']
                                    except Exception as e:
                                        logging.warn(str(e))
                                    try:
                                        file_dict[stderr] = shard['stderr']
                                    except Exception as e:
                                        logging.warn(str(e))
                                    break

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
        Create attachment from a file.
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
        except Exception as e:
            logging.warn('Unable to generate attachment for {}:\n{}'.format(filename, e))

    def generate_attachments(self, file_dict):
        """
        Generates a list of attachments to be added to an e-mail
        :param file_dict: A dictionary of filename:filepath pairs. Note the name is what the file will be called, and
        does not refer to the name of the file as it exists prior to attaching. That should be part of the filepath.
        :return: A list of attachments
        """
        attachments = list()
        # if file_dict.items() > 3:
        #     attachment = MIMEBase('application', 'zip')
        #     with zipfile.ZipFile('workflow_logs.zip', mode='w') as zf:
        #         for file_name, path in file_dict.items():
        #             try:
        #                 zf.write(path, os.path.basename(file_name))
        #             except Exception as e:
        #                 logging.warn('Unable to generate attachment for {}:\n{}'.format(file_name, e))
        #     zf.close()
        #     attachment.set_payload('workflow_logs.zip')
        #     encoders.encode_base64(attachment)
        #     attachment.add_header('Content-Disposition', 'attachment', filename='workflow_logs.zip')
        #     attachments.append(attachment)
        # else:
        for name, path in file_dict.items():
            attachments.append(self.generate_attachment(name, path))
        return attachments

    def generate_content(self, query_status, workflow_id, metadata=None, user=None):
        """
        a method for generating the email content to be sent to user.
        :param query_status: status of workflow (helps determine what content to include in email).
        :param workflow_id: Workflow ID of the workflow to create e-mail for.
        :param metadata: The metadata of the workflow (optional).
        :return: a dictionary containing the email contents for the template.
        """
        jdata = self.cromwell.query_metadata(workflow_id) if metadata is None else metadata
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
        if 'Failed' in jdata['status']:
            fail_summary = "<br><b>Failures:</b> {}".format(json.dumps(jdata['failures']))
            fail_summary = fail_summary.replace(',', '<br>')
            summary += fail_summary.replace('\n', '<br>')
        if 'workflowName' in jdata:
            summary = "<b>Workflow Name:</b> {}{}".format(jdata['workflowName'], summary)
        if 'workflowRoot' in jdata:
            summary += "<br><b>workflowRoot:</b> {}".format(jdata['workflowRoot'])
        summary += "<br><b>Timing graph:</b> http://{}:9000/api/workflows/v2/{}/timing".format(self.host,
                                                                                               jdata['id'])
        user = self.user if user is None else user
        email_content = {
            'user': user,
            'workflow_id': jdata['id'],
            'status': jdata['status'],
            'summary': summary
        }
        return email_content
