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
            onprem_dict_key = workflow_name + "." + "onprem_download_path"

            if onprem_dict_key not in metadata["inputs"]:
                return

            onprem_path = metadata["inputs"][onprem_dict_key]

            if onprem_dict_key in metadata["inputs"]:
                for key, item in metadata["outputs"].iteritems():
                    if isinstance(item, list):
                        for subpath in item:
                            base_fn = subpath.split("/")[-1]
                            local_path = onprem_path + "/" + base_fn
                            subpath = "/".join(subpath.split("/")[3:])
                            self.bucket.download_blob(subpath, local_path)
                    else:
                        base_fn = item.split("/")[-1]
                        local_path = onprem_path + "/" + base_fn
                        remote_path = "/".join(item.split("/")[3:])
                        self.bucket.download_blob(remote_path, local_path)

class GATKDownload(object):
    def __init__(self):
        self.bucket = SingleBucket("broad-cil-devel-bucket")

    def on_changed_workflow_status(self, workflow, metadata, host):
        if "workflowName" not in metadata.keys():
            return

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


