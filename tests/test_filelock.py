import unittest
from mock import patch, MagicMock

from se_mailbox import filelock


class TestFileLock(unittest.TestCase):
    """"""

    def setUp(self):
        pass

    def tearDown(self):
        patch.stopall()

    def test_acquire(self):
        """Test that we can't acquire a lock on the same file """
        f1 = filelock.FileLock("filename")
        f2 = filelock.FileLock("filename", timeout=0.1)

        f1.acquire()

        try:
            with self.assertRaises(filelock.FileLockException):
                f2.acquire()
        except AssertionError:
            raise
        finally:
            f1.release()

    def test_context_locking(self):
        """Test that using a FileLock object in a context will call
        acquire and release upon enter and exit."""
        tested_obj = filelock.FileLock("filename")
        tested_obj.acquire = MagicMock()
        tested_obj.release = MagicMock()

        with tested_obj:
            # the acquire method should have set this
            # release will not be called if is_locked is not True
            tested_obj.is_locked = True

        tested_obj.acquire.assert_called_once()
        tested_obj.release.assert_called_once()



