import unittest
import googleapiclient.discovery as gc
from google.cloud import storage
import config as c


class CloudUnitTests(unittest.TestCase):
    @classmethod
    def setUpClass(self):
        self.compute = gc.build('compute', 'v1')
        self.bucket = "cil-test-bucket"
        self.project = "broad-cil-devel"
        self.instance_name = "widdler-cloud-test"
        self.zone = "us-central1"
        self.storage_client = storage.Client.from_service_account_json(c.service_account_json)

    def test_list_instance(self):
        buckets = list(self.storage_client.list_buckets())
        print(buckets)
        self.assertEqual(True, False)

    @classmethod
    def tearDownClass(self):
        pass

if __name__ == '__main__':
    unittest.main()
