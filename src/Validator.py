__author__= 'Amr Abouelleil'
import logging
import json
import config as c
import os


class Validator:
    """
    Module to validate WDL and JSON inputs.
    """
    def __init__(self):
        self.wdl_tool = os.path.join(c.resource_dir, 'wdltool-0.10.jar')

    def get_json(self, json):
        pass

    def validate_json(self, json):
        pass