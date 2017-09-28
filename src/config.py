import os
import sys

servers = ['ale', 'btl-cromwell', 'localhost', 'gscid-cromwell']
resource_dir = os.path.abspath(os.path.dirname(__file__)).replace('src', 'resources')

if sys.platform == 'win32':
    log_dir = os.path.abspath(os.path.dirname(__file__)).replace('src', 'logs')
else:
    log_dir = "/cil/shed/resources/widdler/logs/"
run_states = ['Running', 'Submitted', 'QueuedInCromwell']
terminal_states = ['Failed', 'Aborted', 'Succeeded']

