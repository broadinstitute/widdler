import os
import sys

servers = ['ale', 'ale1', 'btl-cromwell', 'localhost', 'gscid-cromwell']
resource_dir = os.path.abspath(os.path.dirname(__file__)).replace('src', 'resources')
run_states = ['Running', 'Submitted', 'QueuedInCromwell']
terminal_states = ['Failed', 'Aborted', 'Succeeded']
workflow_db = "workflow.db"
cloud_server = "35.193.85.62"
service_account_json = "{}/service_account.json".format(resource_dir)

if sys.platform == 'win32':
    log_dir = os.path.abspath(os.path.dirname(__file__)).replace('src', 'logs')
else:
    log_dir = "/cil/shed/apps/internal/widdler/logs/"


