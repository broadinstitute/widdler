import os
import sys
from itertools import chain, imap

# Hosts that have a broadinstitute.org domain
bi_hosts = ['ale', 'ale1', 'btl-cromwell', 'gscid-cromwell']
# Hosts that don't
other_hosts = ['cloud', 'localhost', 'gscid-cloud']
# cloud only hosts
cloud_hosts = ['cloud', 'gscid-cloud']
servers = bi_hosts + other_hosts

resource_dir = os.path.abspath(os.path.dirname(__file__)).replace('src', 'resources')
run_states = ['Running', 'Submitted', 'QueuedInCromwell']
terminal_states = ['Failed', 'Aborted', 'Succeeded']

dirname = os.path.split(os.path.abspath(__file__))[0]
workflow_db = dirname + "/../../workflow.db"

# localhost port
local_port = 8000

# cloud servers IP address(es)
cloud_server = "35.193.85.62"
gscid_cloud_server = "35.184.36.201"
cloud_port = 8000

# bucket names
gscid_bucket = "4b66fc8a-tmp"
dev_bucket = "broad-cil-devel-bucket"
default_bucket = gscid_bucket
inputs_root = "broad-file-inputs"

# directory for generated temporary files (ex: for making fofns)

temp_dir = os.path.abspath(os.path.dirname(__file__)).replace('src', 'generated')


if sys.platform == 'win32':
    log_dir = os.path.abspath(os.path.dirname(__file__)).replace('src', 'logs')
else:
    log_dir = "/cil/shed/apps/internal/widdler/logs/"

# Exclude these json keys from being converted to GS URLs.
exclude_gspath_array = ["onprem_download_path"]


def gspathable(k):
    """
    Evaluate if a key is allowed to be converted to a GS path.
    :param k: The key to evaluate.
    :return: True if allowed, false if not.
    """
    for field in exclude_gspath_array:
        if field in k:
            return False

    return True

def flatmap(f, items):
    return chain.from_iterable(imap(f, items))

temp_test_dir = "/broad/hptmp"
