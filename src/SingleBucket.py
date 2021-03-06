__author__ = "Amr Abouelleil"
from google.cloud import storage
import google.cloud.exceptions as ge
from Validator import Validator
import config as c
import logging
import sys
import os
import traceback

sb_logger = logging.getLogger('widdler.SingleBucket.SingleBucket')


class SingleBucket:
    """
    Class wrapping Google Cloud API interactions with a single Google Cloud Storage Bucket. Lots of inspiration from:
    https://github.com/GoogleCloudPlatform/python-docs-samples/blob/master/storage/cloud-client/snippets.py
    """
    def __init__(self, bucket_name):
        try:
            self.client = storage.Client()
        except EnvironmentError as e:
            msg = "{}\nHave you activated your Google Cloud Platform credentials in this environment?".format(str(e))
            print_log_exit(msg)
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
            print_log_exit("Sorry, bucket {} does not exist!".format(bucket_name))

        except ge.Forbidden as e:
            print_log_exit("You do not have permissions for the bucket {}:\n{}".format(bucket_name, str(e)))
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
            print("Downloading " + str(source_blob_name) +" to " + str(destination_file_name) + "...")
            blob.download_to_filename(destination_file_name)
        except Exception as e:
            print(traceback.format_exc())
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

        blob = self.bucket.blob("broad-file-inputs/" + destination_blob_name)

        try:
            blob.upload_from_filename(source_file_name)
        except Exception as e:
            traceback.print_exc()
            print_log_exit(str(e))

    def upload_files(self, source_files):
        """
        Upload multiple files.
        :param source_files: An array of files to upload to the bucket.
        :return:
        """
        for f in source_files:
            # Replaces windows path folder separators with unix style.
            if isinstance(f, list):
                for f2 in f:
                    self.upload_file(f2, f2.replace('\\', '/'))
            else:
                self.upload_file(f, f.replace('\\', '/'))

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

    def upload_workflow_input_files(self, wdl_file, json_file):
        """
        Given workflow inputs, parse them to determine which inputs are files or files containing file paths, and
        upload those files to the bucket specified by the SingleBucket instance.
        :param wdl_file: File containing workflow description. Used to determine which workflow inputs are files.
        :param json_file: JSON inputs to wdl. Contains actual paths to files.
        :return: A list of files that were uploaded.
        """
        v = Validator(wdl_file, json_file)
        # get all the wdl arguments and figure out which ones are file inputs, store them in an array.
        wdl_args = v.get_wdl_args()
        file_keys = {k: v for k, v in wdl_args.iteritems() if 'File' in v}.keys()
        json_dict = v.get_json()

        files_to_upload = list()
        for file_key in file_keys:
            # need to make sure that keys in wdl args but not json dict aren't processed as file keys.
            # also, need to skip gs urls since they are already uploaded.
            if file_key in json_dict.keys() and "gs://" not in json_dict[file_key]:
                if 'fofn' in file_key:
                    # get files listed in the fofn and add them to list of files to upload
                    files_to_upload.extend(get_files_from_fofn(json_dict[file_key]))
                    """
                    Next don't want to upload the original fofn because it won't have the 'gs://' prefix for the files in.
                    Therefore need to create a new fofn that has updated paths, and we add that to files_to_upload.
                    """
                    new_fofn = update_fofn(json_dict[file_key], self.bucket.name)
                    files_to_upload.append(new_fofn)
                else:
                    if isinstance(json_dict[file_key], list):
                        for f in json_dict[file_key]:
                            if "gs://" not in f:
                                files_to_upload.append(f)
                    elif isinstance(json_dict[file_key], dict):
                        file_dict = json_dict[file_key]

                        for k,v in file_dict.iteritems(): #assume all Map with File are Map[?,File]
                            if "gs://" not in v:
                                files_to_upload.append(v)
                    else:
                        files_to_upload.append(json_dict[file_key])

        self.upload_files(files_to_upload)

        return files_to_upload


def get_files_from_fofn(fofn):
    """
    A function for extracting files from a file containing paths to files.
    :param fofn: a file of file names that is white-space delimited.
    :return: A list of file paths extracted from the input fofn.
    """
    fh = open(fofn, 'r')
    files_to_upload = list()
    for fofn_row in fh:
        fofn_row_fields = fofn_row.split()
        for field in fofn_row_fields:
            if os.path.isfile(field):
                files_to_upload.append(field)
    fh.close()
    return files_to_upload


def make_gs_url(local_path, dest_bucket):
    import re
    if local_path.startswith("/"):
        local_path = local_path[1:]
    return re.sub(r'\\+', '/', 'gs://{}/{}/{}'.format(dest_bucket, c.inputs_root, local_path))


def update_fofn(fofn, bucket):
    new_fofn = "{}.cloud".format(fofn)
    old_fh = open(fofn, 'rb')
    new_fh = open(new_fofn, 'wb')
    for fofn_row in old_fh:
        cleaned_row = fofn_row.rstrip('\n')
        fofn_row_fields = cleaned_row.split()
        new_row = list()
        for field in fofn_row_fields:
            if os.path.isfile(field):
                import re
                new_row.append(make_gs_url(field, bucket))
            else:
                new_row.append(field.rstrip())
        if len(new_row) > 1:
            new_fh.write('\t'.join(new_row))
        else:
            new_fh.write(new_row[0])
        new_fh.write('\n')
    return new_fofn


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
