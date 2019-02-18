#!/usr/bin/env python3
from unittest import TestCase, mock, skip
from unittest.mock import MagicMock, patch, mock_open
from argparse import Namespace
from contextlib import redirect_stdout, redirect_stderr
from io import StringIO
import os
import shutil
import datetime
from nextcloudBackup import NextcloudBackup

class NextcloudBackupTests(TestCase):
    OLD_DUMMY_DATE = NextcloudBackup.OLD_DUMMY_DATE
    DUMMY_EPOCH_TIME = 1535862436.9329703
    IGNORED_FILE_TYPES = NextcloudBackup.IGNORED_FILE_TYPES
    NEXTCLOUD_DATA = NextcloudBackup.NEXTCLOUD_DATA
    NEXTCLOUD_DATA_BACKUP = NextcloudBackup.NEXTCLOUD_DATA_BACKUP
    NEXTCLOUD_BACKUP_PARTITION = NextcloudBackup.NEXTCLOUD_BACKUP_PARTITION
    SAMPLE_ERRORED_FILES = '{}\n{}\n'.format(os.path.join(NEXTCLOUD_DATA, '/file/', '1.txt'), os.path.join(NEXTCLOUD_DATA, '/file/', '2.txt'))
    FAKE_FILES = ['file1.txt', 'file2.' + IGNORED_FILE_TYPES[-1]]

    class MockDatetime(datetime.datetime):
        def now():
            return datetime.datetime.fromtimestamp(NextcloudBackupTests.DUMMY_EPOCH_TIME)

    def setUp(self):
        self.obj = object()

    def tearDown(self):
        if hasattr(self.obj, '_instance') and self.obj._instance is not None:
            del type(self.obj)._instance

        del self.obj

    @patch('os.stat')
    @patch('os.path.isfile')
    @patch('builtins.open', new_callable=mock_open())
    @patch('nextcloudBackup.NextcloudBackup.checkDataExists')
    @patch('nextcloudBackup.NextcloudBackup.mountBackupPartition')
    @patch('nextcloudBackup.NextcloudBackup.executeCommand')
    def test_sanity(self, mockExecuteCommand, mockMountBackupPartition, mockCheckExists, mockOpen, mockIsfile, mockStat):
        mockStat.side_effect = [MagicMock(st_size=1), MagicMock(st_size=0)]
        mockIsfile.return_value = True
        mockExecuteCommand.return_value = ''
        self.obj = NextcloudBackup(Namespace(verbose=False, dry_run=False))

    @patch('os.path.exists')
    @patch('nextcloudBackup.NextcloudBackup.checkArgs')
    def test_bad_nextcloud_data(self, mockCheckArgs, mockExists):
        mockCheckArgs.side_effect = SystemExit('Did not raise SystemExit in checkDataExists()')
        mockExists.return_value = False
        with self.assertRaises(SystemExit) as err:
            self.obj = NextcloudBackup(Namespace(verbose=False, dry_run=False))

        self.assertEqual(err.exception.code, 'Error: Nextcloud data directory \'{}\' does not exist'.format(self.NEXTCLOUD_DATA))

    @patch('os.path.exists')
    @patch('nextcloudBackup.NextcloudBackup.checkArgs')
    def test_bad_nextcloud_data_backup(self, mockCheckArgs, mockExists):
        mockCheckArgs.side_effect = SystemExit('Did not raise SystemExit in checkDataExists()')
        mockExists.side_effect = [True, False]
        with self.assertRaises(SystemExit) as err:
            self.obj = NextcloudBackup(Namespace(verbose=False, dry_run=False))

        self.assertEqual(err.exception.code, 'Error: Nextcloud backup mount point \'{}\' does not exist'.format(self.NEXTCLOUD_DATA_BACKUP))

    @patch('os.path.exists')
    @patch('nextcloudBackup.NextcloudBackup.checkArgs')
    @patch('nextcloudBackup.NextcloudBackup.executeCommand')
    def test_bad_nextcloud_backup_partition(self, mockExecuteCommand, mockCheckArgs, mockExists):
        mockCheckArgs.side_effect = SystemExit('Did not raise SystemExit in checkDataExists()')
        mockExists.return_value = True
        mockExecuteCommand.return_value = ''
        with self.assertRaises(SystemExit) as err:
            self.obj = NextcloudBackup(Namespace(verbose=False, dry_run=False))

        self.assertEqual(err.exception.code, 'Error: Nextcloud backup partition \'{}\' does not exist'.format(self.NEXTCLOUD_BACKUP_PARTITION))

    @patch('nextcloudBackup.NextcloudBackup.openLogFile')
    @patch('nextcloudBackup.NextcloudBackup.checkDataExists')
    def test_bad_args_object(self, mockCheckExists, mockOpenLogFile):
        mockOpenLogFile.side_effect = SystemExit('Did not raise SystemExit in checkArgs()')

        with self.assertRaises(SystemExit) as err:
            self.obj = NextcloudBackup(MagicMock(verbose=False, dry_run=False))

        self.assertEqual(err.exception.code, 'Error: expected object of type \'argparse.Namespace\', received object of type \'<class \'unittest.mock.MagicMock\'>\'')

    @patch('nextcloudBackup.NextcloudBackup.openLogFile')
    @patch('nextcloudBackup.NextcloudBackup.checkDataExists')
    def test_missing_arg(self, mockCheckExists, mockOpenLogFile):
        mockOpenLogFile.side_effect = SystemExit('Did not raise SystemExit in checkArgs()')

        with self.assertRaises(SystemExit) as err:
            self.obj = NextcloudBackup(Namespace(dry_run=False))

        self.assertEqual(err.exception.code, 'Error: missing required attributes in Namespace object')

    @patch('nextcloudBackup.NextcloudBackup.openLogFile')
    @patch('nextcloudBackup.NextcloudBackup.checkDataExists')
    def test_bad_arg_type(self, mockCheckExists, mockOpenLogFile):
        mockOpenLogFile.side_effect = SystemExit('Did not raise SystemExit in checkArgs()')

        with self.assertRaises(SystemExit) as err:
            self.obj = NextcloudBackup(Namespace(verbose=False, dry_run=1))

        self.assertEqual(err.exception.code, 'Error: expected property of type \'bool\', found type \'<class \'int\'>\'')

    @patch('os.stat')
    @patch('os.path.isfile')
    @patch('builtins.open', new_callable=mock_open())
    @patch('nextcloudBackup.NextcloudBackup.checkDataExists')
    @patch('nextcloudBackup.NextcloudBackup.mountBackupPartition')
    @patch('nextcloudBackup.NextcloudBackup.executeCommand')
    def test_set_verbosity_on_dry_run(self, mockExecuteCommand, mockMountBackupPartition, mockCheckExists, mockOpen, mockIsfile, mockStat):
        mockStat.side_effect = [MagicMock(st_size=1), MagicMock(st_size=0)]
        mockIsfile.return_value = True
        mockExecuteCommand.return_value = ''
        self.obj = NextcloudBackup(Namespace(dry_run=True, verbose=False))
        self.assertTrue(self.obj.args.verbose)

    @patch('os.stat')
    @patch('os.path.isfile')
    @patch('nextcloudBackup.NextcloudBackup.checkDataExists')
    @patch('nextcloudBackup.NextcloudBackup.mountBackupPartition')
    @patch('nextcloudBackup.NextcloudBackup.executeCommand')
    def test_log_access(self, mockExecuteCommand, mockMountBackupPartition, mockCheckExists, mockIsfile, mockStat):
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

    @patch('shutil.copy2')
    @patch('os.path.getmtime')
    @patch('os.path.exists')
    @patch('os.walk')
    @patch('os.stat')
    @patch('os.path.isfile')
    @patch('nextcloudBackup.NextcloudBackup.checkDataExists')
    @patch('nextcloudBackup.NextcloudBackup.mountBackupPartition')
    @patch('nextcloudBackup.NextcloudBackup.executeCommand')
    def test_main(self, mockExecuteCommand, mockMountBackupPartition, mockCheckExists, mockIsfile, mockStat, mockWalk, mockExists, mockGetmtime, mockShutil):
        mockStat.side_effect = [MagicMock(st_size=1), MagicMock(st_size=0)]
        mockIsfile.return_value = True
        mockExists.return_value = True
        mockWalk.return_value = [(self.NEXTCLOUD_DATA, 'dirs', self.FAKE_FILES)]
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
            self.assertEqual(self.obj.toBackup, [os.path.join(self.NEXTCLOUD_DATA, x) for x in self.FAKE_FILES])

    @patch('os.makedirs')
    @patch('shutil.copy2')
    @patch('os.path.getmtime')
    @patch('os.path.exists')
    @patch('os.walk')
    @patch('os.stat')
    @patch('os.path.isfile')
    @patch('nextcloudBackup.NextcloudBackup.checkDataExists')
    @patch('nextcloudBackup.NextcloudBackup.mountBackupPartition')
    @patch('nextcloudBackup.NextcloudBackup.executeCommand')
    def test_main_verbose(self, mockExecuteCommand, mockMountBackupPartition, mockCheckExists, mockIsfile, mockStat, mockWalk, mockExists, mockGetmtime, mockShutil, mockMakedirs):
        mockStat.side_effect = [MagicMock(st_size=1), MagicMock(st_size=0)]
        mockIsfile.return_value = True
        mockExists.side_effect = [False, True]
        mockWalk.return_value = [(self.NEXTCLOUD_DATA, 'dirs', self.FAKE_FILES)]
        mockExecuteCommand.return_value = ''
        mockGetmtime.return_value = self.DUMMY_EPOCH_TIME

        # log file setup
        mainHandler = mock_open()
        mockLog = mock_open(read_data=self.OLD_DUMMY_DATE)
        mockError = mock_open()
        mockErroredFiles = mock_open()
        mainHandler.side_effect = [mockLog.return_value, mockError.return_value, mockErroredFiles.return_value]
        out = StringIO()

        with patch('builtins.open', mainHandler):
            with redirect_stdout(out):
                self.obj = NextcloudBackup(Namespace(dry_run=False, verbose=True))
                self.obj.main()
                self.assertEqual(self.obj.toBackup, [os.path.join(self.NEXTCLOUD_DATA, x) for x in self.FAKE_FILES])
                self.assertEqual(out.getvalue(), 'creating \'{}\'\n\'{}\' --> \'{}\'\n'.format(self.NEXTCLOUD_DATA_BACKUP, os.path.join(self.NEXTCLOUD_DATA, self.FAKE_FILES[0]), os.path.join(self.NEXTCLOUD_DATA_BACKUP, self.FAKE_FILES[0])))

    @patch('datetime.datetime', MockDatetime)
    @patch('os.makedirs')
    @patch('shutil.copy2')
    @patch('os.path.getmtime')
    @patch('os.path.exists')
    @patch('os.walk')
    @patch('os.stat')
    @patch('os.path.isfile')
    @patch('nextcloudBackup.NextcloudBackup.checkDataExists')
    @patch('nextcloudBackup.NextcloudBackup.mountBackupPartition')
    @patch('nextcloudBackup.NextcloudBackup.executeCommand')
    def test_main_copy_errors(self, mockExecuteCommand, mockMountBackupPartition, mockCheckExists, mockIsfile, mockStat, mockWalk, mockExists, mockGetmtime, mockShutil, mockMakedirs):
        mockStat.side_effect = [MagicMock(st_size=1), MagicMock(st_size=0)]
        mockIsfile.return_value = True
        mockExists.side_effect = [False, True]
        mockWalk.return_value = [(self.NEXTCLOUD_DATA, 'dirs', self.FAKE_FILES)]
        mockExecuteCommand.return_value = ''
        mockGetmtime.return_value = self.DUMMY_EPOCH_TIME
        mockShutil.side_effect = Exception('FAKE ERROR')

        # log file setup
        mainHandler = mock_open()
        mockLog = mock_open(read_data=self.OLD_DUMMY_DATE)
        mockError = mock_open()
        mockErroredFiles = mock_open()
        mainHandler.side_effect = [mockLog.return_value, mockError.return_value, mockErroredFiles.return_value]
        out = err = StringIO()
        errorMessage = '{}: caught error \'FAKE ERROR\' while attempting to copy \'{}\'\n'.format(datetime.datetime.fromtimestamp(self.DUMMY_EPOCH_TIME).strftime('%c'), os.path.join(self.NEXTCLOUD_DATA_BACKUP, self.FAKE_FILES[0]))

        with patch('builtins.open', mainHandler):
            with redirect_stderr(err):
                self.obj = NextcloudBackup(Namespace(dry_run=False, verbose=True))
                self.obj.main()
                self.assertEqual(self.obj.toBackup, [os.path.join(self.NEXTCLOUD_DATA, x) for x in self.FAKE_FILES])
                self.assertEqual(err.getvalue(), errorMessage)
                mockError().write.assert_called_once_with(errorMessage)
                mockErroredFiles().write.assert_called_once_with(os.path.join(self.NEXTCLOUD_DATA, self.FAKE_FILES[0]) + '\n')

    def test_singleton_behavior(self):
        oldInit = NextcloudBackup.__init__
        NextcloudBackup.__init__ = lambda self: print('constructor called')
        out = StringIO()

        with redirect_stdout(out):
            self.obj = NextcloudBackup()
            obj2 = NextcloudBackup()

        self.assertTrue(self.obj is obj2)
        self.assertEqual(out.getvalue(), 'constructor called\n')

        NextcloudBackup.__init__ = oldInit

    @patch('datetime.datetime', MockDatetime)
    @patch('os.stat')
    @patch('os.path.isfile')
    @patch('nextcloudBackup.NextcloudBackup.checkDataExists')
    @patch('nextcloudBackup.NextcloudBackup.mountBackupPartition')
    @patch('nextcloudBackup.NextcloudBackup.executeCommand')
    def test_tear_down(self, mockExecuteCommand, mockMountBackupPartition, mockCheckExists, mockIsfile, mockStat):
        mockStat.side_effect = [MagicMock(st_size=1), MagicMock(st_size=0)]
        mockExecuteCommand.return_value = ''
        mockIsfile.return_value = True

        # log file setup
        mainHandler = mock_open()
        mockLog = mock_open(read_data=self.OLD_DUMMY_DATE)
        mockError = mock_open()
        mockErroredFiles = mock_open()
        mainHandler.side_effect = [mockLog.return_value, mockError.return_value, mockErroredFiles.return_value]
        with patch('builtins.open', mainHandler):
            self.obj = NextcloudBackup(Namespace(dry_run=False, verbose=False))
            self.obj.tearDown()
            mockLog().write.assert_called_once_with('{}\n'.format(datetime.datetime.fromtimestamp(self.DUMMY_EPOCH_TIME).strftime('%c')))
            for log in [mockLog(), mockError(), mockErroredFiles()]:
                log.close.assert_called_once()
