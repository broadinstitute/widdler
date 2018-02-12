__author__ = 'Amr Abouelleil'

from Cromwell import Cromwell
import config as c
import unittest
import requests
import os
import logging
import time
import json


class CromwellCloudUnitTests(unittest.TestCase):
    @classmethod
    def setUp(self):
        resources = c.resource_dir
        self.logger = logging.getLogger('test_cromwell')
        hdlr = logging.FileHandler(os.path.join(c.log_dir, 'test_cromwell.log'))
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        hdlr.setFormatter(formatter)
        self.logger.addHandler(hdlr)
        self.logger.setLevel(logging.INFO)
        self.cromwell = Cromwell(c.cloud_server, 8000)
        self.json = os.path.join(resources, 'hello.json')
        self.wdl = os.path.join(resources, 'hello_world.wdl')
        self.logger.info('Resources: {}, {}'.format(self.wdl, self.json))
        self.wf = self.cromwell.jstart_workflow(self.wdl, self.json)
        self.logger.info('Workflow: {}'.format(self.wf))
        self.workflow_id = self.wf['id']
        self.labels = {'username': 'amr', 'foo': 'bar'}
        # Sleeping here to make sure workflow is started and has workflow ID otherwise tests can fail.
        time.sleep(5)

    def test_get_version(self):
        """
        Simple test to make sure the server is responding.
        :return:
        """
        result = requests.get("http://35.193.85.62:8000/engine/v1/version")
        self.assertEqual(result.status_code, 200)

    def test_begin_workflow(self):
        self.logger.info('Testing start_workflow...')
        self.assertTrue('id' in self.wf and 'status' in self.wf)
        self.assertEqual(self.wf['status'], 'Submitted')

    def test_query_status(self):
        self.logger.info('Testing query_status...')
        result = self.cromwell.query_status(self.workflow_id)
        self.logger.info('Result: {}'.format(result))
        self.assertTrue('id' in result and 'status' in result)

    def test_query_metadata(self):
        self.logger.info('Testing query_metadata...')
        result = self.cromwell.query_metadata(self.workflow_id)
        self.logger.info('Result: {}'.format(result))
        self.assertTrue('id' in result and 'submission' in result)

    def test_label_workflow(self):
        r = self.cromwell.label_workflow(self.workflow_id, self.labels)
        self.assertEquals(r.status_code, 200)

    @classmethod
    def tearDown(self):
        self.logger.info("Test done!")
