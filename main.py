#!/usr/bin/env python3
import argparse
from nextcloudBackup import NextcloudBackup

def main():
    """Sets up argument parser to parse command line arguments and calls class start method"""
    parser = argparse.ArgumentParser()
    parser.add_argument('--verbose', default=False, help='increases verbosity', action='store_true')
    parser.add_argument('--dry-run', default=False, help='run script without copying files, implies --verbose', action='store_true')
    backup = NextcloudBackup(parser.parse_args())
    backup.main()
    backup.tearDown()

if __name__ == '__main__':
    main()
