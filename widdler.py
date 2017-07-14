#!/usr/bin/env python
import argparse
import sys
import os
import src.config as c
from src.Cromwell import Cromwell
import logging
import getpass


def call_run(args):
    cromwell = Cromwell(host=args.server)
    return cromwell.jstart_workflow(wdl_file=args.wdl, json_file=args.json)


def call_query(args):
    cromwell = Cromwell(host=args.server)
    queries = []
    if args.status:
        status = cromwell.query_status(args.workflow_id)
        queries.append(status)
    if args.metadata:
        metadata = cromwell.query_metadata(args.workflow_id)
        queries.append(metadata)
    if args.logs:
        logs = cromwell.query_logs(args.workflow_id)
        queries.append(logs)
    return queries


def call_abort(args):
    cromwell = Cromwell(host=args.server)
    return cromwell.stop_workflow(args.workflow_id)

parser = argparse.ArgumentParser(
    description='Description: A tool for executing and monitoring WDLs to Cromwell instances.',
    usage='widdler.py <run | query | abort> [<args>]',
    formatter_class=argparse.ArgumentDefaultsHelpFormatter)

sub = parser.add_subparsers()

run = sub.add_parser(name='run',
                     description='Submit a WDL & JSON for execution on a Cromwell VM.',
                     usage='widdler.py run <wdl file> <json file> [<args>]',
                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)

run.add_argument('wdl', action='store', help='Path to the WDL to be executed.')
run.add_argument('json', action='store', help='Path the json inputs file.')
run.add_argument('-v', '--validate', action='store_true', default=True,
                 help=argparse.SUPPRESS)
run.add_argument('-S', '--server', action='store', required=True, type=str, choices=c.servers,
                 help='Choose a cromwell server from {}'.format(c.servers))
run.set_defaults(func=call_run)

query = sub.add_parser(name='query',
                       description='Query cromwell for information on the submitted workflow.',
                       usage='widdler.py query <workflow id> [<args>]',
                       formatter_class=argparse.ArgumentDefaultsHelpFormatter)
query.add_argument('workflow_id', action='store', help='workflow id for workflow execution of interest.')
query.add_argument('-s', '--status', action='store_true', default=False, help='Print status for workflow to stdout')
query.add_argument('-m', '--metadata', action='store_true', default=False, help='Print metadata for workflow to stdout')
query.add_argument('-l', '--logs', action='store_true', default=False, help='Print logs for workflow to stdout')
query.add_argument('-S', '--server', action='store', required=True, type=str, choices=c.servers,
                   help='Choose a cromwell server from {}'.format(c.servers))
query.set_defaults(func=call_query)

abort = sub.add_parser(name='abort',
                       description='Abort a submitted workflow.',
                       usage='widdler.py abort <workflow id>',
                       formatter_class=argparse.ArgumentDefaultsHelpFormatter)
abort.add_argument('workflow_id', action='store', help='workflow id of workflow to abort.')
abort.add_argument('-S', '--server', action='store', required=True, type=str, choices=c.servers,
                   help='Choose a cromwell server from {}'.format(c.servers))

abort.set_defaults(func=call_abort)

args = parser.parse_args()


def main():
    logger = logging.getLogger('widdler')
    logger.setLevel(logging.DEBUG)
    # create file handler which logs even debug messages
    fh = logging.FileHandler(os.path.join(c.log_dir, 'widdler.log'))
    fh.setLevel(logging.DEBUG)
    # create console handler with a higher log level
    ch = logging.StreamHandler()
    ch.setLevel(logging.ERROR)
    # create formatter and add it to the handlers
    user = getpass.getuser()
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    fh.setFormatter(formatter)
    ch.setFormatter(formatter)
    # add the handlers to the logger
    logger.addHandler(fh)
    logger.addHandler(ch)
    logger.info("\n-------------New Widdler Execution by {}-------------".format(user))
    logger.info("Parameters chosen: {}".format(vars(args)))
    result = args.func(args)
    logger.info("Result: {}".format(result))
    print(result)
    logger.info("\n-------------End Widdler Execution by {}-------------".format(user))

if __name__ == "__main__":
    sys.exit(main())

