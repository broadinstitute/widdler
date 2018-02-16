__author__ = "Amr Abouelleil"
from google.cloud import storage
import google.cloud.exceptions as ge
import config as c
import logging
import sys
import os

sb_logger = logging.getLogger('widdler.Bucket.Bucket')


class SingleBucket:
    """
    Class wrapping Google Cloud API interactions with a single Google Cloud Storage Bucket. Lots of inspiration from:
    https://github.com/GoogleCloudPlatform/python-docs-samples/blob/master/storage/cloud-client/snippets.py
    """
    def __init__(self, bucket_name):
        self.client = storage.Client.from_service_account_json(c.service_account_json)
        self.bucket = self._get_bucket(bucket_name)

    def _get_bucket(self, bucket_name):
        """
        Get a pre-existing bucket.
        :param bucket_name: Name of the bucket to get.
        :return: A Google bucket object.
        """
        try:
            return self.client.get_bucket(bucket_name)
        except ge.NotFound:
            ("Sorry, bucket {} does not exist!".format(bucket_name))
        except ge.Forbidden:
            print_log_exit("You do not have permissions for the bucket {}".format(bucket_name))
        except Exception as e:
            print_log_exit(str(e))

    def delete_bucket(self):
        """
        Deletes the bucket. Bucket must be empty.
        :return:
        """

        try:
            self.bucket.delete()
        except ge.NotFound:
            print_log_exit("Sorry, bucket {} does not exist!".format(self.bucket.name))
        except ge.Conflict as e:
            print_log_exit(
                str(e).replace(
                    "The bucket", "Bucket {} is not empty. Can't delete.".format(self.bucket.name)
                )
            )
        except Exception as e:
            print_log_exit(str(e))

    def download_blob(self, source_blob_name, destination_file_name):
        """
        Download a block from the bucket.
        :param source_blob_name:
        :param destination_file_name:
        :return:
        """
        blob = self.bucket.blob(source_blob_name)
        try:
            blob.download_to_filename(destination_file_name)
        except Exception as e:
            print_log_exit(msg=str(e), sys_exit=False)

    def download_blobs(self, destination_path):
        """
        Given a Google Bucket, download it's contents (called blobs, but basically files).
        :param destination_path: Directory to download files to.
        :return:
        """
        for blob in self.bucket.list_blobs():
            self.download_blob(blob.name, "{}/{}".format(destination_path, blob.name))

    def upload_file(self, source_file_name, destination_blob_name):
        """
        Upload a file to a bucket. Once they are in the bucket, they are called blobs.
        :param source_file_name: Full path and name of source file.
        :param destination_blob_name: name to give file in bucket.
        :return:
        """
        blob = self.bucket.blob(destination_blob_name)

        try:
            blob.upload_from_filename(source_file_name)
        except Exception as e:
            print_log_exit(str(e))

    def upload_files(self, source_files):
        """
        Upload multiple files.
        :param source_files: An array of files to upload to the bucket.
        :return:
        """
        for f in source_files:
            self.upload_file(f, os.path.basename(f))

    def delete_blob(self, blob_name):
        """
        Delete a blob from the bucket.
        :param blob_name:
        :return:
        """
        blob = self.bucket.blob(blob_name)
        try:
            blob.delete()
        except Exception as e:
            print_log_exit(str(e))

    def delete_blobs(self, blob_names):
        """
        Deletes an array of blobs.
        :param blob_names: A string of blob names.
        :return:
        """
        for n in blob_names:
            self.delete_blob(n)

    def rename_blob(self, blob_name, new_blob_name):
        try:
            blob = self.bucket.blob(blob_name)
            self.bucket.rename_blob(blob, new_blob_name)
        except Exception as e:
            print_log_exit(str(e))

    def list_blobs(self):
        """
        list the blobs in the bucket.
        :return:
        """
        try:
            return self.bucket.list_blobs()
        except Exception as e:
            print_log_exit(msg=e, sys_exit=False)


def list_buckets():
    """
    Get a collection of buckets accessible by authenticated user.
    :return: Iterator containing all buckets the authenticated user has access to.
    """
    try:
        client = storage.Client()
        return client.list_buckets()
    except Exception as e:
        print_log_exit(str(e))


def make_bucket(bucket_name):
    """
    Create a bucket. Should be used only
    :param bucket_name: Name of the bucket to create.
    :return: A Google bucket object.
    """
    try:
        client = storage.Client()
        return client.create_bucket(bucket_name=bucket_name)
    except ge.Conflict as e:
        print_log_exit(str(e).replace("this bucket", bucket_name))
    except Exception as e:
        print_log_exit(str(e))


def print_log_exit(msg, sys_exit=True, ple_logger=sb_logger):
    """
    Function for standard print/log/exit routine for fatal errors.
    :param msg: error message to print/log.
    :param sys_exit: Cause widdler to exit.
    :param ple_logger: Logger to use when logging message.
    :return:
    """
    print(msg)
    ple_logger.critical(msg)
    if sys_exit:
        sys.exit(1)
