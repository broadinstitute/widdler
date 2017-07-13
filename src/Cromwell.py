__author__ = 'paulcao'
import logging
import json
import urllib3
import requests


class Cromwell:
    """ Module to interact with Cromwell Pipeline workflow manager. Example usage:
        cromwell = Cromwell()
        cromwell.start_workflow('VesperWorkflow', {'project_name': 'Vesper_Anid_test'})

        Generated json payload:
        {"VesperWorkflow.project_name":"Vesper_Anid_test"}
    """

    def __init__(self, host='btl-cromwell', port=9000):
        self.url = 'http://' + host + ':' + str(port) + '/api/workflows/v1'
        self.logger = logging.getLogger('widdler.Cromwell.Cromwell')
        self.logger.info('URL:{}'.format(self.url))

    def get(self, workflow_id, action):
        workflow_url = self.url + '/' + workflow_id + '/' + action
        self.logger.debug("GET REQUEST:{}".format(workflow_url))
        r = requests.get(workflow_url)
        return json.loads(r.text)

    def post(self, workflow_id, action):
        workflow_url = self.url + '/' + workflow_id + '/' + action
        self.logger.debug("POST REQUEST:{}".format(workflow_url))
        r = requests.post(workflow_url)
        return json.loads(r.text)

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

    def jstart_workflow(self, wdl_file, json_file):
        with open(json_file) as fh:
            args = json.load(fh)
        fh.close()
        j_args = json.dumps(args)
        files = {'wdlSource': (wdl_file, open(wdl_file, 'rb'), 'application/octet-stream'),
                 'workflowInputs': ('report.csv', j_args, 'application/json')}
        r = requests.post(self.url, files=files)
        return json.loads(r.text)

    def stop_workflow(self, workflow_id):
        return self.post(workflow_id, 'abort')

    def query_metadata(self, workflow_id):
        return self.get(workflow_id, 'metadata')

    def query_status(self, workflow_id):
        return self.get(workflow_id, 'status')

    def query_logs(self, workflow_id):
        return self.get(workflow_id, 'logs')


