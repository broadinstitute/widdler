#!/usr/bin/env python
import argparse
import sys
import os
import src.config as c
from src.Cromwell import Cromwell
import logging




def call_run(args):
    cromwell = Cromwell(host=args.server)
    return cromwell.jstart_workflow(wdl_file=args.wdl, json_file=args.json)


def call_query(args):
    cromwell = Cromwell(host=args.server)
    query = []
    if args.status:
        status = cromwell.query_status(args.workflow_id)
        query.append(status)
    if args.metadata:
        metadata = cromwell.query_metadata(args.workflow_id)
        query.append(metadata)
    if args.logs:
        logs = cromwell.query_logs(args.workflow_id)
        query.append(logs)
    return query


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
                 help='Validate WDL and JSON files before execution. On by default.')
run.add_argument('-S', '--server', action='store', required=True, type=str, choices=c.servers,
                 help='Choose a cromwell server from {}'.format(c.servers))
run.set_defaults(func=call_run)

query = sub.add_parser(name='query',
                       description='Check the status of a submitted workflow.',
                       usage='widdler.py query <workflow id>',
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
    logger = logging.getLogger('widdlier')
    logger.setLevel(logging.DEBUG)
    log_file = os.path.join(c.log_dir, 'widdler.log')
    fh = logging.FileHandler(log_file)
    fh.setLevel(logging.DEBUG)
    formatter = logging.Formatter('[%(asctime)s | %(name)s | %(levelname)s] %(message)s')
    fh.setFormatter(formatter)
    logger.addHandler(fh)
    logger.info("\n-------------New Widdler Execution-------------")
    logger.info("Parameters chosen: {}".format(vars(args)))
    result = args.func(args)
    print(result)
    logger.info("\n-------------End Widdler Execution-------------")

if __name__ == "__main__":
    sys.exit(main())

