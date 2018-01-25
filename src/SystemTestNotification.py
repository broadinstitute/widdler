from string import Template
import urllib2
import logging

class SystemTestNotification(object):

    def on_changed_workflow_status(self, workflow, metadata, host):
        if (workflow.status == "Failed" or workflow.status == "Succeeded" or workflow.status == "Aborted") \
                and "system_test_url_template" in metadata["input"]:
            
            url_template = metadata["input"]["system_test_url_template"]
            url = Template(url_template).substitute(metadata)
            urllib2.urlopen(url).read()

            logging.warn("Triggerring system test for: " + str(workflow))