#!/usr/bin/env python
"""Some docstring"""
# import statements
import sys
import argparse

# Metadata
__author__ = "Amr Abouelleil"
__copyright__ = "Copyright 2017, The Broad Institute"
__credits__ = ["Amr Abouelleil"]
__license__ = "GPL"
__version__ = "1.0"
__maintainer__ = "Amr Abouelleil"
__email__ = "amr@broadinstitute.org"
__status__ = "Development"

parser = argparse.ArgumentParser(description="")
parser.add_argument('-i', '--input', action='store',
                    help='Input file.')

args = vars(parser.parse_args())


def main():
    pass


if __name__ == "__main__":
    sys.exit(main())
