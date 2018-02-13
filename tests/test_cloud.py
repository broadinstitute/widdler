import unittest
import googleapiclient.discovery as gc
from google.cloud import storage
import config as c


class CloudUnitTests(unittest.TestCase):
    @classmethod
    def setUpClass(self):
        self.compute = gc.build('compute', 'v1')
        self.bucket = "widdler_test_bucket"
        self.project = "broad-cil-devel"
        self.instance_name = "widdler-cloud-test"
        self.zone = "us-central1"

    # def test_list_instance(self):
    #
    #     print(buckets)
    #     self.assertEqual(True, False)

    def test_create_bucket(self):
        storage_client = storage.Client()
        bucket = storage_client.create_bucket(self.bucket)
        print('Bucket {} created.'.format(bucket.name))
        self.assertEqual(str(bucket.name), self.bucket)


    @classmethod
    def tearDownClass(self):
        pass

if __name__ == '__main__':
    unittest.main()
