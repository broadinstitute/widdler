import datetime
import calendar
from Cromwell import Cromwell
from Messenger import Messenger
from dateutil.parser import parse
import json
from email.mime.text import MIMEText
import logging
import config as c


class EmailNotification(object):

    def __init__(self, cromwell):
        self.messenger = Messenger("")

    def on_changed_workflow_status(self, workflow, metadata, host):
        if (workflow.status == "Aborted" or workflow.status == "Failed" or workflow.status == "Succeeded") and \
                (workflow.person_id != "" and workflow.person_id != None):
            email_body = self.generate_content(metadata=metadata,
                                                user=workflow.person_id, host=host)
            msg = self.messenger.compose_email(email_body)
            EmailNotification.attach_logs(msg, metadata)

            logging.warn("E-mail notification for: " + str(workflow) + " to " + workflow.person_id)
            self.messenger.send_email(msg, workflow.person_id + "@broadinstitute.org")

    @staticmethod
    def attach_logs(msg, metadata):
        failed_jobs = Cromwell.getCalls('Failed', metadata['calls'], full_logs=True)

        for log in failed_jobs:
            stdout_attachment = MIMEText(str(log["stdout"]['log']))
            stdout_attachment.add_header('Content-Disposition', 'attachment', filename=log["stdout"]["label"])
            msg.attach(stdout_attachment)

            stderr_attachment = MIMEText(str(log["stderr"]['log']))
            stderr_attachment.add_header('Content-Disposition', 'attachment', filename=log["stderr"]["label"])
            msg.attach(stderr_attachment)

        metadata_attachment = MIMEText(str(json.dumps(metadata, indent=4, default=EmailNotification.json_serializer)))
        metadata_attachment.add_header('Content-Disposition', 'attachment', filename=metadata["id"] + ".metadata")
        msg.attach(metadata_attachment)

    def json_serializer(obj):
        """JSON serializer for time."""
        if isinstance(obj, datetime.datetime):
            if obj.utcoffset() is not None:
                obj = obj - obj.utcoffset()
                return int(calendar.timegm(obj.timetuple()) * 1000 +obj.microsecond / 1000)
        raise TypeError('Not sure how to serialize %s' % (obj,))

    def generate_content(self, metadata, user, host):
        """
        a method for generating the email content to be sent to user.
        :param metadata: The metadata of the workflow (optional).
        :return: a dictionary containing the email contents for the template.
        """
        jdata = metadata
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
            if host == c.gscid_cloud_server or host == c.cloud_server:
                import re
                root_array = re.split(r"[/]+", jdata['workflowRoot'])
                exec_dir = ""
                if host == c.gscid_cloud_server:
                    exec_dir = "/cromwell-executions"
                gcp_url = "https://console.cloud.google.com/storage/browser/{}{}/{}/{}".format(root_array[1], exec_dir,
                                                                                               jdata['workflowName'],
                                                                                               jdata['id'])
                href_root = "<a href=\"{}\"> {} </a>".format(gcp_url, jdata['workflowRoot'])
                summary += "<br><b>workflowRoot:</b> {}".format(href_root)
            else:
                summary += "<br><b>workflowRoot:</b> {}".format(jdata['workflowRoot'])
        if host in c.cloud_hosts:
            port = c.cloud_port
        else:
            port = c.local_port

        summary += "<br><b>Timing graph:</b> http://{}:{}/api/workflows/v2/{}/timing".format(host, port, jdata['id'])
        email_content = {
            'user': user,
            'workflow_id': jdata['id'],
            'status': jdata['status'],
            'summary': summary
        }
        return email_content