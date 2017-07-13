#!/usr/bin/env python
__author__ = "Amr Abouelleil"

import sys
import argparse

parser = argparse.ArgumentParser(description="")
parser.add_argument('-i', '--input', action='store',
                    help='Input file.')

args = vars(parser.parse_args())


def main():
    pass


if __name__ == "__main__":
    sys.exit(main())

