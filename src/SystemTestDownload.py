from string import Template
import urllib2
import logging
import json

import re
from src.SingleBucket import SingleBucket, make_bucket, list_buckets
from config import flatmap, temp_test_dir
import uuid
import os
import urllib2

system_test_map = {
 'gatk_indexref': 'http://ale-staging1:8080/job/gatk_indexref_test/buildWithParameters?token=12345&comparison_dir='
}


class SystemTestDownload(object):

    def __init__(self):
        self.bucket = SingleBucket("broad-cil-devel-bucket")

    @staticmethod
    def is_systemtest_workflow(metadata):
        if "labels" in metadata:
            labels = metadata["labels"]
            return "system-test" in labels
        return False

    @staticmethod
    def truncate_gs_prefix(path):
        return "/".join(path.split("/")[3:])

    def download_file(self, remote_path, local_dir):
        filename = remote_path.split("/")[-1]
        local_path = local_dir + "/" + filename
        truncated_remote_path = SystemTestDownload.truncate_gs_prefix(remote_path)

        self.bucket.download_blob(truncated_remote_path, local_path)

    def on_changed_workflow_status(self, workflow, metadata, host):
        if SystemTestDownload.is_systemtest_workflow(metadata):
            system_test_url = system_test_map[metadata["workflowName"]]

            if workflow.status == "Succeeded" and SystemTestDownload.is_systemtest_workflow(metadata):
                temporary_dir = temp_test_dir + "/" +str(uuid.uuid4())
                os.makedirs(temporary_dir)

                outputs = list(flatmap(lambda o: o if isinstance(o, list) else [o], metadata["outputs"].values()))
                [self.download_file(remote, temporary_dir) for remote in outputs]

                system_test_url = system_test_url + temporary_dir

                print(system_test_url)
		urllib2.urlopen(system_test_url).read()
                logging.warn("Triggerring system test for succeeded workflow: " + str(workflow))

            elif workflow.status == "Failed":
                system_test_url = system_test_url + "FailedRun"

                urllib2.urlopen(system_test_url).read()
                logging.warn("Triggerring system test for failed workflow: " + str(workflow))
