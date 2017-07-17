__author__ = 'Amr Abouelleil'
import unittest
import logging
import config as c
import os
from Validator import Validator


class ValidatorUnitTests(unittest.TestCase):
    @classmethod
    def setUpClass(self):
        resources = c.resource_dir
        self.logger = logging.getLogger('test_validator')
        hdlr = logging.FileHandler(os.path.join(c.log_dir, 'test_validator.log'))
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        hdlr.setFormatter(formatter)
        self.logger.addHandler(hdlr)
        self.logger.setLevel(logging.INFO)
        self.json = os.path.join(resources, 'test.json')
        self.validator = Validator()


    def test_validate_json(self):
        pass

    @classmethod
    def tearDownClass(self):
        self.logger.info("Test done!")