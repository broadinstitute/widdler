import os
import sys

servers = ['ale1', 'btl-cromwell', 'localhost', 'gscid-cromwell']
resource_dir = os.path.abspath(os.path.dirname(__file__)).replace('src', 'resources')
run_states = ['Running', 'Submitted', 'QueuedInCromwell']
terminal_states = ['Failed', 'Aborted', 'Succeeded']
if sys.platform == 'win32':
    log_dir = os.path.abspath(os.path.dirname(__file__)).replace('src', 'logs')
else:
    log_dir = "/cil/shed/apps/internal/widdler/logs/"


