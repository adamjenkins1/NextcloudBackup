#!/usr/bin/env python3
from unittest import TestCase, mock, skip
from unittest.mock import MagicMock, patch, mock_open
from argparse import Namespace
import os
import shutil
import random
from nextcloudBackup import NextcloudBackup

class NextcloudBackupTests(TestCase):
    def setUp(self):
        self.OLD_DUMMY_DATE = NextcloudBackup.OLD_DUMMY_DATE
        self.SAMPLE_ERRORED_FILES = '/path/to/file/1.txt\n/path/to/file/2.txt\n'
        self.DUMMY_EPOCH_TIME = 1535862436.9329703
        self.IGNORED_FILE_TYPES = NextcloudBackup.IGNORED_FILE_TYPES
        self.obj = object()

    def tearDown(self):
        if hasattr(self.obj, '_instance') and self.obj._instance is not None:
            del type(self.obj)._instance

        del self.obj

    @patch('os.stat')
    @patch('os.path.isfile')
    @patch('builtins.open', new_callable=mock_open())
    @patch('nextcloudBackup.NextcloudBackup.mountBackupPartition')
    @patch('nextcloudBackup.NextcloudBackup.executeCommand')
    def test_sanity(self, mockExecuteCommand, mockMountBackupPartition, mockOpen, mockIsfile, mockStat):
        mockStat.side_effect = [MagicMock(st_size=1), MagicMock(st_size=0)]
        mockIsfile.return_value = True
        mockExecuteCommand.return_value = ''
        self.obj = NextcloudBackup(Namespace(verbose=False, dry_run=False))

    @patch('os.stat')
    @patch('os.path.isfile')
    @patch('builtins.open', new_callable=mock_open())
    @patch('nextcloudBackup.NextcloudBackup.mountBackupPartition')
    @patch('nextcloudBackup.NextcloudBackup.executeCommand')
    def test_bad_args_object(self, mockExecuteCommand, mockMountBackupPartition, mockOpen, mockIsfile, mockStat):
        mockStat.side_effect = [MagicMock(st_size=1), MagicMock(st_size=0)]
        mockIsfile.return_value = True
        mockExecuteCommand.return_value = ''

        with self.assertRaises(SystemExit) as err:
            self.obj = NextcloudBackup(MagicMock(verbose=False, dry_run=False))

        self.assertEqual(err.exception.code, 'Error: expected object of type \'argparse.Namespace\', received object of type \'<class \'unittest.mock.MagicMock\'>\'')

    @patch('os.stat')
    @patch('os.path.isfile')
    @patch('builtins.open', new_callable=mock_open())
    @patch('nextcloudBackup.NextcloudBackup.mountBackupPartition')
    @patch('nextcloudBackup.NextcloudBackup.executeCommand')
    def test_missing_arg(self, mockExecuteCommand, mockMountBackupPartition, mockOpen, mockIsfile, mockStat):
        mockStat.side_effect = [MagicMock(st_size=1), MagicMock(st_size=0)]
        mockIsfile.return_value = True
        mockExecuteCommand.return_value = ''

        with self.assertRaises(SystemExit) as err:
            self.obj = NextcloudBackup(Namespace(dry_run=False))

        self.assertEqual(err.exception.code, 'Error: missing required attributes in Namespace object')

    @patch('os.stat')
    @patch('os.path.isfile')
    @patch('builtins.open', new_callable=mock_open())
    @patch('nextcloudBackup.NextcloudBackup.mountBackupPartition')
    @patch('nextcloudBackup.NextcloudBackup.executeCommand')
    def test_bad_arg_type(self, mockExecuteCommand, mockMountBackupPartition, mockOpen, mockIsfile, mockStat):
        mockStat.side_effect = [MagicMock(st_size=1), MagicMock(st_size=0)]
        mockIsfile.return_value = True
        mockExecuteCommand.return_value = ''

        with self.assertRaises(SystemExit) as err:
            self.obj = NextcloudBackup(Namespace(verbose=False, dry_run=1))

        self.assertEqual(err.exception.code, 'Error: expected property of type \'bool\', found type \'<class \'int\'>\'')

    @patch('os.stat')
    @patch('os.path.isfile')
    @patch('builtins.open', new_callable=mock_open())
    @patch('nextcloudBackup.NextcloudBackup.mountBackupPartition')
    @patch('nextcloudBackup.NextcloudBackup.executeCommand')
    def test_set_verbosity_on_dry_run(self, mockExecuteCommand, mockMountBackupPartition, mockOpen, mockIsfile, mockStat):
        mockStat.side_effect = [MagicMock(st_size=1), MagicMock(st_size=0)]
        mockIsfile.return_value = True
        mockExecuteCommand.return_value = ''
        self.obj = NextcloudBackup(Namespace(dry_run=True, verbose=False))
        self.assertTrue(self.obj.args.verbose)

    @patch('os.stat')
    @patch('os.path.isfile')
    @patch('nextcloudBackup.NextcloudBackup.mountBackupPartition')
    @patch('nextcloudBackup.NextcloudBackup.executeCommand')
    def test_log_access(self, mockExecuteCommand, mockMountBackupPartition, mockIsfile, mockStat):
        mockStat.side_effect = [MagicMock(st_size=0), MagicMock(st_size=1)]
        mockIsfile.return_value = False
        mockExecuteCommand.return_value = ''
        mainHandler = mock_open()
        mockLog = mock_open()
        mockError = mock_open()
        mockErroredFiles = mock_open(read_data=self.SAMPLE_ERRORED_FILES)
        mainHandler.side_effect = [mockLog.return_value, mockError.return_value, mockErroredFiles.return_value]
        with patch('builtins.open', mainHandler):
            self.obj = NextcloudBackup(Namespace(dry_run=True, verbose=False))
            self.assertEqual(self.obj.toBackup, self.SAMPLE_ERRORED_FILES.split('\n')[:-1])
            mockLog().write.assert_called_once_with(self.OLD_DUMMY_DATE)

    #@skip('test not done yet')
    @patch('shutil.copy2')
    @patch('os.path.getmtime')
    @patch('os.path.exists')
    @patch('os.walk')
    @patch('os.stat')
    @patch('os.path.isfile')
    @patch('nextcloudBackup.NextcloudBackup.mountBackupPartition')
    @patch('nextcloudBackup.NextcloudBackup.executeCommand')
    def test_main(self, mockExecuteCommand, mockMountBackupPartition, mockIsfile, mockStat, mockWalk, mockExists, mockGetmtime, mockShutil):
        mockStat.side_effect = [MagicMock(st_size=1), MagicMock(st_size=0)]
        mockIsfile.return_value = True
        mockExists.return_value = True
        mockWalk.return_value = [('/path/to/subdir/', 'dirs', ['file1.txt', 'file2.' + random.choice(self.IGNORED_FILE_TYPES)])]
        mockExecuteCommand.return_value = ''
        mockGetmtime.return_value = self.DUMMY_EPOCH_TIME

        # log file setup
        mainHandler = mock_open()
        mockLog = mock_open(read_data=self.OLD_DUMMY_DATE)
        mockError = mock_open()
        mockErroredFiles = mock_open()
        mainHandler.side_effect = [mockLog.return_value, mockError.return_value, mockErroredFiles.return_value]
        with patch('builtins.open', mainHandler):
            self.obj = NextcloudBackup(Namespace(dry_run=False, verbose=False))
            self.obj.main()
