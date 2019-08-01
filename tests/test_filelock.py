import unittest
from mock import patch, MagicMock

from se_mailbox import filelock


class TestFileLock(unittest.TestCase):
    """"""

    def setUp(self):
        self.tested_obj = filelock.FileLock("filename")

    def tearDown(self):
        self.tested_obj.release()
        patch.stopall()

    def test_acquire(self):
        """Test that we can't acquire a lock on the same file."""
        f2 = filelock.FileLock("filename", timeout=0.1)

        self.tested_obj.acquire()

        with self.assertRaises(filelock.FileLockException):
            f2.acquire()

    def test_context_locking(self):
        """Test that using a FileLock object in a context
        will call acquire and release upon enter and exit."""
        self.tested_obj.acquire = MagicMock()
        self.tested_obj.release = MagicMock()

        with self.tested_obj:
            # the acquire method should have set this
            # release will not be called if is_locked is not True
            self.tested_obj.is_locked = True

        self.tested_obj.acquire.assert_called_once()
        self.tested_obj.release.assert_called_once()



