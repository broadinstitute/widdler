from string import Template
import urllib2
import logging
import json
from src.SingleBucket import SingleBucket, make_bucket, list_buckets

class Download(object):

    def __init__(self):
        self.bucket = SingleBucket("broad-cil-devel-bucket")

    def on_changed_workflow_status(self, workflow, metadata, host):
        if (workflow.status == "Succeeded"):
            workflow_name = metadata["workflowName"]

            handoff_dict_key = workflow_name + "." + "handoff_files"
            onprem_dict_key = workflow_name + "." + "onprem_download_path"

            if onprem_dict_key in metadata["inputs"] and \
                            handoff_dict_key in metadata["inputs"]:
                handoff_file_dict = metadata["inputs"][handoff_dict_key]
                onprem_path = metadata["inputs"][onprem_dict_key]

                for key,local_fn in handoff_file_dict.iteritems():
                    remote_path = metadata["outputs"][workflow_name + "." + key]

                    if isinstance(remote_path, list):
                        #local_path_prefix = ".".join(local_path.split(".")[:-1])
                        #local_path_extension = local_path.split(".")[-1]
                        #local_path = local_path_prefix + "-" + str(idx) + "." + local_path_extension


                        for idx, remote_sub_path in enumerate(remote_path):
                            curr_local_fn = local_fn if local_fn != "" else remote_sub_path.split("/")[-1]
                            local_path = onprem_path + "/" + curr_local_fn
                            remote_sub_path = "/".join(remote_sub_path.split("/")[3:])

                            self.bucket.download_blob(remote_sub_path, local_path)
                    else:
                        local_fn = local_fn if local_fn != "" else remote_path.split("/")[-1]
                        local_path = onprem_path + "/" + local_fn
                        remote_path = "/".join(remote_path.split("/")[3:])

                        self.bucket.download_blob(remote_path, local_path)