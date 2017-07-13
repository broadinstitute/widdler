__author__ = 'paulcao'
import logging
import json
import requests

logging.basicConfig(level=logging.DEBUG)


class Cromwell:
    """ Module to interact with Cromwell Pipeline workflow manager. Example usage:
        cromwell = Cromwell()
        cromwell.start_workflow('VesperWorkflow', {'project_name': 'Vesper_Anid_test'})

        Generated json payload:
        {"VesperWorkflow.project_name":"Vesper_Anid_test"}
    """

    def __init__(self, host='btl-cromwell', port=9000):
        self.url = 'http://' + host + ':' + str(port) + '/api/workflows/v1'

    def start_workflow(self, wdl_file, workflow_name, workflow_args):

        json_workflow_args = {}
        for key in workflow_args.keys():
            json_workflow_args[workflow_name + "." + key] = workflow_args[key]

        args_string = json.dumps(json_workflow_args)

        print("args_string:")
        print(args_string)

        files = {'wdlSource': (wdl_file, open(wdl_file, 'rb'), 'application/octet-stream'),
                 'workflowInputs': ('report.csv', args_string, 'application/json')}

        r = requests.post(self.url, files=files)
        return json.loads(r.text)

    def query_status(self, workflow_id):
        workflow_url = self.url + "/" + workflow_id + "/metadata"
        r = requests.get(workflow_url)
        return json.loads(r.text)