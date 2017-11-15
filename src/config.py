import os

servers = ['ale1', 'btl-cromwell', 'localhost', 'gscid-cromwell']
resource_dir = os.path.abspath(os.path.dirname(__file__)).replace('src', 'resources')
log_dir = os.path.abspath(os.path.dirname(__file__)).replace('src', 'logs')
run_states = ['Running', 'Submitted', 'QueuedInCromwell']