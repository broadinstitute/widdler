__author__ = 'paulcao, amr'
import logging
import json
import urllib3
import requests
import datetime
#from urllib import parse
import getpass

module_logger = logging.getLogger('widdler.Cromwell')


class Cromwell:
    """ Module to interact with Cromwell Pipeline workflow manager. Example usage:
        cromwell = Cromwell()
        cromwell.start_workflow('VesperWorkflow', {'project_name': 'Vesper_Anid_test'})

        Generated json payload:
        {"VesperWorkflow.project_name":"Vesper_Anid_test"}
    """

    def __init__(self, host='btl-cromwell', port=9000):
        self.url = 'http://' + host + ':' + str(port) + '/api/workflows/v1'
        self.logger = logging.getLogger('widdler.cromwell.Cromwell')
        self.logger.info('URL:{}'.format(self.url))

    def get(self, action, workflow_id=None):
        if workflow_id:
            workflow_url = self.url + '/' + workflow_id + '/' + action
        else:
            workflow_url = self.url + '/' + action
        self.logger.info("GET REQUEST:{}".format(workflow_url))
        r = requests.get(workflow_url)
        return json.loads(r.text)

    def post(self, workflow_id, action):
        if workflow_id:
            workflow_url = self.url + '/' + workflow_id + '/' + action
        else:
            workflow_url = self.url + '/' + action
        self.logger.info("POST REQUEST:{}".format(workflow_url))
        r = requests.post(workflow_url)
        return json.loads(r.text)

    def start_workflow(self, wdl_file, workflow_name, workflow_args, dependencies=None):

        json_workflow_args = {}
        for key in workflow_args.keys():
            json_workflow_args[workflow_name + "." + key] = workflow_args[key]

        args_string = json.dumps(json_workflow_args)

        print("args_string:")
        print(args_string)

        files = {'wdlSource': (wdl_file, open(wdl_file, 'rb'), 'application/octet-stream'),
                 'workflowInputs': ('report.csv', args_string, 'application/json')}
        if dependencies:
            # add dependency as zip file
            files['wdlDependencies'] = (dependencies, open(dependencies, 'rb'), 'application/zip')
        r = requests.post(self.url, files=files)
        return json.loads(r.text)

    def jstart_workflow(self, wdl_file, json_file,  dependencies=None):
        with open(json_file) as fh:
            args = json.load(fh)
        fh.close()
        args['user'] = getpass.getuser()
        j_args = json.dumps(args)
        files = {'wdlSource': (wdl_file, open(wdl_file, 'rb'), 'application/octet-stream'),
                 'workflowInputs': ('report.csv', j_args, 'application/json')}
        if dependencies:
            # add dependency as zip file
            files['wdlDependencies'] = (dependencies, open(dependencies, 'rb'), 'application/zip')
        r = requests.post(self.url, files=files)
        return json.loads(r.text)

    def stop_workflow(self, workflow_id):
        self.logger.info('Aborting workflow {}'.format(workflow_id))
        return self.post( 'abort', workflow_id)

    def query_metadata(self, workflow_id):
        self.logger.info('Querying metadata for workflow {}'.format(workflow_id))
        return self.get('metadata', workflow_id)

    def query_status(self, workflow_id):
        self.logger.info('Querying status for workflow {}'.format(workflow_id))
        return self.get( 'status', workflow_id)

    def query_logs(self, workflow_id):
        self.logger.info('Querying logs for workflow {}'.format(workflow_id))
        return self.get('logs', workflow_id)

    def query_outputs(self, workflow_id):
        self.logger.info('Querying logs for workflow {}'.format(workflow_id))
        return self.get('outputs', workflow_id)

    def build_query_url(self, base_url, url_dict):
        first = True
        for key, value in url_dict.items():
            if not first:
                base_url += '&'
            if isinstance(value, datetime.datetime):
                dt = value.strftime('%Y-%m-%dT%H%%3A%S%%3A%f')
                #test = parse.quote_plus(dt)
                #value = test
            if isinstance(value, list):
                for item in value:
                    base_url += '{}={}'.format(key, item)

            base_url += '{}={}'.format(key, value)
            first = False
        return base_url

    def query(self, query_dict):
        base_url = self.url + 'query?'
        self.build_long_query_url(base_url, query_dict)


