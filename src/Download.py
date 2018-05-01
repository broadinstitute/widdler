from string import Template
import urllib2
import logging
import json
from src.SingleBucket import SingleBucket, make_bucket, list_buckets
from config import flatmap

class Download(object):

    def __init__(self):
        self.bucket = SingleBucket("broad-cil-devel-bucket")

    @staticmethod
    def truncate_gs_prefix(path):
        return "/".join(path.split("/")[3:])

    def download_file(self, remote_path, local_dir):
        if local_dir == None:
            return

        filename = remote_path.split("/")[-1]
        local_path = local_dir + "/" + filename
        truncated_remote_path = Download.truncate_gs_prefix(remote_path)

        self.bucket.download_blob(truncated_remote_path, local_path)

    def on_changed_workflow_status(self, workflow, metadata, host):

        if (workflow.status == "Succeeded"):
            workflow_name = metadata["workflowName"]

            handoff_dict_key = workflow_name + "." + "handoff_files"
            onprem_dict_key = workflow_name + "." + "onprem_download_path"

            if handoff_dict_key in metadata["inputs"] and metadata["inputs"][handoff_dict_key] == None:
                onprem_path = metadata["inputs"][onprem_dict_key]
                outputs = list(flatmap(lambda o: o if isinstance(o, list) else [o], metadata["outputs"].values()))
                [self.download_file(remote, onprem_path) for remote in outputs]
            elif onprem_dict_key in metadata["inputs"] and handoff_dict_key in metadata["inputs"]:
                handoff_file_dict = metadata["inputs"][handoff_dict_key]
                onprem_path = metadata["inputs"][onprem_dict_key]

                for key,local_fn in handoff_file_dict.iteritems():
                    remote_path = metadata["outputs"][key]

                    if isinstance(remote_path, list):
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

class GATKDownload(object):
    def __init__(self):
        self.bucket = SingleBucket("broad-cil-devel-bucket")

    def on_changed_workflow_status(self, workflow, metadata, host):
        workflow_name = metadata["workflowName"]

        if workflow_name == "gatk_process_samples" and workflow.status == "Succeeded":
            onprem_dict_key = workflow_name + "." + "onprem_download_path"
            onprem_path = metadata["inputs"][onprem_dict_key]

            if onprem_path != None:
                cloud_vcf_fh = open(onprem_path + "/vcfs.out", "w")
                local_vcf_fh = open(onprem_path + "/local_vcfs.out", "w")
                files = metadata["outputs"]["gatk_process_samples.out_gvcf"]

                for file in files:
                    cloud_vcf_fh.write(file + "\n")
                    local_path = onprem_path + "/" + file.split("/")[-1]
                    local_vcf_fh.write(local_path + "\n")

                cloud_vcf_fh.close()
                local_vcf_fh.close()


