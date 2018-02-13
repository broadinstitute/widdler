import unittest
from src.Bucket import Bucket


class BucketUnitTests(unittest.TestCase):
    @classmethod
    def setUpClass(self):
        self.bucket_name = "widdler_test_bucket"
        self.cs = Bucket()
        self.bucket = self.cs.make_bucket(self.bucket_name)

    def test_make_bucket(self):
        self.assertEqual(self.bucket_name, self.bucket.name)

    def test_get_bucket(self):
        self.cs.get_bucket(self.bucket_name)

    def test_upload_to_bucket(self):
        pass

    def test_list_buckets(self):
        pass

    def test_download_bucket_contents(self):
        pass

    @classmethod
    def tearDownClass(self):
        self.bucket.delete()


if __name__ == '__main__':
    unittest.main()
