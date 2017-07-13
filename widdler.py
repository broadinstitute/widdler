#!/usr/bin/env python
import argparse
import sys
import widdler.config as c
from widdler.Cromwell import Cromwell

parser = argparse.ArgumentParser(
    description='Description: A tool for executing and monitoring WDLs to Cromwell instances.',
    usage='widdler.py <run | check> [<args>]',
    formatter_class=argparse.ArgumentDefaultsHelpFormatter)

sub = parser.add_subparsers()

run = sub.add_parser('run', 
                     description='Submit a WDL & JSON for execution on a Cromwell VM.',
                     usage='widdler.py run <wdl file> <json file> [<args>]',
                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)

run.add_argument('wdl', action='store', help='Path to the WDL to be executed.')
run.add_argument('json', action='store', help='Path the json inputs file.')
run.add_argument('-v', '--validate', action='store_true', default=True,
                 help='Validate WDL and JSON files before execution.')
run.add_argument('-s', '--server', action='store', required=True, type=str, choices=c.servers,
                 help='Choose a cromwell server from {}'.format(c.servers))

check = sub.add_parser('check',
                       description='Check the status of a submitted workflow.',
                       usage='widdler.py check <workflow id>',
                       formatter_class=argparse.ArgumentDefaultsHelpFormatter)
check.add_argument('workflow_id', action='store', help='workflow id for workflow execution of interest.')
check.add_argument('-s', '--server', action='store', required=True, type=str, choices=c.servers,
                 help='Choose a cromwell server from {}'.format(c.servers))

args_dict = vars(parser.parse_args())


def main():
    cromwell = Cromwell(host=args_dict['server'])
    if 'workflow_id' in args_dict:
        cromwell.query_status(args_dict['workflow_id'])
    else:
        pass

if __name__ == "__main__":
    sys.exit(main())

