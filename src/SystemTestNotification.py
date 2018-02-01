from string import Template
import urllib2
import logging
import json
import requests

system_test_map = {
    'VesperWorkflow':
        'http://ale-staging1:8080/view/Vesper%20Testing/job/Vesper%20System%20Test/buildWithParameters?token=12345&handoff_dir=$handoff_directory&comparison_dir=$comparison_dir',
    'smartseq':
        'http://ale-staging1:8080/view/SMARTSeq%20Testing/job/SMARTSeq%20System%20Test/buildWithParameters?token=12345&output_dir=$output_dir&comparison_dir=$comparison_dir'
}

class SystemTestNotification(object):

    @staticmethod
    def get_field(key):
        splits = key.split(".")
        return splits[1] if len(splits) > 1 else splits[0]

    @staticmethod
    def encode_val(val):
        if isinstance(val, basestring):
            return urllib2.quote(val)
        else:
            return val

    def on_changed_workflow_status(self, workflow, metadata, host):
        if (workflow.status == "Failed" or workflow.status == "Succeeded" or workflow.status == "Aborted"):
            inputs = json.loads(metadata["submittedFiles"]["inputs"])
            inputs = dict( (SystemTestNotification.get_field(key),
                                SystemTestNotification.encode_val(value)) for key, value in inputs.iteritems() )
            workflow_name = metadata["workflowName"]


            if workflow_name in system_test_map and "system_test" in inputs:
                url_template = system_test_map[workflow_name]
                url = Template(url_template).substitute(inputs)
                urllib2.urlopen(url).read()
                logging.warn("Triggerring system test for: " + str(workflow))