import unittest
import os
import time
import logging
from src.Cromwell import Cromwell
from src.Monitor import Monitor
import src.config as c
import datetime
import requests


class MyTestCase(unittest.TestCase):
    @classmethod
    def setUp(self):
        resources = c.resource_dir
        self.logger = logging.getLogger('test_cromwell')
        hdlr = logging.FileHandler(os.path.join(c.log_dir, 'test_cromwell.log'))
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        hdlr.setFormatter(formatter)
        self.logger.addHandler(hdlr)
        self.logger.setLevel(logging.INFO)
        self.cromwell = Cromwell(host='btl-cromwell')
        self.json = os.path.join(resources, 'test.json')
        self.wdl = os.path.join(resources, 'test.wdl')
        self.m = Monitor(user='amr', host='btl-cromwell', no_notify=False, verbose=True, interval=5)
        self.wf = self.cromwell.jstart_workflow(self.wdl, self.json)
        self.workflow_id = self.wf['id']
        time.sleep(2)

    def test_monitor_workflow(self):
        self.assertEquals(0, self.m.monitor_workflow(self.workflow_id))

    def test_get_user_workflows(self):
        self.m.get_user_workflows()

    @classmethod
    def tearDown(self):
        self.cromwell.stop_workflow(self.workflow_id)


if __name__ == '__main__':
    unittest.main()
