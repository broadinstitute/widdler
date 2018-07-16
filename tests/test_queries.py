__author__ = 'Amr Abouelleil'
import unittest
import os
import time
from src.Cromwell import Cromwell
import src.config as c
import datetime
import requests


class QueryUnitTests(unittest.TestCase):
    @classmethod
    def setUpClass(self):
        resources = c.resource_dir
        self.cromwell = Cromwell(host='btl-cromwell')
        self.json = os.path.join(resources, 'hw.json')
        self.wdl = os.path.join(resources, 'hw.wdl')
        self.labels = {'username': 'amr', 'foo': 'bar'}

    def _initiate_workflow(self):
        wf = self.cromwell.jstart_workflow(self.wdl, self.json)
        time.sleep(5)
        return wf

    def test_query_status(self):
        wf = self._initiate_workflow()
        wfid = wf['id']
        result = self.cromwell.query_status(wfid)
        self.assertTrue('id' in result and 'status' in result)
        self.cromwell.stop_workflow(wfid)

    def test_query_metadata(self):
        wf = self._initiate_workflow()
        wfid = wf['id']
        result = self.cromwell.query_metadata(wfid)
        self.assertTrue('id' in result and 'submission' in result)
        self.cromwell.stop_workflow(wfid)

    def test_query_logs(self):
        wf = self._initiate_workflow()
        wfid = wf['id']
        result = self.cromwell.query_logs(wfid)
        self.assertTrue('id' in result)
        self.cromwell.stop_workflow(wfid)

    def test_build_long_url(self):
        wf = self._initiate_workflow()
        wfid = wf['id']
        url_dict = {
            'name': 'test_build_long_url',
            'id': wfid,
            'start': datetime.datetime.now() - datetime.timedelta(days=1),
            'end': datetime.datetime.now()
        }
        query_url = self.cromwell.build_query_url('http://btl-cromwell:9000/api/workflows/v1/query?', url_dict)
        r = requests.get(query_url)
        self.assertEquals(r.status_code, 200)
        self.cromwell.stop_workflow(wfid)

    def test_query(self):
        wf = self._initiate_workflow()
        wfid = wf['id']
        url_dict = {
            'name': 'gatk',
            'id': [wfid],
            'start': datetime.datetime.now() - datetime.timedelta(days=1),
            'end': datetime.datetime.now()
        }
        result = self.cromwell.query(url_dict)
        self.assertTrue(isinstance(result['results'], list), True)
        self.cromwell.stop_workflow(wfid)

    def test_label_workflow(self):
        wf = self._initiate_workflow()
        wfid = wf['id']
        r = self.cromwell.label_workflow(wfid, self.labels)
        self.assertEquals(r.status_code, 200)
        self.cromwell.stop_workflow(wfid)

    def test_query_labels(self):
        wf = self._initiate_workflow()
        wfid = wf['id']
        labels = {'username': 'amr', 'foo': 'bar'}
        self.cromwell.label_workflow(wfid, self.labels)
        # This sleep is needed to make sure the label workflow completes before we query for it.
        time.sleep(5)
        r = self.cromwell.query_labels(labels)
        # Here, the most recent workflow that matches the query will be the last item so we can use that to check
        # this assertion.
        self.assertTrue(wfid in r['results'][-1]['id'])
        self.cromwell.stop_workflow(wfid)

    def test_query_filter_by_status(self):
        from argparse import Namespace
        from widdler import call_list
        wf = self._initiate_workflow()
        wfid = wf['id']
        result = call_list(Namespace(server="btl-cromwell", all=False, no_notify=True, verbose=True, interval=None,
                                     username="*", days=1, filter=['Succeeded']))
        statuses = set(d['status'] for d in result)
        self.assertEqual(len(statuses), 1)
        self.cromwell.stop_workflow(wfid)

    def test_query_filter_by_name(self):
        from argparse import Namespace
        from widdler import call_list
        user_result = call_list(Namespace(server="btl-cromwell", all=False, no_notify=True, verbose=True, interval=None,
                                          username="amr", days=1, filter=None))
        user_wfids = set(d['id'] for d in user_result)
        all_result = call_list(Namespace(server="btl-cromwell", all=False, no_notify=True, verbose=True, interval=None,
                               username="*", days=1, filter=None))
        all_wfids = set(d['id'] for d in all_result)
        self.assertGreater(len(all_wfids), len(user_wfids))

    def test_query_filter_by_days(self):
        from argparse import Namespace
        from widdler import call_list
        result = call_list(Namespace(server="btl-cromwell", all=False, no_notify=True, verbose=True, interval=None,
                                     username="*", days=1, filter=None))
        all_dates = set(d['start'].split('T')[0] for d in result)
        print all_dates
        self.assertEqual(len(all_dates), 1)

    def test_query_backend(self):
        self.assertTrue('defaultBackend' in self.cromwell.query_backend())

    @classmethod
    def tearDownClass(self):
        print("Done!")