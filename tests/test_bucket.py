import unittest
import os
import logging
from src.SingleBucket import SingleBucket, make_bucket, list_buckets
import src.config as c

# Logger setup
sb_logger = logging.getLogger('widdler.tests.test_bucket')
hdlr = logging.FileHandler(os.path.join(c.log_dir, 'test_cromwell.log'))
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
hdlr.setFormatter(formatter)
sb_logger.addHandler(hdlr)
sb_logger.setLevel(logging.INFO)


class BucketUnitTests(unittest.TestCase):
    @classmethod
    def setUpClass(self):
        self.b_name = 'widdler-test-bucket'
        make_bucket(self.b_name)
        self.single_bucket = SingleBucket(self.b_name)
        self.f_array = ['a.txt', 'b.txt', 'c.txt']
        for f in self.f_array:
            open(f, 'a').close()

    def test_make_bucket(self):
        """
        Making of bucket actually happens in setUpClass because I want to use the same bucket in my other test methods.
        Only way to do that is to guarantee that it is created on init, as test methods have non-deterministic order of
        execution.
        :return:
        """
        make_bucket('make_bucket_test')
        gotten_bucket = SingleBucket('make_bucket_test')
        self.assertEqual(gotten_bucket.bucket.name, 'make_bucket_test')
        gotten_bucket.delete_bucket()

    def test_get_bucket(self):
        """
        _getbucket is run as part of SingleBucket instantiation, and is normally not intended to be used outside of
        the class. Here, we just get another instance of the same bucket created in setUpClass.
        :return:
        """
        b = SingleBucket(self.b_name)
        self.assertEqual(b.bucket.name, self.b_name)

    def test_upload_download_delete_from_bucket(self):
        """
        Uses array of empty files to test upload, queries for files contained in bucket, and asserts that their names
        are in the array. Rename blobs in bucket, download renamed blobs, and assert the downloaded files have the
        new names.
        :return:
        """
        self.single_bucket.upload_files(self.f_array)
        blobs = self.single_bucket.list_blobs()
        for b in blobs:
            self.assertIn(b.name, self.f_array)
        renamed = list()
        for f in self.f_array:
            new_name = f.replace('.txt', '.csv')
            self.single_bucket.rename_blob(f, new_name)
            renamed.append(new_name)
        self.single_bucket.download_blobs(os.getcwd())
        cwd_contents = os.listdir(os.getcwd())
        for r in renamed:
            self.assertIn(r, cwd_contents)
        self.single_bucket.delete_blobs(renamed)
        self.assertEqual(len(list(self.single_bucket.list_blobs())), 0)

    def test_list_buckets(self):
        bucket_list = list()
        for b in list_buckets():
            bucket_list.append(b.name)
        self.assertIn(self.b_name, bucket_list)

    @classmethod
    def tearDownClass(self):
        self.single_bucket.bucket.delete()
        for f in self.f_array:
            os.remove(f)
            os.remove(f.replace('.txt', '.csv'))

