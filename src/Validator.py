__author__= 'Amr Abouelleil'
import logging
import json
import src.config as c
import os
import subprocess
import csv
import sys

module_logger = logging.getLogger('widdler.Validator')


class Validator:
    """
    Module to validate JSON inputs.
    """
    def __init__(self, wdl, json):
        self.wdl = wdl
        self.json = json
        self.wdl_tool = os.path.join(c.resource_dir, 'wdltool-0.10.jar')
        self.logger = logging.getLogger('widdler.validator.Validator')

    def get_json(self):
        """
        Get a dict representation of the json file.
        :return: dict
        """
        fh = open(self.json)
        json_data = json.load(fh)
        fh.close()
        return json_data

    def get_wdl_args(self):
        """
        Uses wdl-tool to get the expected arguments from the WDL file.
        :return: Returns a dictionary of wdl arguments as keys and expected type as as value.
        """
        try:
            os.chdir(os.path.dirname(self.wdl))
        except OSError:
            print('Warning: Could not navigate to WDL directory.')
        cmd = ['java', '-jar', self.wdl_tool, 'inputs', self.wdl]
        run = subprocess.check_output(cmd).decode("utf-8")
        try:
            return json.loads(run)
        except json.JSONDecodeError:
            print("Something went wrong with getting args. Note that if using validation, unzipped WDL dependencies "
                  "must be in same directory as main WDL.\n "
                  "Alternatively, turn off validation or use widdler.py validate")
            sys.exit(-1)

    def validate_json(self):
        """
        A function for validating a json file intended for WDL execution against the WDL file.
        :return: A list of errors found with the json file.
        """
        errors = list()
        jdict = self.get_json()
        wdict = self.get_wdl_args()
        # for every key/value pair in jdict
        # first make sure the key is in wdict. If it isn't, that's an error.
        # return a list of any errors uncovered.
        for param, val in jdict.items():
            if self.validate_param(param, wdict):
                # param is valid
                if 'File' in wdict[param]:
                    if not self.validate_file(val):
                        errors.append('{}: {} is not a valid file path.'.format(param, val))
                elif 'Array' in wdict[param]:
                    if not self.validate_array(val):
                        errors.append('{}: {} is not a valid array/list.'.format(param, val))
                elif 'String' in wdict[param]:
                    if not self.validate_string(val):
                        errors.append('{}: {} is not a valid String.'.format(param, val))
                elif 'Int' in wdict[param]:
                    if not self.validate_int(val):
                        errors.append('{}: {} is not a valid Int.'.format(param, val))
                elif 'Float' in wdict[param]:
                    if not self.validate_float(val):
                        errors.append('{}: {} is not a valid Float.'.format(param, val))
                elif 'Boolean' in wdict[param]:
                    if not self.validate_boolean(val):
                        msg = "Note that JSON boolean values must not be quoted."
                        errors.append('{}: {} is not a valid Boolean. {}'.format(param, val, msg))
                else:
                    errors.append('{}: {} is not a recognized parameter value'.format(param, val))
                if 'samples_file' in param:
                    try:
                        fh = open(val, 'r')
                        s_reader = csv.reader(fh, delimiter='\t')
                        errors += self.validate_samples_array(s_reader)
                        fh.close()
                    except IOError as e:
                        errors.append(str(e))
                # Once a parameter is processed we delete it from wdict so we can see if any parameters were not
                # checked. This indicates the user didn't specify the parameter. If the param is optional that's ok
                # but if it isn't, we should add it to errors.
                del wdict[param]
        for k, v in wdict.items():
            if 'optional' not in v:
                errors.append('Required parameter {} is missing from input json.'.format(k))
        return errors

    def validate_samples_array(self, samples_array):
        """
        Validates a TSV sample file array (passed as an array) used in WDL inputs.
        Assumes that last column of each row contains an absolute path to a file.
        :param samples_file: a tab-delimitted file with the last column of each row containing a file path.
        :return: A list of errors. If list is empty, there were no errors.
        """
        errors = []
        for row in samples_array:
            if not self.validate_file(row[-1]):
                errors.append('File path {} found in samples file does not exist.'.format(row[-1]))
        return errors

    @staticmethod
    def validate_array(i):
        """
        Returns true if the input value is of class list, false if not. Note that isinstance does not behave as
        expected here, hence why I use type instead.
        :param i: input parameter
        :return: Boolean
        """
        if type(i) is list:
            return True
        else:
            return False

    @staticmethod
    def validate_param(param, wdict):
        """
        Returns true if the param exists in WDL, false if not.
        :param param: the param to evaluate
        :param wdict: dictionary of wdl args
        :return: Boolean
        """
        if param in wdict:
            return True
        else:
            return False

    @staticmethod
    def validate_string(i):
        """
        Returns true if object is string, false if not.
        :param i: input object
        :return: Boolean
        """
        return isinstance(i, basestring)

    @staticmethod
    def validate_file(f):
        """
        Validates that a particular file exists in the file system.
        :param f:
        :return: Boolean
        """
        return os.path.exists(f.rstrip())

    @staticmethod
    def validate_boolean(i):
        """
        Returns true if object is a boolean, false if not.
        :param i: input object
        :return: Boolean
        """
        return isinstance(i, bool)

    @staticmethod
    def validate_int(i):
        """
        Returns true if object is an int, false if not.
        :param i: input object
        :return: Boolean
        """
        return isinstance(i, int)

    @staticmethod
    def validate_float(i):
        """
        Returns true if object is a float, false if not.
        :param i: input object
        :return: Boolean
        """
        return isinstance(i, float)
