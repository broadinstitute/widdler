__author__ = 'Amr Abouelleil'
import unittest
import logging
import src.config as c
import os
from src.Validator import Validator


class ValidatorUnitTests(unittest.TestCase):
    """
    This test class tests good inputs only. A separate one for bad inputs is below.
    """
    @classmethod
    def setUpClass(self):
        resources = c.resource_dir
        self.logger = logging.getLogger('test_validator')
        hdlr = logging.FileHandler(os.path.join(c.log_dir, 'test_validator.log'))
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        hdlr.setFormatter(formatter)
        self.logger.addHandler(hdlr)
        self.logger.setLevel(logging.INFO)
        self.wdl = os.path.join(resources, 'test.wdl')
        self.json = os.path.join(resources, 'test.json')
        self.validator = Validator(wdl=self.wdl, json=self.json)
        self.logger.info('Starting Validator tests...')
        self.wdl_args = self.validator.get_wdl_args()
        self.json_args = self.validator.get_json()

    def test_get_wdl_args(self):
        self.assertIsInstance(self.wdl_args, dict)

    def test_get_json(self):
        self.logger.info("Testing get_json...")
        self.assertIsInstance(self.json_args, dict)

    def test_validate_param_json(self):
        self.logger.info("Testing validate_param_json...")
        for k, v in self.json_args.items():
            if not self.validator.validate_param(k, self.wdl_args):
                print(k, v)

            self.assertIs(self.validator.validate_param(k, self.wdl_args), True)

    def test_validate_string(self):
        self.logger.info("Testing validate_string...")
        self.assertIs(self.validator.validate_string('foo'), True)
        self.assertIs(self.validator.validate_string(0), False)
        self.assertIs(self.validator.validate_string(1.0), False)
        self.assertIs(self.validator.validate_string(True), False)

    def test_validate_boolean(self):
        self.logger.info("Testing validate_boolean...")
        self.assertIs(self.validator.validate_boolean('foo'), False)
        self.assertIs(self.validator.validate_boolean(0), False)
        self.assertIs(self.validator.validate_boolean(1.0), False)
        self.assertIs(self.validator.validate_boolean(True), True)

    def test_validate_int(self):
        self.logger.info("Testing validate_int...")
        self.assertIs(self.validator.validate_int('foo'), False)
        self.assertIs(self.validator.validate_int(0), True)
        self.assertIs(self.validator.validate_int(1.0), False)
        self.assertIs(self.validator.validate_int(True), True)

    def test_validate_float(self):
        self.logger.info("Testing validate_float...")
        self.assertIs(self.validator.validate_float('foo'), False)
        self.assertIs(self.validator.validate_float(0), False)
        self.assertIs(self.validator.validate_float(1.0), True)
        self.assertIs(self.validator.validate_float(True), False)

    def test_validate_file(self):
        self.assertIs(self.validator.validate_file(self.wdl), True)
        self.assertIs(self.validator.validate_file('notexists.txt'), False)

    def test_validate_samples_array(self):
        samples_array = [
            ['S1', self.wdl],
            ['S2', self.json],
            ['S3', 'not_exists.txt']
        ]
        result = self.validator.validate_samples_array(samples_array)
        self.assertEqual(1, len(result))

    def test_validate_json(self):
        self.validator.validate_json()

    @classmethod
    def tearDownClass(self):
        self.logger.info("Test done!")


class ValidatorUnitTestsBad(unittest.TestCase):
    """
    This test class tests good inputs only. A separate one for bad inputs is below.
    """
    @classmethod
    def setUpClass(self):
        resources = c.resource_dir
        self.logger = logging.getLogger('test_validator')
        hdlr = logging.FileHandler(os.path.join(c.log_dir, 'test_validator.log'))
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        hdlr.setFormatter(formatter)
        self.logger.addHandler(hdlr)
        self.logger.setLevel(logging.INFO)
        self.wdl = os.path.join(resources, 'test.wdl')
        self.json = os.path.join(resources, 'bad.json')
        self.validator = Validator(wdl=self.wdl, json=self.json)
        self.logger.info('Starting Validator tests...')
        self.wdl_args = self.validator.get_wdl_args()
        self.json_args = self.validator.get_json()

    def test_validate_param_json(self):
        self.logger.info("Testing validate_param_json...")
        ref_dict = {"gatk.samples_file": "/cil/shed/sandboxes/amr/dev/gatk_pipeline/data/pfal_5.tsv"}
        for k, v in self.json_args.items():
            self.assertIs(self.validator.validate_param(k, ref_dict), False)

    @classmethod
    def tearDownClass(self):
        self.logger.info("Test done!")
