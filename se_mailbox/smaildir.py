# -*- coding: utf-8 -*-

"""Read/write support for Maildir mailboxes."""

import os
import time
import mailbox

import scandir

__all__ = ('Maildir', 'scandir')


class Maildir(mailbox.Maildir):
    """A qmail-style Maildir mailbox.

    Uses scandir() rather than listdir().

    Also provides a new iter_folders() method that works like
    list_folders() but provides a generator rather than returning a
    list.
    """

    def list_folders(self):
        """Return a list of folder names."""
        return list(self.iter_folders())

    def iter_folders(self):
        """Return a generator of folder names."""
        for entry in scandir.scandir(self._path):
            entry = entry.name
            if len(entry) > 1 and entry[0] == '.' and \
               os.path.isdir(os.path.join(self._path, entry)):
                yield entry[1:]

    def remove_folder(self, folder):
        """Delete the named folder, which must be empty."""
        path = os.path.join(self._path, '.' + folder)
        for entry in scandir.scandir(os.path.join(path, 'new')):
            if len(entry.name) < 1 or entry.name[0] != '.':
                raise mailbox.NotEmptyError('Folder contains message(s): %s' %
                                            folder)
        for entry in scandir.scandir(os.path.join(path, 'cur')):
            if len(entry.name) < 1 or entry.name[0] != '.':
                raise mailbox.NotEmptyError('Folder contains message(s): %s' %
                                            folder)
        for entry in scandir.scandir(path):
            if (entry.name != 'new' and entry.name != 'cur'
                    and entry.name != 'tmp' and entry.is_dir()):
                raise mailbox.NotEmptyError("Folder contains subdirectory "
                                            "'%s': %s" % (folder, entry))
        for root, dirs, files in scandir.walk(path, topdown=False):
            for entry in files:
                os.remove(os.path.join(root, entry))
            for entry in dirs:
                os.rmdir(os.path.join(root, entry))
        os.rmdir(path)

    def clean(self):
        """Delete old files in "tmp"."""
        now = time.time()
        for entry in scandir.scandir(os.path.join(self._path, 'tmp')):
            entry = entry.name
            path = os.path.join(self._path, 'tmp', entry)
            if now - os.path.getatime(path) > 129600:  # 60 * 60 * 36
                os.remove(path)

    def _refresh(self):
        """Update table of contents mapping."""
        # If it has been less than two seconds since the last _refresh() call,
        # we have to unconditionally re-read the mailbox just in case it has
        # been modified, because os.path.mtime() has a 2 sec resolution in the
        # most common worst case (FAT) and a 1 sec resolution typically.  This
        # results in a few unnecessary re-reads when _refresh() is called
        # multiple times in that interval, but once the clock ticks over, we
        # will only re-read as needed.  Because the filesystem might be being
        # served by an independent system with its own clock, we record and
        # compare with the mtimes from the filesystem.  Because the other
        # system's clock might be skewing relative to our clock, we add an
        # extra delta to our wait.  The default is one tenth second, but is an
        # instance variable and so can be adjusted if dealing with a
        # particularly skewed or irregular system.
        if time.time() - self._last_read > 2 + self._skewfactor:
            refresh = False
            for subdir in self._toc_mtimes:
                mtime = os.path.getmtime(self._paths[subdir])
                if mtime > self._toc_mtimes[subdir]:
                    refresh = True
                self._toc_mtimes[subdir] = mtime
            if not refresh:
                return
        # Refresh toc
        self._toc = {}
        for subdir in self._toc_mtimes:
            path = self._paths[subdir]
            for entry in scandir.scandir(path):
                if entry.is_dir():
                    continue
                entry = entry.name
                uniq = entry.split(self.colon)[0]
                self._toc[uniq] = os.path.join(subdir, entry)
        self._last_read = time.time()
