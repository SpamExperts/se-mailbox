# -*- coding: utf-8 -*-

"""A file-lock mechanism."""

# BSD license, sourced from:
# http://www.evanfosmark.com/2009/01/cross-platform-file-locking-support-in-python/
#
# Modified to work with Python 2.5 by changing the exception catching.

import os
import time
import fcntl
import errno


class FileLockException(Exception):
    """Something went wrong while locking the file."""
    pass


class FileLock(object):
    """A file locking mechanism that has context-manager support so
    you can use it in a with statement.
    """

    def __init__(self, file_name, timeout=10, delay=0.05, base=None):
        """Prepare the file locker. Specify the file to lock and optionally
        the maximum timeout and the delay between each attempt to lock."""
        if base is None:
            base = os.getcwd()
        self.is_locked = False
        self.lockfile = os.path.join(base, "%s.lock" % file_name)
        self.file_name = file_name
        self.timeout = timeout
        self.delay = delay
        self.fd = None

    def acquire(self):
        """Acquire the lock, if possible. If the lock is in use, it check
        again every `wait` seconds. It does this until it either gets the
        lock or exceeds `timeout` number of seconds, in which case it throws
        an exception."""
        start_time = time.time()
        while True:
            try:
                self.fd = open(self.lockfile, "w+b")
                fcntl.flock(self.fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except (OSError, IOError) as e:
                if e.errno != errno.EWOULDBLOCK:
                    raise
                if (time.time() - start_time) >= self.timeout:
                    raise FileLockException("Timeout occurred.")
                time.sleep(self.delay)
            else:
                break
        self.is_locked = True

    def release(self):
        """Get rid of the lock by deleting the lockfile.
        When working in a `with` statement, this gets automatically called
        at the end."""
        if hasattr(self, "is_locked") and self.is_locked:
            try:
                self.fd.close()
                os.unlink(self.lockfile)
            except OSError as e:
                if e.errno != errno.ENOENT:
                    raise
            self.is_locked = False

    def __enter__(self):
        """Activated when used in the with statement.
        Should automatically acquire a lock to be used in the with block.
        """
        if not self.is_locked:
            self.acquire()
        return self

    def __exit__(self, exit_type, value, traceback):
        """Activated at the end of the with statement.
        It automatically releases the lock if it isn't locked."""
        if self.is_locked:
            self.release()

    def __del__(self):
        """Make sure that the FileLock instance doesn't leave a lockfile
        lying around."""
        self.release()
