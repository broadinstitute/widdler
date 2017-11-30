import os
import sys

servers = ['ale', 'ale1', 'btl-cromwell', 'localhost', 'gscid-cromwell']
resource_dir = os.path.abspath(os.path.dirname(__file__)).replace('src', 'resources')

if sys.platform == 'win32':
    log_dir = os.path.abspath(os.path.dirname(__file__)).replace('src', 'logs')
else:
    log_dir = "/cil/shed/apps/internal/widdler/logs/"
run_states = ['Running', 'Submitted', 'QueuedInCromwell']
terminal_states = ['Failed', 'Aborted', 'Succeeded']

