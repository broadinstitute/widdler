import smtplib
import os
from email.mime.text import MIMEText
from string import Template
from email.mime.multipart import MIMEMultipart
from email.utils import formatdate
import src.config as c

__author__ = "Amr Abouelleil"


class Messenger(object):
    """
    Some docstring
    """

    def __init__(self, user):
        self.user_email = "{}@broadinstitute.org".format(user)
        self.sender = "widdler@broadinstitute.org"

    def compose_email(self, content_dict):
        subject = "Workflow ({}) {}".format(content_dict['workflow_id'], content_dict['status'])
        msg = MIMEMultipart(From=self.sender, To=self.user_email, Date=formatdate(localtime=True),
                            Subject=subject)
        msg["Subject"] = subject
        template = open(os.path.join(c.resource_dir, 'email.template'), 'r')
        src = Template(template.read())
        text = src.safe_substitute(content_dict)
        msg.attach(MIMEText(text))
        template.close()
        return msg

    def send_email(self, msg):
        mailer = smtplib.SMTP('localhost')
        mailer.sendmail(self.sender, self.user_email, msg.as_string())
