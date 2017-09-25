#!/usr/bin/env python
"""
Widdler is a tool for submitting workflows via command-line to the cromwell execution engine servers. For more
info, visit https://github.com/broadinstitute/widdler/blob/master/README.md.
"""
import argparse
import sys
import os
import src.config as c
from src.Cromwell import Cromwell
from src.Monitor import Monitor
from src.Validator import Validator
import logging
import getpass
import json
import zipfile
import pprint
import time
import pytz
import datetime

__author__ = "Amr Abouelleil, Paul Cao"
__copyright__ = "Copyright 2017, The Broad Institute"
__credits__ = ["Amr Abouelleil", "Paul Cao", "Jean Chang"]
__license__ = "GPL"
__version__ = "1.3.4"
__maintainer__ = "Amr Abouelleil"
__email__ = "amr@broadinstitute.org"
__status__ = "Production"

# Logging setup
logger = logging.getLogger('widdler')
logger.setLevel(logging.DEBUG)
# create file handler which logs even debug messages
fh = logging.FileHandler(os.path.join(c.log_dir, '{}.widdler.log'.format(str(time.time()))))
fh.setLevel(logging.DEBUG)
# create console handler with a higher log level
ch = logging.StreamHandler()
ch.setLevel(logging.ERROR)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
fh.setFormatter(formatter)
ch.setFormatter(formatter)
# add the handlers to the logger
logger.addHandler(fh)
logger.addHandler(ch)


def is_valid(path):
    """
    Integrates with ArgParse to validate a file path.
    :param path: Path to a file.
    :return: The path if it exists, otherwise raises an error.
    """
    if not os.path.exists(path):
        raise argparse.ArgumentTypeError(("{} is not a valid file path.\n".format(path)))
    else:
        return path


def is_valid_zip(path):
    """
    Integrates with argparse to validate a file path and verify that the file is a zip file.
    :param path: Path to a file.
    :return: The path if it exists and is a zip file, otherwise raises an error.
    """
    is_valid(path)
    if not zipfile.is_zipfile(path):
        e = "{} is not a valid zip file.\n".format(path)
        logger.error(e)
        raise argparse.ArgumentTypeError(e)
    else:
        return path


def call_run(args):
    """
    Optionally validates inputs and starts a workflow on the Cromwell execution engine if validation passes. Validator
    returns an empty list if valid, otherwise, a list of errors discovered.
    :param args: run subparser arguments.
    :return: JSON response with Cromwell workflow ID.
    """
    if args.validate:
        call_validate(args)
    cromwell = Cromwell(host=args.server)
    result = cromwell.jstart_workflow(wdl_file=args.wdl, json_file=args.json, dependencies=args.dependencies)
    print("-------------Cromwell Links-------------")
    links = get_cromwell_links(args.server, result['id'], cromwell.port)
    print (links['metadata'])
    print (links['timing'])
    logger.info("Metadata:{}".format(links['metadata']))
    logger.info("Timing Graph:{}".format(links['timing']))
    print ("These will also be e-mailed to you when the workflow completes.")
    cromwell.label_workflow(result['id'], {'username': getpass.getuser()})
    if args.monitor:
        time.sleep(2)
        retry = 4
        while retry != 0:
            try:
                args.workflow_id = result['id']
                call_monitor(args)
                break
            except KeyError as e:
                logger.debug(e)
                retry = retry - 1
    return result


def call_query(args):
    """
    Get various types of data on a particular workflow ID.
    :param args:  query subparser arguments.
    :return: A list of json responses based on queries selected by the user.
    """
    cromwell = Cromwell(host=args.server)
    responses = []

    if args.workflow_id == None or args.workflow_id == "None":
        return call_list(args)

    if args.status:
        logger.info("Status requested.")
        status = cromwell.query_status(args.workflow_id)
        responses.append(status)
    if args.metadata:
        logger.info("Metadata requested.")
        metadata = cromwell.query_metadata(args.workflow_id)
        responses.append(metadata)
    if args.logs:
        logger.info("Logs requested.")
        logs = cromwell.query_logs(args.workflow_id)
        responses.append(logs)
    logger.debug("Query Results:\n" + str(responses))
    return responses


def call_validate(args):
    logger.info("Validation requested.")
    validator = Validator(wdl=args.wdl, json=args.json)
    result = validator.validate_json()
    if len(result) != 0:
        e = "{} input file contains the following errors:\n{}".format(args.json, "\n".join(result))
        # This will also print to stdout so no need for a print statement
        logger.critical(e)
        sys.exit(-1)
    else:
        s = 'No errors found in {}'.format(args.wdl)
        print(s)
        logger.info(s)


def call_abort(args):
    """
    Abort a workflow with a given workflow id.
    :param args: abort subparser args.
    :return: JSON containing abort response.
    """
    cromwell = Cromwell(host=args.server)
    logger.info("Abort requested")
    return cromwell.stop_workflow(workflow_id=args.workflow_id)


def call_monitor(args):
    logger.info("Monitoring requested")
    print("-------------Monitoring Workflow-------------")
    m = Monitor(host=args.server, user=args.username, no_notify=args.no_notify, verbose=args.verbose,
                interval=args.interval)
    if args.workflow_id:
        m.monitor_workflow(workflow_id=args.workflow_id)
    else:
        m.monitor_user_workflows()


def call_restart(args):
    logger.info("Restart requested")
    cromwell = Cromwell(host=args.server)
    result = cromwell.restart_workflow(workflow_id=args.workflow_id, disable_caching=args.disable_caching)

    if result is not None and "id" in result:
        msg = "Workflow restarted successfully; new workflow-id: " + str(result['id'])
        print(msg)
        logger.info(msg)
        cromwell.label_workflow(result['id'], {'username': getpass.getuser()})
    else:
        msg = "Workflow was not restarted successfully; server response: " + str(result)
        print(msg)
        logger.critical(msg)


def get_cromwell_links(server, workflow_id, port):
    return {'metadata': 'http://{}:{}/api/workflows/v1/{}/metadata'.format(server, port, workflow_id),
            'timing': 'http://{}:{}/api/workflows/v1/{}/timing'.format(server, port, workflow_id)}


def call_explain(args):
    logger.info("Explain requested")
    cromwell = Cromwell(host=args.server)
    (result, additional_res, stdout_res) = cromwell.explain_workflow(workflow_id=args.workflow_id,
                                                                     include_inputs=args.input)

    def my_safe_repr(object, context, maxlevels, level):
        typ = pprint._type(object)
        if typ is unicode:
            object = str(object)
        return pprint._safe_repr(object, context, maxlevels, level)

    printer = pprint.PrettyPrinter()
    printer.format = my_safe_repr
    if result is not None:
        print("-------------Workflow Status-------------")
        printer.pprint(result)

        if len(additional_res) > 0:
            print("-------------Additional Parameters-------------")
            printer.pprint(additional_res)

        if len(stdout_res) > 0:
            for log in stdout_res["failed_jobs"]:
                print("-------------Failed Stdout-------------")
                print (log["stdout"]["name"] + ":")
                print (log["stdout"]["log"])
                print ("-------------Failed Stderr-------------")
                print (log["stderr"]["name"] + ":")
                print (log["stderr"]["log"])

        print("-------------Cromwell Links-------------")
        links = get_cromwell_links(args.server, result['id'], cromwell.port)
        print (links['metadata'])
        print (links['timing'])

    else:
        print("Workflow not found.")

    args.monitor = True
    return None


def call_list(args):
    username = "*" if args.all else args.username
    m = Monitor(host=args.server, user=username, no_notify=True, verbose=True,
                interval=None, status_filter=args.filter)

    def get_iso_date(dt):
        tz = pytz.timezone("US/Eastern")
        return tz.localize(dt).isoformat()

    def process_job(job):
        links = get_cromwell_links(args.server, job['id'], m.cromwell.port)
        job['metadata'] = links['metadata']
        job['timing'] = links['timing']
        return job

    def my_safe_repr(object, context, maxlevels, level):
        typ = pprint._type(object)
        if typ is unicode:
            object = str(object)
        return pprint._safe_repr(object, context, maxlevels, level)

    start_date_str = get_iso_date(datetime.datetime.now() - datetime.timedelta(days=int(args.days)))
    result = m.get_user_workflows(raw=True, start_time=start_date_str)["results"]

    result = map(lambda j:process_job(j), result)
    printer = pprint.PrettyPrinter()
    printer.format = my_safe_repr
    printer.pprint(result)

    args.monitor = True
    return None


def call_label(args):
    cromwell = Cromwell(host=args.server)
    # cromwell.label_workflow(args.workflow_id)
    labels_dict = dict()
    for label in args.label:
        (key, val) = label.split(':')
        labels_dict[key] = val
    response = cromwell.label_workflow(args.workflow_id, labels=labels_dict)
    print(response)


parser = argparse.ArgumentParser(
    description='Description: A tool for executing and monitoring WDLs to Cromwell instances.',
    usage='widdler.py <run | monitor | query | abort | validate |restart | explain | label> [<args>]',
    formatter_class=argparse.ArgumentDefaultsHelpFormatter)

sub = parser.add_subparsers()
restart = sub.add_parser(name='restart',
                         description='Restart a submitted workflow.',
                         usage='widdler.py restart <workflow id>',
                         formatter_class=argparse.ArgumentDefaultsHelpFormatter)
restart.add_argument('workflow_id', action='store', help='workflow id of workflow to restart.')
restart.add_argument('-S', '--server', action='store', required=True, type=str, choices=c.servers,
                     help='Choose a cromwell server from {}'.format(c.servers))
restart.add_argument('-M', '--monitor', action='store_true', default=True, help=argparse.SUPPRESS)
restart.add_argument('-D', '--disable_caching', action='store_true', default=False, help=argparse.SUPPRESS)
restart.set_defaults(func=call_restart)

explain = sub.add_parser(name='explain',
                         description='Explain the status of a workflow.',
                         usage='widdler.py explain <workflowid>',
                         formatter_class=argparse.ArgumentDefaultsHelpFormatter)
explain.add_argument('workflow_id', action='store', help='workflow id of workflow to abort.')
explain.add_argument('-S', '--server', action='store', required=True, type=str, choices=c.servers,
                     help='Choose a cromwell server from {}'.format(c.servers))
explain.add_argument('-I', '--input', action='store_true', default=False, help=argparse.SUPPRESS)
explain.add_argument('-M', '--monitor', action='store_false', default=False, help=argparse.SUPPRESS)
explain.set_defaults(func=call_explain)

abort = sub.add_parser(name='abort',
                       description='Abort a submitted workflow.',
                       usage='widdler.py abort <workflow id>',
                       formatter_class=argparse.ArgumentDefaultsHelpFormatter)
abort.add_argument('workflow_id', action='store', help='workflow id of workflow to abort.')
abort.add_argument('-S', '--server', action='store', required=True, type=str, choices=c.servers,
                   help='Choose a cromwell server from {}'.format(c.servers))
abort.add_argument('-M', '--monitor', action='store_false', default=False, help=argparse.SUPPRESS)

abort.set_defaults(func=call_abort)

monitor = sub.add_parser(name='monitor',
                         description='Monitor a particular workflow and notify user via e-mail upon completion. If a'
                                     'workflow ID is not provided, user-level monitoring is assumed.',
                         usage='widdler.py monitor <workflow_id> [<args>]',
                         formatter_class=argparse.ArgumentDefaultsHelpFormatter)
monitor.add_argument('workflow_id', action='store', nargs='?',
                     help='workflow id for workflow to monitor. Do not specify if user-level monitoring is desired.')
monitor.add_argument('-u', '--username', action='store', default=getpass.getuser(),
                     help='Owner of workflows to monitor.')
monitor.add_argument('-i', '--interval', action='store', default=30, type=int,
                     help='Amount of time in seconds to elapse between status checks.')
monitor.add_argument('-V', '--verbose', action='store_true', default=False,
                     help='When selected, widdler will write the current status to STDOUT until completion.')
monitor.add_argument('-n', '--no_notify', action='store_true', default=False,
                     help='When selected, disable widdler e-mail notification of workflow completion.')
monitor.add_argument('-S', '--server', action='store', required=True, type=str, choices=c.servers,
                     help='Choose a cromwell server from {}'.format(c.servers))
monitor.add_argument('-M', '--monitor', action='store_true', default=True, help=argparse.SUPPRESS)
monitor.set_defaults(func=call_monitor)

query = sub.add_parser(name='query',
                       description='Query cromwell for information on the submitted workflow.',
                       usage='widdler.py query <workflow id> [<args>]',
                       formatter_class=argparse.ArgumentDefaultsHelpFormatter)
query.add_argument('workflow_id', nargs='?', default="None", help='workflow id for workflow execution of interest.')
query.add_argument('-s', '--status', action='store_true', default=False, help='Print status for workflow to stdout')
query.add_argument('-m', '--metadata', action='store_true', default=False, help='Print metadata for workflow to stdout')
query.add_argument('-l', '--logs', action='store_true', default=False, help='Print logs for workflow to stdout')
query.add_argument('-u', '--username', action='store', default=getpass.getuser(),help='Owner of workflows to monitor.')
query.add_argument('-d', '--days', action='store', default=7, help='Last n days to query.')
query.add_argument('-S', '--server', action='store', required=True, type=str, choices=c.servers,
                   help='Choose a cromwell server from {}'.format(c.servers))
query.add_argument('-f', '--filter', action='append', type=str, choices=c.run_states + c.terminal_states,
                   help='Filter by a workflow status from those listed above. May be specified more than once.')
query.add_argument('-a', '--all', action='store_true', default=False, help='Query for all users.')
query.add_argument('-M', '--monitor', action='store_false', default=False, help=argparse.SUPPRESS)

query.set_defaults(func=call_query)

run = sub.add_parser(name='run',
                     description='Submit a WDL & JSON for execution on a Cromwell VM.',
                     usage='widdler.py run <wdl file> <json file> [<args>]',
                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)

run.add_argument('wdl', action='store', type=is_valid, help='Path to the WDL to be executed.')
run.add_argument('json', action='store', type=is_valid, help='Path the json inputs file.')
run.add_argument('-v', '--validate', action='store_true', default=False,
                 help='Validate WDL inputs in json file.')
run.add_argument('-m', '--monitor', action='store_true', default=False,
                 help='Monitor the workflow and receive an e-mail notification when it terminates.')
run.add_argument('-i', '--interval', action='store', default=30, type=int,
                 help='If --monitor is selected, the amount of time in seconds to elapse between status checks.')
run.add_argument('-V', '--verbose', action='store_true', default=False,
                 help='If selected, widdler will write the current status to STDOUT until completion while monitoring.')
run.add_argument('-n', '--no_notify', action='store_true', default=False,
                     help='When selected, disable widdler e-mail notification of workflow completion.')
run.add_argument('-d', '--dependencies', action='store', default=None, type=is_valid_zip,
                 help='A zip file containing one or more WDL files that the main WDL imports.')
run.add_argument('-S', '--server', action='store', required=True, type=str, choices=c.servers,
                 help='Choose a cromwell server from {}'.format(c.servers))
run.add_argument('-l', '--label', action='append', help='A key:value pair to assign. May be used multiple times.')
run.add_argument('-u', '--username', action='store', default=getpass.getuser(), help=argparse.SUPPRESS)
run.add_argument('-w', '--workflow_id', help=argparse.SUPPRESS)
run.set_defaults(func=call_run)

validate = sub.add_parser(name='validate',
                          description='Validate (but do not run) a json for a specific WDL file.',
                          usage='widdler.py validate <wdl_file> <json_file>',
                          formatter_class=argparse.ArgumentDefaultsHelpFormatter)
validate.add_argument('wdl', action='store', type=is_valid, help='Path to the WDL associated with the json file.')
validate.add_argument('json', action='store', type=is_valid, help='Path the json inputs file to validate.')
validate.add_argument('-M', '--monitor', action='store_false', default=False, help=argparse.SUPPRESS)
validate.set_defaults(func=call_validate)

label = sub.add_parser(name='label',
                       description='Label a specific workflow with one or more key/value pairs.',
                       usage='widdler.py label <workflow_id> [<args>]',
                       formatter_class=argparse.ArgumentDefaultsHelpFormatter)
label.add_argument('workflow_id', nargs='?', default="None", help='workflow id for workflow to label.')
label.add_argument('-S', '--server', action='store', required=True, type=str, choices=c.servers,
                   help='Choose a cromwell server from {}'.format(c.servers))
label.add_argument('-l', '--label', action='append', help='A key:value pair to assign. May be used multiple times.')
label.add_argument('-M', '--monitor', action='store_false', default=False, help=argparse.SUPPRESS)

label.set_defaults(func=call_label)

args = parser.parse_args()


def main():
    user = getpass.getuser()
    logger.info("\n-------------New Widdler Execution by {}-------------".format(user))
    logger.info("Parameters chosen: {}".format(vars(args)))
    result = args.func(args)
    logger.info("Result: {}".format(result))
    if not args.monitor:
        print(json.dumps(result, indent=4))
    logger.info("\n-------------End Widdler Execution by {}-------------".format(user))

if __name__ == "__main__":
    sys.exit(main())

