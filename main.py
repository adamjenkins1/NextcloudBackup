#!/usr/bin/env python3
'''Contains main function to create NextcloudBackup object and start incremental backup'''

import argparse
from nextcloudBackup import NextcloudBackup

def main():
    '''Sets up argument parser to parse command line arguments and calls class main method'''
    parser = argparse.ArgumentParser()
    parser.add_argument('--verbose', default=False, help='increases verbosity', action='store_true')
    parser.add_argument('--dry-run', default=False, help='run script without copying files, implies --verbose', action='store_true')

    with NextcloudBackup(parser.parse_args()) as backup:
        backup.main()

if __name__ == '__main__':
    main()
