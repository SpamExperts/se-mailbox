# -*- coding: utf-8 -*-

"""A file-lock mechanism."""

# BSD license, sourced from:
# http://www.evanfosmark.com/2009/01/cross-platform-file-locking-support-in-python/
#
# Modified to work with Python 2.5 by changing the exception catching.

import os
import time
import errno


class FileLockException(Exception):
    """Something went wrong while locking the file."""
    pass


class FileLock(object):
    """A file locking mechanism that has context-manager support so
    you can use it in a with statement. This should be relatively cross
    compatible as it doesn't rely on msvcrt or fcntl for the locking."""

    def __init__(self, file_name, timeout=10, delay=0.05, base=None,
                 max_age=None):
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
        if max_age and os.path.exists(self.lockfile):
            # If the lock file is older than this, then remove it (we
            # assume that the lock failed to be released when the process
            # that acquired it completed).  If the lock file is removed
            # during this check, nothing is wrong.
            try:
                if time.time() - os.stat(self.lockfile).st_mtime > max_age:
                    os.remove(self.lockfile)
            except OSError:
                pass

    def acquire(self):
        """Acquire the lock, if possible. If the lock is in use, it check
        again every `wait` seconds. It does this until it either gets the
        lock or exceeds `timeout` number of seconds, in which case it throws
        an exception."""
        start_time = time.time()
        while True:
            try:
                self.fd = os.open(self.lockfile,
                                  os.O_CREAT | os.O_EXCL | os.O_RDWR)
            except OSError as e:
                if e.errno != errno.EEXIST:
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
            os.close(self.fd)
            os.unlink(self.lockfile)
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
