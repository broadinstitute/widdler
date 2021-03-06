"""
A module that handles messaging of workflow results.
"""
import smtplib
import os
from email.mime.text import MIMEText
from string import Template
from email.mime.multipart import MIMEMultipart
from email.utils import formatdate
import src.config as c
from ratelimit import rate_limited

__author__ = "Amr Abouelleil"


ONE_MINUTE = 60


class Messenger(object):
    """
    A class for generating and sending messages with workflow results to users.
    """

    def __init__(self, user):
        self.user_email = "{}@broadinstitute.org".format(user)
        self.sender = "widdler@broadinstitute.org"

    def compose_email(self, content_dict):
        """
        Composes an e-mail to be sent containing workflow ID, result of the workflow, and workflow metadata.
        :param content_dict: A dictionary of key/value pairs that fulfill the requirements of email.template. The keys
        are: workflow_id, user, status, and metadata.
        :return: A MIMEMultipart message object.
        """
        subject = "Workflow ({}) {}".format(content_dict['workflow_id'], content_dict['status'])
        msg = MIMEMultipart(From=self.sender, To=self.user_email, Date=formatdate(localtime=True),
                            Subject=subject)
        msg["Subject"] = subject
        template = open(os.path.join(c.resource_dir, 'email.template'), 'r')
        src = Template(template.read())
        text = src.safe_substitute(content_dict)
        msg.attach(MIMEText(text, 'html'))
        template.close()
        return msg

    @rate_limited(300, ONE_MINUTE)
    def send_email(self, msg, user=None):
        """
        Sends an e-mail to recipients using the localhosts smtp server.
        :param msg: A MIMEMultipart message object.
        :return: 
        """
        mailer = smtplib.SMTP('smtp.broadinstitute.org')
        if not user:
            mailer.sendmail(self.sender, self.user_email, msg.as_string())
        else:
            mailer.sendmail(self.sender, user, msg.as_string())
