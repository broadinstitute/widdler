import os
import sys

# Hosts that have a broadinstitute.org domain
bi_hosts = ['ale', 'ale1', 'btl-cromwell', 'gscid-cromwell']
# Hosts that don't
other_hosts = ['cloud', 'localhost']
servers = bi_hosts + other_hosts

resource_dir = os.path.abspath(os.path.dirname(__file__)).replace('src', 'resources')
run_states = ['Running', 'Submitted', 'QueuedInCromwell']
terminal_states = ['Failed', 'Aborted', 'Succeeded']
workflow_db = "workflow.db"

# localhost port
local_port = 8000

# cloud server IP address(es)
cloud_server = "35.193.85.62"
cloud_port = 8000

# service account used for bucket interactions
service_account_json = "{}/service_account.json".format(resource_dir)
default_bucket = 'broad-cil-devel-bucket'

# directory for generated temporary files (ex: for making fofns)

temp_dir = os.path.abspath(os.path.dirname(__file__)).replace('src', 'generated')


if sys.platform == 'win32':
    log_dir = os.path.abspath(os.path.dirname(__file__)).replace('src', 'logs')
else:
    log_dir = "/cil/shed/apps/internal/widdler/logs/"


