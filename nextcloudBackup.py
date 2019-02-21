'''Contains Singleton metaclass and NextcloudBackup class to backup Nextcloud data

Since NextcloudBackup.__init__() includes system calls to mount and opening log files,
only one instance of NextcloudBackup should exist at a time. To ensure that this is the case,
NextcloudBackup is an instance of its metaclass, Singleton, which creates an instance of
NextcloudBackup if one does not exist, and returns it. Otherwise, the existing
instance is returned.
'''

import datetime
import os
import sys
import shutil
import subprocess
import argparse

class Singleton(type):
    '''Metaclass to ensure only one instance of cls exists at a time'''
    _instance = None
    def __call__(cls, *args, **kwargs):
        '''Creates new instance of cls if one does not exist'''
        if cls._instance is None:
            cls._instance = super(Singleton, cls).__call__(*args, **kwargs)

        return cls._instance

class NextcloudBackup(metaclass=Singleton):
    '''Class designed to perform an incremental backup of Nextcloud data'''
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
        '''Initializes object, validates constants/passed arguments, and mounts backup partition'''
        # list of files to backup
        self.toBackup = []

        # verify argparse namespace object
        self.args = self.checkArgs(args)

        # verify that NEXTCLOUD_DATA, NEXTCLOUD_DATA_BACKUP, and
        # NEXTCLOUD_BACKUP_PARTITION exist
        self.checkDataExists()

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

    def __enter__(self):
        '''Returns self when used in context manager'''
        return self

    def __exit__(self, *args, **kwargs):
        '''Calls tearDown() at end of context manager'''
        self.tearDown()

    def tearDown(self):
        '''Unmounts Nextcloud backup partition and closes open log files'''
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
        '''Verifies that data location, backup mount point, and backup partition exist'''
        # test if nextcloud data directory exists
        if not os.path.exists(self.NEXTCLOUD_DATA):
            sys.exit(('Error: Nextcloud data directory \'{}\' '
                      'does not exist'.format(self.NEXTCLOUD_DATA)))

        # test if nextcloud backup mount point exists
        if not os.path.exists(self.NEXTCLOUD_DATA_BACKUP):
            sys.exit(('Error: Nextcloud backup mount point \'{}\' does '
                      'not exist'.format(self.NEXTCLOUD_DATA_BACKUP)))

        # verifies if specified partition exists
        if self.NEXTCLOUD_BACKUP_PARTITION.split('/')[-1] not in self.executeCommand('lsblk -l'):
            sys.exit(('Error: Nextcloud backup partition \'{}\' '
                      'does not exist'.format(self.NEXTCLOUD_BACKUP_PARTITION)))

    def checkArgs(self, args):
        '''Validates passed command line arguments and returns passed object if valid'''
        # check that args is of type argparse.Namespace
        if not isinstance(args, argparse.Namespace):
            sys.exit(('Error: expected object of type \'argparse.Namespace\', received '
                      'object of type \'{}\''.format(type(args))))

        # check that args has correct attributes
        if not hasattr(args, 'verbose') or not hasattr(args, 'dry_run'):
            sys.exit('Error: missing required attributes in Namespace object')

        # check that attributes are of correct type (bool)
        for val in [args.verbose, args.dry_run]:
            if not isinstance(val, bool):
                sys.exit(('Error: expected property of type \'bool\', '
                          'found type \'{}\''.format(type(val))))

        # dry run implies verbose
        if args.dry_run:
            args.verbose = True

        return args

    def openLogFile(self, path):
        '''Opens given file if it exists, otherwise it is created. File object is then returned'''
        if not os.path.isfile(path):
            fp = open(path, 'w+')
        else:
            fp = open(path, 'r+')

        return fp

    def executeCommand(self, command):
        '''Executes command given and exits if error is encountered'''
        if self.args.dry_run:
            return ''

        # create subprocess object with passed command
        process = subprocess.Popen(command,
                                   stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE,
                                   shell=True)
        # get stdout and stderr from process object
        out, err = process.communicate()
        out = out[:-1].decode()
        err = err[:-1].decode()

        # if process.returncode is a non-zero value, report encountered error
        if process.returncode:
            errorMessage = ('{}: \'{}\' returned the following error: \'{}\''
                            .format(datetime.datetime.now().strftime('%c'), command, err))
            self.error.write(errorMessage + '\n')
            print(errorMessage, file=sys.stderr)
            sys.exit(process.returncode)

        # return captured stdout from executed command
        return out

    def mountBackupPartition(self):
        '''Mounts Nextcloud backup partition and unmounts required resources if used'''
        # if something is mounted at our backup mount point, unmount it
        if os.path.ismount(self.NEXTCLOUD_DATA_BACKUP):
            self.executeCommand('umount {}'.format(self.NEXTCLOUD_DATA_BACKUP))

        # if our backup partition is mounted, unmount it
        if self.NEXTCLOUD_BACKUP_PARTITION in self.executeCommand('mount -l'):
            self.executeCommand('umount {}'.format(self.NEXTCLOUD_BACKUP_PARTITION))

        # mount storage partition
        self.executeCommand('mount {} {}'
                            .format(self.NEXTCLOUD_BACKUP_PARTITION, self.NEXTCLOUD_DATA_BACKUP))

    def main(self):
        '''Main routine to perform incremental backup'''
        # get datetime of last backup
        lastBackup = datetime.datetime.strptime(self.log.readlines()[-1].strip('\n'), '%c')

        # iterate through nextcloud data and find all files that need to be backed up
        for subdir, dirs, files in os.walk(self.NEXTCLOUD_DATA):
            for f in files:
                path = os.path.join(subdir, f)
                if datetime.datetime.fromtimestamp(os.path.getmtime(path)) > lastBackup or \
                    not os.path.exists(path.replace(self.NEXTCLOUD_DATA, self.NEXTCLOUD_DATA_BACKUP)):
                    self.toBackup.append(path)

        # iterate over all files that need to be backed up and copy them
        for src in self.toBackup:
            if src.split('.')[-1] in self.IGNORED_FILE_TYPES:
                continue

            dst = src.replace(self.NEXTCLOUD_DATA, self.NEXTCLOUD_DATA_BACKUP)
            destPath = dst.replace(dst[dst.rfind('/') + 1:], '')

            # if directory doesn't exist, create it
            if not os.path.exists(destPath):
                if self.args.verbose:
                    print('creating \'{}\''.format(destPath))

                os.makedirs(destPath, exist_ok=True)

            # attempt to copy file. if error is caught, record error in log and
            # add errored file to erroredFiles log if it still exists
            # (if it wasn't deleted during this process)
            try:
                if self.args.verbose:
                    print('\'{}\' --> \'{}\''.format(src, dst))

                if not self.args.dry_run:
                    shutil.copy2(src, dst)
            except Exception as e:
                errorMessage = ('{}: caught error \'{}\' while attempting to copy \'{}\''
                                .format(datetime.datetime.now().strftime('%c'), e, dst))
                self.error.write(errorMessage + '\n')
                print(errorMessage, file=sys.stderr)

                if os.path.exists(src):
                    self.erroredFiles.write(src + '\n')
