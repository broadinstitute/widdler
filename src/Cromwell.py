__author__ = 'paulcao, amr'
import logging
import json
import requests
import datetime
import getpass
from requests.utils import quote
import urllib

module_logger = logging.getLogger('widdler.Cromwell')


class Cromwell:
    """ Module to interact with Cromwell Pipeline workflow manager. Example usage:
        cromwell = Cromwell()
        cromwell.start_workflow('VesperWorkflow', {'project_name': 'Vesper_Anid_test'})

        Generated json payload:
        {"VesperWorkflow.project_name":"Vesper_Anid_test"}
    """

    def __init__(self, host='btl-cromwell', port=9000):
        if host == 'localhost':
            self.port = 8000
        else:
            self.port = port
        self.url = 'http://' + host + ':' + str(self.port) + '/api/workflows/v1'
        self.logger = logging.getLogger('widdler.cromwell.Cromwell')
        self.logger.info('URL:{}'.format(self.url))

    def get(self, rtype, workflow_id=None, headers=None):
        """
        A generic get request function.
        :param rtype: a type of request such as 'abort' or 'status'.
        :param workflow_id: The ID of a workflow if get request requires one.
        :param headers: Optional headers for request.
        :return: json of request response
        """
        if workflow_id:
            workflow_url = self.url + '/' + workflow_id + '/' + rtype
        else:
            workflow_url = self.url + '/' + rtype
        self.logger.info("GET REQUEST:{}".format(workflow_url))
        if headers:
            r = requests.get(workflow_url, headers=headers)
        else:
            r = requests.get(workflow_url)
        return json.loads(r.content)

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

    def patch(self, rtype, workflow_id, payload, headers):
        workflow_url = self.url + '/' + workflow_id + '/' + rtype
        self.logger.info("POST REQUEST:{}".format(workflow_url))
        r = requests.patch(url=workflow_url, data=payload, headers=headers)
        return r

    def restart_workflow(self, workflow_id, disable_caching=False):
        """
        Restart a workflow given an existing workflow id.
        :param workflow_id: the id of the existing workflow
        :param disable_caching: If true, do not use cached data to restart the workflow.
        :return: Request response json.
        """
        metadata = self.query_metadata(workflow_id)

        try:
            workflow_input = metadata['submittedFiles']['inputs']
            wdl = metadata['submittedFiles']['workflow']
            self.logger.info('Workflow restarting with inputs: {}'.format(workflow_input))
            return self.jstart_workflow(wdl, workflow_input, wdl_string=True, disable_caching=disable_caching)
        except KeyError:
            return None

    @staticmethod
    def getCalls(status, call_arr, full_logs=False, limit_n=3):

        filteredCalls = list(filter(lambda c:c[0]['executionStatus'] == status, call_arr))
        filteredCalls = map(lambda c:c[0], filteredCalls)

        def parse_logs(call):
            log = {}
            try:
                log['stdout'] = {'name': call['stdout']}
            except KeyError as e:
                log['stddout'] = e
            try:
                log['stderr'] = {'name': call['stderr']}
            except KeyError as e:
                log['stderr'] = e
            if full_logs:
                try:
                    with open(call['stdout'], 'r') as stdout_in:
                        log['stdout']['log'] = stdout_in.read()
                except IOError as e:
                    log['stdout']['log'] = e
                try:
                    with open(call['stderr'], 'r') as stderr_in:
                        log["stderr"]['log'] = stderr_in.read()
                except IOError as e:
                    log["stderr"]['log'] = e
            return log

        return map(lambda c:parse_logs(c), filteredCalls[:limit_n])

    def explain_workflow(self, workflow_id, include_inputs=True):

        def assign(sdict, ddict, key):
            try:
                ddict[key] = sdict[key]
            except KeyError as e:
                ddict[key] = e
        result = self.query_metadata(workflow_id)
        explain_res = {}
        additional_res= {}
        stdout_res = {}

        if result != None:
            assign(result, explain_res, 'status')
            assign(result, explain_res, 'id')
            assign(result, explain_res, 'workflowRoot')
            if explain_res["status"] == "Failed":
                stdout_res["failed_jobs"] = Cromwell.getCalls('RetryableFailure', result['calls'].values(),
                                                              full_logs=True)

            elif explain_res["status"] == "Running":
                explain_res["running_jobs"] = Cromwell.getCalls('Running', result['calls'].values())

            if include_inputs:
                additional_res["inputs"] = result["inputs"]
        else:
            print("Workflow not found.")

        return (explain_res, additional_res, stdout_res)

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

    def jstart_workflow(self, wdl_file, json_file, dependencies=None, wdl_string=False, disable_caching=False):
        """
        Start a workflow using json file for argument inputs.
        :param wdl_file: Workflow description file or WDL string (specify wdl_string if so).
        :param json_file: JSON file or JSON string containing arguments.
        :param dependencies: The subworkflow zip file. Optional.
        :param wdl_string: If the wdl_file argument is actually a string. Optional.
        :return: Request response json.
        """

        if not json_file.startswith("{"):
            with open(json_file) as fh:
                args = json.load(fh)
            fh.close()
            args['user'] = getpass.getuser()
            j_args = json.dumps(args)
        else:
            j_args = json_file

        files = None
        if not wdl_string:
            files = {'wdlSource': (wdl_file, open(wdl_file, 'rb'), 'application/octet-stream'),
                 'workflowInputs': ('report.csv', j_args, 'application/json')}
        else:
            files = {'wdlSource': ('workflow.wdl', wdl_file, 'application/text-plain'),
                  'workflowInputs': ('report.csv', j_args, 'application/json')}
        if dependencies:
            # add dependency as zip file
            files['wdlDependencies'] = (dependencies, open(dependencies, 'rb'), 'application/zip')

        if disable_caching:
            files['workflowOptions'] = ('options.json', "{\"read_from_cache\":false}", 'application/json')
            print('disable_caching enabled')

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
        return self.get('metadata', workflow_id, {'Accept': 'application/json', 'Accept-Encoding': 'identity'})

    def label_workflow(self, workflow_id, labels):
        """
        A method for labeling a workflow with one more labels.
        :param workflow_id: Workflow ID to label.
        :param labels: A dictionary of labels.
        :return: JSON response
        """
        labels_json = json.dumps(labels)
        headers = {'Content-type': 'application/json', 'Accept': 'application/json'}
        return self.patch('labels', workflow_id, labels_json, headers)

    def query_labels(self, labels, start_time=None, status_filter=None):
        """
        Query cromwell database with a given set of labels.
        :param labels: A dictionary of label keys and values.
        :return: Query results.
        """
        label_dict = {}
        for k, v in labels.items():
            label_dict["label=" + k] = v
        time_query = "start=" + start_time if start_time != None else ""
        status_query = ""
        if status_filter:
            for status in status_filter:
                status_query += "status={}&".format(status)
        url = self.build_query_url(self.url + '/query?' + "&".join([time_query, status_query]), label_dict, ':')
        # In soem cases we can get a dangling & so this removed that.
        r = requests.get(url.rstrip('&'))
        return json.loads(r.content)

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
        :return: A dictionary of the json content.
        """
        base_url = self.url + '/query?'
        query_url = self.build_query_url(base_url, query_dict)
        self.logger.info("QUERY REQUEST:{}".format(query_url))
        r = requests.get(query_url)
        return json.loads(r.text)

    @staticmethod
    def build_query_url(base_url, url_dict, sep='='):
        """
        A function for building a query URL given a dictionary of key/value pairs to query.
        :param base_url: The base query URL (ex:http://btl-cromwell:9000/api/workflows/v1/query?)
        :param url_dict: Dictionary of query terms.
        :param sep: Seperator for query terms.
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
                    url_string += '{}{}{}'.format(key, sep, item)
            else:
                url_string += '{}{}{}'.format(key, sep, value)
            first = False
        return base_url.rstrip() + url_string

    def query_backend(self):
        return self.get('backends')
