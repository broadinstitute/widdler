from string import Template
import urllib2
import logging
import json

import re
from src.SingleBucket import SingleBucket, make_bucket, list_buckets

class SystemTestDownload(object):

    def __init__(self):
        self.bucket = SingleBucket("broad-cil-devel-bucket")

    @staticmethod
    def is_systemtest_workflow(metadata):
        workflow_name = metadata["workflowName"]
        pattern = re.compile(workflow_name + ".[^.]+.system_test")

        matches = filter(lambda str: pattern.match(str), metadata)
        return len(matches) > 0

    def on_changed_workflow_status(self, workflow, metadata, host):
        if (workflow.status == "Succeeded"):
            workflow_name = metadata["workflowName"]

            if SystemTestDownload.is_systemtest_workflow(metadata):
                for filename, filepath in metadata["ouputs"].iteritems():
                    #TO-DO: Download the files
                    pass