__author__ = 'paulcao, amr'
import logging
import json
import requests
import datetime
import sys
import getpass
from requests.utils import quote

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

    def get(self, rtype, workflow_id=None):
        """
        A generic get request function.
        :param rtype: a type of request such as 'abort' or 'status'.
        :param workflow_id: The ID of a workflow if get request requires one.
        :return: json of request response
        """
        if workflow_id:
            workflow_url = self.url + '/' + workflow_id + '/' + rtype
        else:
            workflow_url = self.url + '/' + rtype
        self.logger.info("GET REQUEST:{}".format(workflow_url))
        r = requests.get(workflow_url)
        return json.loads(r.text)

    def post(self, rtype, workflow_id=None):
        """
        A generic post request function.
        :param rtype: a type of request such as 'abort' or 'status'.
        :param workflow_id: The ID of a workflow if get request requires one.
        :return: json of request response
        """
        if workflow_id:
            workflow_url = self.url + '/' + workflow_id + '/' + rtype
        else:
            workflow_url = self.url + '/' + rtype
        self.logger.info("POST REQUEST:{}".format(workflow_url))
        r = requests.post(workflow_url)
        return json.loads(r.text)

    def start_workflow(self, wdl_file, workflow_name, workflow_args, dependencies=None):
        """
        Start a workflow using a dictionary of arguments.
        :param wdl_file: workflow description file.
        :param workflow_name: the name of the workflow (ex: gatk).
        :param workflow_args: A dictionary of workflow arguments.
        :param dependencies: The subworkflow zip file. Optional.
        :return: Request response json.
        """
        json_workflow_args = {}
        for key in workflow_args.keys():
            json_workflow_args[workflow_name + "." + key] = workflow_args[key]
        json_workflow_args['user'] = getpass.getuser()
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
        """
        Start a workflow using json file for argument inputs.
        :param wdl_file: Workflow description file.
        :param json_file: JSON file containing arguments.
        :param dependencies: The subworkflow zip file. Optional.
        :return: Request response json.
        """
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
        """
        Ends a running workflow.
        :param workflow_id: The workflow identifier.
        :return: Request response json.
        """
        self.logger.info('Aborting workflow {}'.format(workflow_id))
        return self.post('abort', workflow_id)

    def query_metadata(self, workflow_id):
        """
        Return all metadata for a given workflow.
        :param workflow_id: The workflow identifier.
        :return: Request Response json.
        """
        self.logger.info('Querying metadata for workflow {}'.format(workflow_id))
        return self.get('metadata', workflow_id)

    def query_status(self, workflow_id):
        """
        Return the status for a given workflow.
        :param workflow_id: The workflow identifier.
        :return: Request Response json.
        """
        self.logger.info('Querying status for workflow {}'.format(workflow_id))
        return self.get('status', workflow_id)

    def query_logs(self, workflow_id):
        """
        Return the task execution logs for a given workflow.
        :param workflow_id: The workflow identifier.
        :return: Request Response json.
        """
        self.logger.info('Querying logs for workflow {}'.format(workflow_id))
        return self.get('logs', workflow_id)

    def query_outputs(self, workflow_id):
        """
        Return the outputs for a given workflow.
        :param workflow_id: The workflow identifier.
        :return: Request Response json.
        """
        self.logger.info('Querying logs for workflow {}'.format(workflow_id))
        return self.get('outputs', workflow_id)

    def query(self, query_dict):
        """
        A function for performing a qet query given a dictionary of query terms.
        :param query_dict: Dictionary of query terms.
        :return:
        """
        base_url = self.url + '/query?'
        query_url = self.build_query_url(base_url, query_dict)
        self.logger.info("QUERY REQUEST:{}".format(query_url))
        r = requests.get(query_url)
        return json.dumps(r.text)

    @staticmethod
    def build_query_url(base_url, url_dict):
        """
        A function for building a query URL given a dictionary of key/value pairs to query.
        :param base_url: The base query URL (ex:http://btl-cromwell:9000/api/workflows/v1/query?)
        :param url_dict: Dictionary of query terms.
        :return: Returns the full query URL.
        """
        first = True
        url_string = ''
        for key, value in url_dict.items():
            if not first:
                url_string += '&'
            if isinstance(value, datetime.datetime):
                dt = quote(str(value)) + 'Z'
                value = dt.replace('%20', 'T')
            if isinstance(value, list):
                for item in value:
                    url_string += '{}={}'.format(key, item)
            else:
                url_string += '{}={}'.format(key, value)
            first = False
        return base_url.rstrip() + url_string

    def query_backend(self):
        return self.get('backends')
