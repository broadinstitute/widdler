import unittest
import os
import time
from src.Cromwell import Cromwell
from src.Monitor import Monitor
import src.config as c


class MyTestCase(unittest.TestCase):
    @classmethod
    def setUp(self):
        resources = c.resource_dir
        self.cromwell = Cromwell(host='btl-cromwell')
        self.json = os.path.join(resources, 'hello_world_on_prem.json')
        self.wdl = os.path.join(resources, 'hello_world_on_prem.wdl')

    def test_monitor_workflow(self):
        m = Monitor(user='amr', host='btl-cromwell', no_notify=False, verbose=True, interval=5)
        wf = self.cromwell.jstart_workflow(self.wdl, self.json)
        time.sleep(2)
        workflow_id = wf['id']
        self.assertEqual(0, m.monitor_workflow(workflow_id))

    @classmethod
    def tearDown(self):
        print("Done!")


