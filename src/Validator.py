__author__= 'Amr Abouelleil'
import logging
import json
import src.config as c
import os
import subprocess
module_logger = logging.getLogger('widdler.Validator')
import csv


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
        cmd = ['java', '-jar', self.wdl_tool, 'inputs', self.wdl]
        run = subprocess.check_output(cmd).decode("utf-8")
        return json.loads(run)

    def validate_json(self):
        errors = list()
        jdict = self.get_json()
        wdict = self.get_wdl_args()
        # for every key/value pair in jdict
        # first make sure the key is in wdict. If it isn't, that's an error.
        # return a list of any errors uncovered.
        for param, val in jdict.items():
            if self.validate_param(param, wdict):
                # param is valid
                print(param, wdict[param])
                if 'File' in val:
                    if not self.validate_file(val):
                        errors.append('{} is not a valid file path.'.format(val))
                elif 'Array' in val:
                    if not self.validate_array(val):
                        errors.append('{} is not a valid array.'.format(val))
                elif 'String' in val:
                    if not self.validate_string(val):
                        errors.append('{} is not a valid String.'.format(val))
                elif 'Int' in val:
                    if not self.validate_int(val):
                        errors.append('{} is not a valid Int.'.format(val))
                elif 'Float' in val:
                    if not self.validate_float(val):
                        errors.append('{} is not a valid Float.'.format(val))
                elif 'Boolean' in val:
                    if not self.validate_boolean(val):
                        errors.append('{} is not a valid Float.'.format(val))
                else:
                    errors.append('{} is not a recognized parameteree value'.format(val))
            else:
                # param doesn't exist, add it to errors.
                errors.append('{} is not a valid WDL parameter.'.format(param))

    def validate_array(self, array):
        isinstance(array, list)

    def validate_param(self, param, wdict):
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

    def validate_string(self, i):
        """
        Returns true if object is string, false if not.
        :param i: input object
        :return: Boolean
        """
        return isinstance(i, str)

    def validate_file(self, f):
        return os.path.isfile(f.rstrip())

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
                errors.append('File path {} does not exist.'.format(row[-1]))
        return errors

    def validate_boolean(self, i):
        """
        Returns true if object is a boolean, false if not.
        :param i: input object
        :return: Boolean
        """
        return isinstance(i, bool)

    def validate_int(self, i):
        """
        Returns true if object is an int, false if not.
        :param i: input object
        :return: Boolean
        """
        return isinstance(i, int)

    def validate_float(self, i):
        """
        Returns true if object is a float, false if not.
        :param i: input object
        :return: Boolean
        """
        return isinstance(i, float)