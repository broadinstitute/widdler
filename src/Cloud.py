__author__ = "Amr Abouelleil"
from google.cloud import storage
import google.cloud.exceptions as ge
import logging
import sys


class Cloud:
    """
    Class wrapping Google Cloud API interactions with Google Cloud Storage Buckets.
    """
    def __init__(self):
        self.client = storage.Client()
        self.logger = logging.getLogger('widdler.cloud.Cloud')

    def print_log_exit(self, msg, exit=True):
        """
        Function for standard print/log/exit routine for fatal errors.
        :param msg: error message to print/log.
        :param exit: Cause widdler to exit.
        :return:
        """
        print(msg)
        self.logger.critical(msg)
        if exit:
            sys.exit(1)

    def make_bucket(self, bucket_name):
        """
        Create a bucket.
        :param bucket_name: Name of the bucket.
        :return: A Google bucket object.
        """
        try:
            return self.client.create_bucket(bucket_name=bucket_name)
        except ge.Conflict as e:
            self.print_log_exit(str(e).replace("this bucket", bucket_name))
        except Exception as e:
            self.print_log_exit(str(e))

    def get_bucket(self, bucket_name):
        """
        Get a pre-existing bucket.
        :param bucket_name: Name of the bucket to get.
        :return: A Google bucket object.
        """
        try:
            return self.client.get_bucket(bucket_name)
        except ge.NotFound:
            self.print_log_exit("Sorry, bucket {} does not exist!".format(bucket_name))
        except ge.Forbidden:
            self.print_log_exit("You do not have permissions for the bucket {}".format(bucket_name))
        except Exception as e:
            self.print_log_exit(str(e))

    def delete_bucket(self, bucket_name):
        """
        Deletes a bucket.
        :param bucket_name: Name of bucket to delete.
        :return:
        """
        bucket = self.get_bucket(bucket_name)
        try:
            bucket.delete()
        except ge.NotFound:
            self.print_log_exit("Sorry, bucket {} does not exist!".format(bucket_name))
        except ge.Conflict as e:
            self.print_log_exit(str(e)
                                .replace("The bucket", "Bucket {} is not empty. Can't delete.".format(bucket_name)))
        except Exception as e:
            self.print_log_exit(str(e))

    def download_bucket_contents(self, bucket, destination):
        """
        Given a Google Bucket, download it's contents.
        :param bucket: Bucket object.
        :param destination: Directory to download files to.
        :return:
        """
        for blob in bucket.list_blobs():
            try:
                blob.download_to_filename("{}/{}".format(destination, blob.name.replace(" ", "_")))
            except Exception as e:
                self.print_log_exit(str(e), exit=False)

    def list_buckets(self):
        """
        Get a collection of buckets.
        :return: Iterator containing all buckets the authenticated user has access to.
        """
        try:
            return self.client.list_buckets()
        except Exception as e:
            self.print_log_exit(str(e))
