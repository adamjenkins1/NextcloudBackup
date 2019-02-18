#!/usr/bin/env python3
import datetime
import os
import sys
import shutil
import subprocess
import argparse

class Singleton(type):
    _instance = None
    def __call__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(Singleton, cls).__call__(*args, **kwargs)

        return cls._instance

class NextcloudBackup(metaclass=Singleton):
    # constants
    NEXTCLOUD_BACKUP_LOG = '/var/log/nextcloud/backups/backups.log'
    NEXTCLOUD_BACKUP_ERROR_LOG = '/var/log/nextcloud/backups/error.log'
    NEXTCLOUD_ERRORED_FILES_LOG = '/var/log/nextcloud/backups/errored_files.log'
    NEXTCLOUD_DATA = '/var/www/nextcloud/data/'
    NEXTCLOUD_DATA_BACKUP = '/mnt/nextcloud_backup/'
    NEXTCLOUD_BACKUP_PARTITION = '/dev/sdc1'
    IGNORED_FILE_TYPES = ['part']
    OLD_DUMMY_DATE = 'Tue Jan 29 19:37:23 2000\n'

    def __init__(self, args):
        # list of files to backup
        self.toBackup = []
        
        # verify that NEXTCLOUD_DATA, NEXTCLOUD_DATA_BACKUP, and 
        # NEXTCLOUD_BACKUP_PARTITION exist
        self.checkDataExists()

        # verify argparse namespace object
        self.args = self.checkArgs(args)

        # log variables
        self.log = self.openLogFile(self.NEXTCLOUD_BACKUP_LOG)
        self.error = self.openLogFile(self.NEXTCLOUD_BACKUP_ERROR_LOG)
        self.erroredFiles = self.openLogFile(self.NEXTCLOUD_ERRORED_FILES_LOG)

        # if backup log is empty, add dummy date
        if os.stat(self.NEXTCLOUD_BACKUP_LOG).st_size == 0:
            self.log.write(self.OLD_DUMMY_DATE)

        # if errored files log contains files, read them first
        if os.stat(self.NEXTCLOUD_ERRORED_FILES_LOG).st_size != 0:
            self.toBackup = [x.strip('\n') for x in self.erroredFiles.readlines()]
            # remove recently read files from log
            # edge case -- program crashes mid operation: errored filenames are lost
            self.erroredFiles.truncate(0)

        self.mountBackupPartition()

    def tearDown(self):
        # unmount storage partition
        self.executeCommand('umount {}'.format(self.NEXTCLOUD_BACKUP_PARTITION))

        # force drive to spin down
        self.executeCommand('hdparm -y {}'.format(self.NEXTCLOUD_BACKUP_PARTITION))

        # write current date in log if not dry run
        if not self.args.dry_run:
            self.log.write(datetime.datetime.now().strftime('%c') + '\n')

        # close log files
        self.log.close()
        self.error.close()
        self.erroredFiles.close()

    def checkDataExists(self):
        paths = {
                    self.NEXTCLOUD_DATA: 'Error: Nextcloud data directory \'{}\' does not exist'.format(self.NEXTCLOUD_DATA), 
                    self.NEXTCLOUD_DATA_BACKUP: 'Error: Nextcloud backup mount point \'{}\' does not exist'.format(self.NEXTCLOUD_DATA_BACKUP)
                }

        for path, err in paths.items():
            if not os.path.exists(path):
                sys.exit(err)

        if self.NEXTCLOUD_BACKUP_PARTITION.split('/')[-1] not in self.executeCommand('lsblk -l'):
            sys.exit('Error: Nextcloud backup partition \'{}\' does not exist'.format(self.NEXTCLOUD_BACKUP_PARTITION))

    def checkArgs(self, args):
        # check type of args object
        if not isinstance(args, argparse.Namespace):
            sys.exit('Error: expected object of type \'argparse.Namespace\', received object of type \'{}\''.format(type(args)))

        # check that args has correct attributes
        if not hasattr(args, 'verbose') or not hasattr(args, 'dry_run'):
            sys.exit('Error: missing required attributes in Namespace object')
        
        # check that attributes are of correct type (bool)
        for val in [args.verbose, args.dry_run]:
            if not isinstance(val, bool):
                sys.exit('Error: expected property of type \'bool\', found type \'{}\''.format(type(val)))

        if args.dry_run:
            args.verbose = True

        return args

    def openLogFile(self, path):
        if not os.path.isfile(path):
            fp = open(path, 'w+')
        else:
            fp = open(path, 'r+')

        return fp

    def executeCommand(self, command):
        """Executes command given and exits if error is encountered"""
        if self.args.dry_run:
            return ''

        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
        out, err = process.communicate()
        out = out[:-1].decode()
        err = err[:-1].decode()

        if process.returncode:
            errorMessage = '{}: \'{}\' returned the following error: \'{}\''.format(datetime.datetime.now().strftime('%c'), command, err)
            self.error.write(errorMessage + '\n')
            print(errorMessage, file=sys.stderr)
            sys.exit(process.returncode)

        return out

    def mountBackupPartition(self):
        # if something is mounted at our backup mount point, unmount it
        if os.path.ismount(self.NEXTCLOUD_DATA_BACKUP):
            self.executeCommand('umount {}'.format(self.NEXTCLOUD_DATA_BACKUP))

        # if our backup partition is mounted, unmount it
        if self.NEXTCLOUD_BACKUP_PARTITION in self.executeCommand('mount -l'):
            self.executeCommand('umount {}'.format(self.NEXTCLOUD_BACKUP_PARTITION))

        # mount storage partition
        self.executeCommand('mount {} {}'.format(self.NEXTCLOUD_BACKUP_PARTITION, self.NEXTCLOUD_DATA_BACKUP))

    def main(self):
        # get datetime of last backup
        lastBackup = datetime.datetime.strptime(self.log.readlines()[-1].strip('\n'), '%c')

        # iterate through nextcloud data and find all files that need to be backed up
        for subdir, dirs, files in os.walk(self.NEXTCLOUD_DATA):
            for f in files:
                path = os.path.join(subdir, f)
                if datetime.datetime.fromtimestamp(os.path.getmtime(path)) > lastBackup:
                    self.toBackup.append(path)

        # iterate over all files that need to be backed up and copy them
        for src in self.toBackup:
            if src.split('.')[-1] in self.IGNORED_FILE_TYPES:
                continue

            dst = src.replace(self.NEXTCLOUD_DATA, self.NEXTCLOUD_DATA_BACKUP)
            dirPath = dst.replace(dst[dst.rfind('/') + 1:], '')

            if not os.path.exists(dirPath):
                if self.args.verbose:
                    print('creating \'{}\''.format(dirPath))

                os.makedirs(dirPath, exist_ok=True)

            try:
                if self.args.verbose:
                    print('\'{}\' --> \'{}\''.format(src, dst))

                if not self.args.dry_run:
                    shutil.copy2(src, dst)
            except Exception as e:
                errorMessage = '{}: caught error \'{}\' while attempting to copy \'{}\''.format(datetime.datetime.now().strftime('%c'), e, dst)
                self.error.write(errorMessage + '\n')
                print(errorMessage, file=sys.stderr)

                if os.path.exists(src):
                    self.erroredFiles.write(src + '\n')
