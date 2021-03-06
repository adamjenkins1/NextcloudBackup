'''Contains NextcloudBackupTests class to test NextcloudBackup class'''

from unittest import TestCase
from unittest.mock import MagicMock, patch, mock_open
from argparse import Namespace
from contextlib import redirect_stdout, redirect_stderr
from io import StringIO
import os
import shutil
import datetime
from dateutil.relativedelta import relativedelta
from nextcloudBackup import NextcloudBackup

class NextcloudBackupTests(TestCase):
    '''Class containing tests to verify functionality of NextcloudBackup class'''
    OLD_DUMMY_DATE = NextcloudBackup.OLD_DUMMY_DATE
    DUMMY_EPOCH_TIME = 1535862436.9329703
    IGNORED_FILE_TYPES = NextcloudBackup.IGNORED_FILE_TYPES
    NEXTCLOUD_DATA = NextcloudBackup.NEXTCLOUD_DATA
    NEXTCLOUD_DATA_BACKUP = NextcloudBackup.NEXTCLOUD_DATA_BACKUP
    NEXTCLOUD_BACKUP_PARTITION = NextcloudBackup.NEXTCLOUD_BACKUP_PARTITION
    SAMPLE_ERRORED_FILES = ('{}\n{}\n'
                            .format(os.path.join(NEXTCLOUD_DATA, '/file/', '1.txt'),
                                    os.path.join(NEXTCLOUD_DATA, '/file/', '2.txt')))
    FAKE_FILES = ['file1.txt', 'file2.' + IGNORED_FILE_TYPES[-1]]

    class MockDatetime(datetime.datetime):
        '''Subclass of datetime.datetime with overridden now() for testing purposes'''
        @classmethod
        def now(cls, tz=None):
            '''Method to always return same time when called'''
            return datetime.datetime.fromtimestamp(NextcloudBackupTests.DUMMY_EPOCH_TIME)

    def setUp(self):
        '''Creates obj member before every test'''
        self.obj = object()

    def tearDown(self):
        '''Deletes obj member and its _instance property if it exists after every test'''
        if hasattr(self.obj, '_instance') and self.obj._instance is not None:
            del type(self.obj)._instance

        del self.obj

    @patch('os.stat', MagicMock(side_effect=[MagicMock(st_size=1), MagicMock(st_size=0)]))
    @patch('os.path.isfile', MagicMock(return_value=True))
    @patch('builtins.open', MagicMock())
    @patch('nextcloudBackup.NextcloudBackup.checkDataExists', MagicMock())
    @patch('nextcloudBackup.NextcloudBackup.mountBackupPartition', MagicMock())
    @patch('nextcloudBackup.NextcloudBackup.executeCommand', MagicMock(return_value=''))
    def test_sanity(self):
        '''Tests ability to create NextcloudBackup object correctly'''
        self.obj = NextcloudBackup(Namespace(verbose=False, dry_run=False))

    @patch('os.path.exists', MagicMock(return_value=False))
    @patch('nextcloudBackup.NextcloudBackup.openLogFile')
    def test_bad_nextcloud_data(self, mockOpenLogFile):
        '''Tests if SystemExit is raised when NEXTCLOUD_DATA doesn't exist'''
        mockOpenLogFile.side_effect = SystemExit('Did not raise SystemExit in checkDataExists()')
        with self.assertRaises(SystemExit) as err:
            self.obj = NextcloudBackup(Namespace(verbose=False, dry_run=False))

        self.assertEqual(err.exception.code, ('Error: Nextcloud data directory \'{}\' '
                                              'does not exist'.format(self.NEXTCLOUD_DATA)))

    @patch('os.path.exists', MagicMock(side_effect=[True, False]))
    @patch('nextcloudBackup.NextcloudBackup.openLogFile')
    def test_bad_nextcloud_data_backup(self, mockOpenLogFile):
        '''Tests if SystemExit is raised when NEXTCLOUD_DATA_BACKUP doesn't exist'''
        mockOpenLogFile.side_effect = SystemExit('Did not raise SystemExit in checkDataExists()')
        with self.assertRaises(SystemExit) as err:
            self.obj = NextcloudBackup(Namespace(verbose=False, dry_run=False))

        self.assertEqual(err.exception.code, ('Error: Nextcloud backup mount point \'{}\' '
                                              'does not exist'.format(self.NEXTCLOUD_DATA_BACKUP)))

    @patch('os.path.exists', MagicMock(return_value=True))
    @patch('nextcloudBackup.NextcloudBackup.executeCommand', MagicMock(return_value=''))
    @patch('nextcloudBackup.NextcloudBackup.openLogFile')
    def test_bad_nextcloud_backup_partition(self, mockOpenLogFile):
        '''Tests if SystemExit is raised when NEXTCLOUD_BACKUP_PARTITION doesn't exist'''
        mockOpenLogFile.side_effect = SystemExit('Did not raise SystemExit in checkDataExists()')
        with self.assertRaises(SystemExit) as err:
            self.obj = NextcloudBackup(Namespace(verbose=False, dry_run=False))

        self.assertEqual(err.exception.code, ('Error: Nextcloud backup partition \'{}\' does '
                                              'not exist'.format(self.NEXTCLOUD_BACKUP_PARTITION)))

    @patch('nextcloudBackup.NextcloudBackup.openLogFile')
    @patch('nextcloudBackup.NextcloudBackup.checkDataExists', MagicMock())
    def test_bad_args_object(self, mockOpenLogFile):
        '''Tests if SystemExit is raised when type of object passed isn't argparse.Namespace'''
        mockOpenLogFile.side_effect = SystemExit('Did not raise SystemExit in checkArgs()')
        with self.assertRaises(SystemExit) as err:
            self.obj = NextcloudBackup(MagicMock(verbose=False, dry_run=False))

        self.assertEqual(err.exception.code, ('Error: expected object of type '
                                              '\'argparse.Namespace\', received object of type '
                                              '\'<class \'unittest.mock.MagicMock\'>\''))

    @patch('nextcloudBackup.NextcloudBackup.openLogFile')
    @patch('nextcloudBackup.NextcloudBackup.checkDataExists', MagicMock())
    def test_missing_arg(self, mockOpenLogFile):
        '''Tests if SystemExit is raised if argument is missing'''
        mockOpenLogFile.side_effect = SystemExit('Did not raise SystemExit in checkArgs()')
        with self.assertRaises(SystemExit) as err:
            self.obj = NextcloudBackup(Namespace(dry_run=False))

        self.assertEqual(err.exception.code, ('Error: missing required attributes in '
                                              'Namespace object'))

    @patch('nextcloudBackup.NextcloudBackup.openLogFile')
    @patch('nextcloudBackup.NextcloudBackup.checkDataExists', MagicMock())
    def test_bad_arg_type(self, mockOpenLogFile):
        '''Tests if SystemExit is raised if arg type is not bool'''
        mockOpenLogFile.side_effect = SystemExit('Did not raise SystemExit in checkArgs()')
        with self.assertRaises(SystemExit) as err:
            self.obj = NextcloudBackup(Namespace(verbose=False, dry_run=1))

        self.assertEqual(err.exception.code, ('Error: expected property of type \'bool\', '
                                              'found type \'<class \'int\'>\''))

    @patch('os.stat', MagicMock(side_effect=[MagicMock(st_size=1), MagicMock(st_size=0)]))
    @patch('os.path.isfile', MagicMock(return_value=True))
    @patch('builtins.open', MagicMock())
    @patch('nextcloudBackup.NextcloudBackup.checkDataExists', MagicMock())
    @patch('nextcloudBackup.NextcloudBackup.mountBackupPartition', MagicMock())
    @patch('nextcloudBackup.NextcloudBackup.executeCommand', MagicMock(return_value=''))
    def test_set_verbosity_on_dry_run(self):
        '''Tests that verbose is set to True if dry_run = True'''
        self.obj = NextcloudBackup(Namespace(dry_run=True, verbose=False))
        self.assertTrue(self.obj.args.verbose)

    @patch('os.stat', MagicMock(side_effect=[MagicMock(st_size=0), MagicMock(st_size=1)]))
    @patch('os.path.isfile', MagicMock(return_value=False))
    @patch('nextcloudBackup.NextcloudBackup.checkDataExists', MagicMock())
    @patch('nextcloudBackup.NextcloudBackup.mountBackupPartition', MagicMock())
    @patch('nextcloudBackup.NextcloudBackup.executeCommand', MagicMock(return_value=''))
    def test_log_access(self):
        '''Tests that all logs are read from and written to properly'''
        # log file setup
        mainHandler = mock_open()
        mockLog = mock_open()
        mockError = mock_open()
        mockErroredFiles = mock_open(read_data=self.SAMPLE_ERRORED_FILES)
        mainHandler.side_effect = [
            mockLog.return_value,
            mockError.return_value,
            mockErroredFiles.return_value
        ]

        with patch('builtins.open', mainHandler):
            self.obj = NextcloudBackup(Namespace(dry_run=True, verbose=False))
            self.assertEqual(self.obj.toBackup, self.SAMPLE_ERRORED_FILES.split('\n')[:-1])
            mockLog().write.assert_called_once_with(self.OLD_DUMMY_DATE)

    @patch('os.path.exists', MagicMock(return_value=True))
    @patch('os.stat', MagicMock(side_effect=[MagicMock(st_size=1), MagicMock(st_size=0)]))
    @patch('os.path.isfile', MagicMock(return_value=True))
    @patch('nextcloudBackup.NextcloudBackup.checkDataExists', MagicMock())
    @patch('nextcloudBackup.NextcloudBackup.mountBackupPartition', MagicMock())
    @patch('nextcloudBackup.NextcloudBackup.executeCommand', MagicMock(return_value=''))
    @patch('shutil.copy2')
    @patch('os.walk')
    @patch('os.path.getmtime')
    def test_main(self, mockGetmtime, mockWalk, mockShutil):
        '''Tests that NextcloudBackup.main() can be run correctly'''
        mockGetmtime.return_value = self.DUMMY_EPOCH_TIME
        mockWalk.return_value = [(self.NEXTCLOUD_DATA, 'dirs', self.FAKE_FILES)]

        # log file setup
        mainHandler = mock_open()
        mockLog = mock_open(read_data=self.OLD_DUMMY_DATE)
        mockError = mock_open()
        mockErroredFiles = mock_open()
        mainHandler.side_effect = [
            mockLog.return_value,
            mockError.return_value,
            mockErroredFiles.return_value
        ]

        with patch('builtins.open', mainHandler):
            self.obj = NextcloudBackup(Namespace(dry_run=False, verbose=False))
            self.obj.main()
            self.assertEqual(mockShutil.call_count, 1)
            self.assertEqual(self.obj.toBackup,
                             [os.path.join(self.NEXTCLOUD_DATA, x) for x in self.FAKE_FILES])

    @patch('os.path.exists', MagicMock(side_effect=[False, True, True]))
    @patch('os.stat', MagicMock(side_effect=[MagicMock(st_size=1), MagicMock(st_size=0)]))
    @patch('os.path.isfile', MagicMock(return_value=True))
    @patch('nextcloudBackup.NextcloudBackup.checkDataExists', MagicMock())
    @patch('nextcloudBackup.NextcloudBackup.mountBackupPartition', MagicMock())
    @patch('nextcloudBackup.NextcloudBackup.executeCommand', MagicMock(return_value=''))
    @patch('shutil.copy2')
    @patch('os.walk')
    @patch('os.path.getmtime')
    def test_no_exist_copy(self, mockGetmtime, mockWalk, mockShutil):
        '''Tests that NextcloudBackup.main() can be run correctly'''
        olderDate = datetime.datetime.strptime(self.OLD_DUMMY_DATE.strip('\n'), '%c') - relativedelta(years=5)
        mockGetmtime.side_effect = [self.DUMMY_EPOCH_TIME, self.DUMMY_EPOCH_TIME, olderDate.timestamp()]
        mockWalk.return_value = [(self.NEXTCLOUD_DATA, 'dirs', self.FAKE_FILES + ['file3.png'])]

        # log file setup
        mainHandler = mock_open()
        mockLog = mock_open(read_data=self.OLD_DUMMY_DATE)
        mockError = mock_open()
        mockErroredFiles = mock_open()
        mainHandler.side_effect = [
            mockLog.return_value,
            mockError.return_value,
            mockErroredFiles.return_value
        ]

        with patch('builtins.open', mainHandler):
            self.obj = NextcloudBackup(Namespace(dry_run=False, verbose=False))
            self.obj.main()
            self.assertEqual(mockShutil.call_count, 2)
            self.assertEqual(self.obj.toBackup,
                             [os.path.join(self.NEXTCLOUD_DATA, x) for x in self.FAKE_FILES + ['file3.png']])

    @patch('os.makedirs', MagicMock())
    @patch('shutil.copy2', MagicMock())
    @patch('os.path.exists', MagicMock(side_effect=[False, True]))
    @patch('os.stat', MagicMock(side_effect=[MagicMock(st_size=1), MagicMock(st_size=0)]))
    @patch('os.path.isfile', MagicMock(return_value=True))
    @patch('nextcloudBackup.NextcloudBackup.checkDataExists', MagicMock())
    @patch('nextcloudBackup.NextcloudBackup.mountBackupPartition', MagicMock())
    @patch('nextcloudBackup.NextcloudBackup.executeCommand', MagicMock(return_value=''))
    @patch('os.walk')
    @patch('os.path.getmtime')
    def test_main_verbose(self, mockGetmtime, mockWalk):
        '''Tests if NextcloudBackup.main() verbose messages print correctly'''
        mockWalk.return_value = [(self.NEXTCLOUD_DATA, 'dirs', self.FAKE_FILES)]
        mockGetmtime.return_value = self.DUMMY_EPOCH_TIME

        # log file setup
        mainHandler = mock_open()
        mockLog = mock_open(read_data=self.OLD_DUMMY_DATE)
        mockError = mock_open()
        mockErroredFiles = mock_open()
        mainHandler.side_effect = [
            mockLog.return_value,
            mockError.return_value,
            mockErroredFiles.return_value
        ]
        out = StringIO()

        with patch('builtins.open', mainHandler):
            with redirect_stdout(out):
                self.obj = NextcloudBackup(Namespace(dry_run=False, verbose=True))
                self.obj.main()
                self.assertEqual(self.obj.toBackup,
                                 [os.path.join(self.NEXTCLOUD_DATA, x) for x in self.FAKE_FILES])
                self.assertEqual(out.getvalue(),
                                 ('creating \'{}\'\n\'{}\' --> \'{}\'\n'
                                  .format(self.NEXTCLOUD_DATA_BACKUP,
                                          os.path.join(self.NEXTCLOUD_DATA, self.FAKE_FILES[0]),
                                          os.path.join(self.NEXTCLOUD_DATA_BACKUP,
                                                       self.FAKE_FILES[0]))))

    @patch('datetime.datetime', MockDatetime)
    @patch('os.makedirs', MagicMock())
    @patch('shutil.copy2', MagicMock(side_effect=Exception('FAKE ERROR')))
    @patch('os.path.exists', MagicMock(side_effect=[False, True]))
    @patch('os.stat', MagicMock(side_effect=[MagicMock(st_size=1), MagicMock(st_size=0)]))
    @patch('os.path.isfile', MagicMock(return_value=True))
    @patch('nextcloudBackup.NextcloudBackup.checkDataExists', MagicMock())
    @patch('nextcloudBackup.NextcloudBackup.mountBackupPartition', MagicMock())
    @patch('nextcloudBackup.NextcloudBackup.executeCommand', MagicMock(return_value=''))
    @patch('os.walk')
    @patch('os.path.getmtime')
    def test_main_copy_errors(self, mockGetmtime, mockWalk):
        '''Tests if copy errors are reported correctly'''
        mockWalk.return_value = [(self.NEXTCLOUD_DATA, 'dirs', self.FAKE_FILES)]
        mockGetmtime.return_value = self.DUMMY_EPOCH_TIME

        # log file setup
        mainHandler = mock_open()
        mockLog = mock_open(read_data=self.OLD_DUMMY_DATE)
        mockError = mock_open()
        mockErroredFiles = mock_open()
        mainHandler.side_effect = [
            mockLog.return_value,
            mockError.return_value,
            mockErroredFiles.return_value
        ]
        out = err = StringIO()
        errorMessage = ('{}: caught error \'FAKE ERROR\' while attempting to copy \'{}\'\n'
                        .format(datetime.datetime.fromtimestamp(self.DUMMY_EPOCH_TIME).strftime('%c'),
                                os.path.join(self.NEXTCLOUD_DATA_BACKUP, self.FAKE_FILES[0])))

        with patch('builtins.open', mainHandler):
            with redirect_stderr(err):
                self.obj = NextcloudBackup(Namespace(dry_run=False, verbose=True))
                self.obj.main()
                self.assertEqual(self.obj.toBackup,
                                 [os.path.join(self.NEXTCLOUD_DATA, x) for x in self.FAKE_FILES])
                self.assertEqual(err.getvalue(), errorMessage)
                mockError().write.assert_called_once_with(errorMessage)
                mockErroredFiles().write.assert_called_once_with('{}\n'.format(os.path.join(self.NEXTCLOUD_DATA, self.FAKE_FILES[0])))

    @patch('nextcloudBackup.NextcloudBackup.__init__')
    def test_singleton_behavior(self, mockInit):
        '''Tests if NextcloudBackup acts like a singleton'''
        mockInit.return_value = None
        self.obj = NextcloudBackup()
        obj2 = NextcloudBackup()

        self.assertTrue(self.obj is obj2)
        self.assertEqual(mockInit.call_count, 1)

    @patch('datetime.datetime', MockDatetime)
    @patch('os.stat', MagicMock(side_effect=[MagicMock(st_size=1), MagicMock(st_size=0)]))
    @patch('os.path.isfile', MagicMock(return_value=True))
    @patch('nextcloudBackup.NextcloudBackup.checkDataExists', MagicMock())
    @patch('nextcloudBackup.NextcloudBackup.mountBackupPartition', MagicMock())
    @patch('nextcloudBackup.NextcloudBackup.executeCommand', MagicMock(return_value=''))
    def test_tear_down(self):
        '''Tests that NextcloudBackup.tearDown() closes log files and records time in main log'''
        # log file setup
        mainHandler = mock_open()
        mockLog = mock_open(read_data=self.OLD_DUMMY_DATE)
        mockError = mock_open()
        mockErroredFiles = mock_open()
        mainHandler.side_effect = [
            mockLog.return_value,
            mockError.return_value,
            mockErroredFiles.return_value
        ]

        with patch('builtins.open', mainHandler):
            self.obj = NextcloudBackup(Namespace(dry_run=False, verbose=False))
            self.obj.tearDown()
            mockLog().write.assert_called_once_with('{}\n'.format(datetime.datetime.fromtimestamp(self.DUMMY_EPOCH_TIME).strftime('%c')))
            for log in [mockLog(), mockError(), mockErroredFiles()]:
                self.assertTrue(log.close.called)

    @patch('os.stat', MagicMock(side_effect=[MagicMock(st_size=1), MagicMock(st_size=0)]))
    @patch('os.path.isfile', MagicMock(return_value=True))
    @patch('builtins.open', MagicMock())
    @patch('nextcloudBackup.NextcloudBackup.checkDataExists', MagicMock())
    @patch('nextcloudBackup.NextcloudBackup.mountBackupPartition', MagicMock())
    @patch('nextcloudBackup.NextcloudBackup.executeCommand', MagicMock(return_value=''))
    @patch('nextcloudBackup.NextcloudBackup.tearDown')
    def test_context_manager_usage(self, mockTearDown):
        '''Tests context manager usage with NextcloudBackup object'''
        with NextcloudBackup(Namespace(verbose=False, dry_run=False)) as self.obj:
            self.assertTrue(isinstance(self.obj, NextcloudBackup))

        self.assertTrue(mockTearDown.called)
