__author__ = 'Amr Abouelleil'
import unittest
import os
import time
import logging
from src.Cromwell import Cromwell
import src.config as c
import datetime
import requests


class CromwellUnitTests(unittest.TestCase):
    @classmethod
    def setUpClass(self):
        resources = c.resource_dir
        self.logger = logging.getLogger('test_cromwell')
        hdlr = logging.FileHandler(os.path.join(c.log_dir, 'test_cromwell.log'))
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        hdlr.setFormatter(formatter)
        self.logger.addHandler(hdlr)
        self.logger.setLevel(logging.INFO)
        self.cromwell = Cromwell(host='ale')
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
        print(result)
        self.assertTrue('id' in result and 'submission' in result)

    def test_query_logs(self):
        self.logger.info('Testing query_logs...')
        result = self.cromwell.query_logs(self.workflow_id)
        self.logger.info('Result: {}'.format(result))
        self.assertTrue('id' in result)

    def test_build_long_url(self):
        url_dict = {
            'name': 'gatk',
            'id': [self.workflow_id],
            'start': datetime.datetime.now() - datetime.timedelta(days=1),
            'end': datetime.datetime.now()
        }
        query_url = self.cromwell.build_query_url('http://btl-cromwell:9000/api/workflows/v1/query?', url_dict)
        r = requests.get(query_url)
        self.assertEquals(r.status_code, 200)

    def test_query(self):
        url_dict = {
            'name': 'gatk',
            'id': [self.workflow_id],
            'start': datetime.datetime.now() - datetime.timedelta(days=1),
            'end': datetime.datetime.now()
        }
        result = self.cromwell.query(url_dict)
        self.assertTrue(isinstance(result['results'], list), True)

    def test_query_backend(self):
        self.assertTrue('defaultBackend' in self.cromwell.query_backend())

    # def test_label_workflow(self):
    #     r = self.cromwell.label_workflow(self.workflow_id, {'foo':'bar'})
    #     self.assertEqual(r.status_code, 200)

    def test_stop_workflow(self):
        self.logger.info('Testing stop_workflow...')
        result = self.cromwell.stop_workflow(self.workflow_id)
        self.logger.info('Result: {}'.format(result))

    @classmethod
    def tearDownClass(self):
        self.logger.info("Test done!")
