import unittest
import os
from src.SingleBucket import SingleBucket, make_bucket
import src.config as c


class BucketUnitTests(unittest.TestCase):
    @classmethod
    def setUpClass(self):
        self.f_array = ['a.txt', 'b.txt', 'c.txt']
        for f in self.f_array:
            open(f, 'a').close()

    @staticmethod
    def _make_test_bucket(name):
        make_bucket(name)
        bucket = SingleBucket(name)
        return bucket

    def test_make_bucket(self):
        """
        Making of bucket actually happens in setUpClass because I want to use the same bucket in my other test methods.
        Only way to do that is to guarantee that it is created on init, as test methods have non-deterministic order of
        execution.
        :return:
        """
        gotten_bucket = self._make_test_bucket('make_bucket_test')
        self.assertEqual(gotten_bucket.bucket.name, 'make_bucket_test')
        gotten_bucket.delete_bucket()

    def test_upload_to_bucket(self):
        bucket = self._make_test_bucket("upload_bucket_test")
        wdl = os.path.join(c.resource_dir, 'hello_world.wdl')
        json = os.path.join(c.resource_dir, 'hello.json')
        bucket.upload_workflow_input_files(wdl, json)
        blobs = list()
        for b in bucket.list_blobs():
            blobs.append(b.name)
        bucket.delete_blobs(blobs)
        bucket.delete_bucket()
        self.assertEqual(len(blobs), 5)

    @classmethod
    def tearDownClass(self):
        print("Done!")

