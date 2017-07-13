__author__ = 'Amr Abouelleil'
import unittest
import os
import time
import logging
from widdler.Cromwell import Cromwell


class CromwellUnitTests(unittest.TestCase):
    def setUp(self):
        self.logger = logging.getLogger('test_cromwell')
        hdlr = logging.FileHandler('test_cromwell.log')
        formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
        hdlr.setFormatter(formatter)
        self.logger.addHandler(hdlr)
        self.logger.setLevel(logging.WARNING)
        self.cromwell = Cromwell(host='btl-cromwell')
        resources = os.path.join(os.path.abspath(os.path.dirname(__file__)).replace('tests', ''), 'resources')
        self.json = os.path.join(resources, 'test.json')
        self.wdl = os.path.join(resources, 'test.wdl')
        self.logger.info('Resources: {}, {}'.format(self.wdl, self.json))
        self.wf = self.cromwell.jstart_workflow(self.wdl, self.json)
        self.logger.info('Workflow: {}'.format(self.wf))
        self.workflow_id = self.wf['id']
        time.sleep(2)

    def test_start_workflow(self):
        self.logger.info('Testing start_workflow...')
        self.assertTrue('id' in self.wf and 'status' in self.wf)
        self.assertEqual(self.wf ['status'], 'Submitted')
        self.assertEqual(len(self.workflow_id), 36)

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

    def test_query_logs(self):
        self.logger.info('Testing query_logs...')
        result = self.cromwell.query_logs(self.workflow_id)
        self.logger.info('Result: {}'.format(result))
        self.assertTrue('id' in result)

    def test_stop_workflow(self):
        self.logger.info('Testing stop_workflow...')
        result = self.cromwell.stop_workflow(self.workflow_id)
        self.logger.info('Result: {}'.format(result))

    def tearDown(self):
        self.logger.info("Test done!")