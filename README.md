# Nextcloud Backup [![Build Status](https://travis-ci.org/adamjenkins1/NextcloudBackup.svg?branch=master)](https://travis-ci.org/adamjenkins1/NextcloudBackup) [![codecov](https://codecov.io/gh/adamjenkins1/NextcloudBackup/branch/master/graph/badge.svg)](https://codecov.io/gh/adamjenkins1/NextcloudBackup)
A Python class designed to perform incremental backups

## Installation
All necessary files are included in the git repository
```
git clone https://github.com/adamjenkins1/NextcloudBackup.git
```

## Dependencies
Python >= 3.5

## Usage
Before running, make sure that `NEXTCLOUD_DATA`, `NEXTCLOUD_DATA_BACKUP`, and `NEXTCLOUD_BACKUP_PARTITION` in `nextcloudBackup.py` reflect the proper values for your system.
To start the incremental backup, run `main.py` with any of the following arguments.
```
usage: main.py [-h] [--verbose] [--dry-run]

script to perform incremental backups using NextcloudBackup class

optional arguments:
  -h, --help  show this help message and exit
  --verbose   increases verbosity
  --dry-run   run script without copying files, implies --verbose
```

To run the tests, use `python3 -m unittest tests.py`. 
