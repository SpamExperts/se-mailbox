# -*- coding: utf-8 -*-

"""QuotaMaildir class.

Both archiving and filtering on a logging server require calculation of the
size of the Maildir mailboxes that we use.  There is an existing
specification as part of the Maildir++ format, but the mailbox library does
not include this.  This class extends the standard mailbox.Maildir class
to add quota functionality (although we do not currently use the Maildir++
quotas).

As much as possible we follow the specification, so that we correctly
interact with other users (e.g. Dovecot), although we have a few changes
where it does not matter for our purposes.
"""

import os
import stat
import time
import mailbox

import scandir

from . import filelock
from . import smaildir


class QuotaMixin(object):
    """Implements the Maildir++ quota size system, as described here:

    http://www.inter7.com/courierimap/README.maildirquota.html

    Quotas are not enforced - this would be good to add, but since we do
    a non-standard operation (dropping old data instead of failing to add)
    there's not much point."""

    def __init__(self):
        self.size_fn = os.path.join(self._path, "maildirsize")
        self.size_quota = None
        self.count_quota = None
        self.get_quota()

    def recalculate(self):
        """Recalculate the space used by this folder, and store in the
        maildirsize cache."""
        # We are meant to look for a "maildirfolder" file in the current
        # directory, and if there is one, then this is a subfolder and we
        # should move up one directory.  However, that doesn't suit our
        # purposes and we only work with top-level folders, so skip that
        # part of the specification.  We are also meant to stat() each
        # subdirectory and only record the counts if the modification time
        # at the end of the calculation hasn't changed since the start. We
        # are not that concerned with being exact, so we skip that too.
        total_size = 0
        total_count = 0
        for folder in ("cur", "new"):
            for filename in scandir.scandir(os.path.join(self._path, folder)):
                full_fn = os.path.join(self._path, folder, filename.name)
                total_count += 1
                # The Maildir++ format allows the size of the message to
                # be stored in the filename with a 'S=nnnn' format, along
                # with the Maildir flags.  However, the specification is
                # not clear on exactly how this is meant to be laid out.
                # In any case, the Python maildir class doesn't write this
                # data out, so we would need to add it there as well for it
                # to be of any use.  We will just use stat() to get the
                # size.
                total_size += os.stat(full_fn).st_size
        for subfolder in self.list_folders():
            if subfolder == "Trash":
                continue
            size, count = self.get_folder(subfolder).recalculate()
            total_size += size
            total_count += count
        self.get_quota()
        quotas = ["%d%s" % (q, l)
                  for l, q in (("S", self.size_quota),
                               ("C", self.count_quota)) if q]
        # This is meant to use the same temp file generation and then
        # renaming that Maildir uses, but (a) that doesn't actually
        # prevent clashes, and (b) we are going to override how that works
        # later on anyway.
        try:
            with filelock.FileLock(self.size_fn):
                size = open(self.size_fn, "w")
                size.write(",".join(quotas) + "\n")
                size.write("%d %d\n" % (total_size, total_count))
                size.close()
        except filelock.FileLockException:
            # Timed out - skip writing the file, and trust that it will get
            # regenerated later (when the file is not busy).
            pass
        return total_size, total_count

    def add(self, message, key):
        """Add a message to the folder, recording the space used."""
        filename = super(QuotaMixin, self).add(message, key)
        full_fn = os.path.join(self._path, self._lookup(filename))
        msg_size = os.stat(full_fn).st_size
        try:
            with filelock.FileLock(self.size_fn):
                if os.path.exists(self.size_fn):
                    size = open(self.size_fn, "a")
                else:
                    size = open(self.size_fn, "w")
                    size.write("%s %s\n" % (self.size_quota or "",
                                            self.count_quota or ""))
                size.write("%d 1\n" % msg_size)
                size.close()
        except filelock.FileLockException:
            # Timed out - skip writing the new data, and rely on the
            # periodic recalculation to fix the error.
            pass
        return filename, msg_size

    def stat_msg(self, key):
        """Stat the message stored under this key."""
        full_fn = os.path.join(self._path, self._lookup(key))
        return os.stat(full_fn)

    def remove(self, key):
        """Remove a message from the folder, recording the space freed."""
        full_fn = os.path.join(self._path, self._lookup(key))
        msg_size = os.stat(full_fn).st_size
        try:
            with filelock.FileLock(self.size_fn):
                size = open(self.size_fn, "a")
                size.write("-%d -1\n" % msg_size)
                size.close()
        except filelock.FileLockException:
            # Timed out - skip writing the new data, and rely on the
            # periodic recalculation to fix the error.
            pass
        super(QuotaMixin, self).remove(key)
        return msg_size

    def size(self):
        """Get the size of the folder (bytes, number of messages)."""
        if not os.path.exists(self.size_fn):
            return self.recalculate()
        size_stat = os.stat(self.size_fn)
        if size_stat.st_size > 5120:
            return self.recalculate()
        i = 0
        total_size = 0
        total_count = 0
        for i, line in enumerate(open(self.size_fn).readlines()[1:]):
            size, count = line.split()
            total_size += int(size)
            total_count += int(count)
        if (((self.count_quota and total_count > self.count_quota) or
             (self.size_quota and total_size > self.size_quota)) and
                (i == 0 or (time.time() - size_stat.st_mtime) > 15 * 60)):
            return self.recalculate()
        return total_size, total_count

    def get_quota(self):
        """Load the size_quota and count_quota for this folder."""
        self.size_quota = None
        self.count_quota = None
        if not os.path.exists(self.size_fn):
            return
        try:
            with open(self.size_fn, "r") as size:
                quotas = size.readline().strip().split(",")
        except OSError:
            # Either the file is invalid or another process is updating
            # it right now.
            return
        for quota in quotas:
            if not quota:
                continue
            if quota[-1] == "S":
                self.size_quota = int(quota[:-1])
            elif quota[-1] == "C":
                self.count_quota = int(quota[:-1])

    def set_quota(self, size_quota, count_quota):
        """Set the size_quota and count_quota for this folder."""
        self.size_quota = size_quota
        self.count_quota = count_quota
        quotas = ["%d%s" % (q, l)
                  for l, q in (("S", size_quota), ("C", count_quota)) if q]
        with filelock.FileLock(self.size_fn):
            if os.path.exists(self.size_fn):
                size = open(self.size_fn, "r")
                lines = size.readlines()
                size.close()
            else:
                lines = [""]
            lines[0] = ",".join(quotas) + "\n"
            size = open(self.size_fn, "w")
            size.write("".join(lines))
            size.close()


class SubclassableMaildir(smaildir.Maildir):
    """A mailbox.Maildir class that is more easily subclassed."""

    def __init__(self, dirname, factory=None, create=True, access=0o700,
                 uid=None, gid=None):
        """Like the parent but allows specification of permission, uid, and
        gid if creating."""
        # pylint: disable=W0233, W0231
        mailbox.Mailbox.__init__(self, dirname, factory, create)
        self._paths = {
            'tmp': os.path.join(self._path, 'tmp'),
            'new': os.path.join(self._path, 'new'),
            'cur': os.path.join(self._path, 'cur'),
            }
        exists = os.path.exists(self._path)
        is_mailbox = (os.path.exists(self._paths["tmp"]) and
                      os.path.exists(self._paths["new"]) and
                      os.path.exists(self._paths["cur"]))
        if not is_mailbox:
            if create:
                mask = os.umask(0o000)
                if not exists:
                    try:
                        os.mkdir(self._path, access)
                    except OSError as e:
                        # If another process has simultaneously created
                        # this mailbox, that's fine.
                        if e.errno != 17:
                            raise
                os.chmod(self._path, stat.S_IRWXU | stat.S_IRWXG |
                         stat.S_IRWXG | stat.S_ISGID)
                if uid and gid:
                    os.chown(self._path, uid, gid)
                elif uid:
                    os.chown(self._path, uid, -1)
                elif gid:
                    os.chown(self._path, -1, gid)
                for path in self._paths.values():
                    if not os.path.exists(path):
                        try:
                            os.mkdir(path, access)
                        except OSError as e:
                            # If another process has simultaneously created
                            # this mailbox, that's fine.
                            if e.errno != 17:
                                raise
                    os.chmod(path, stat.S_IRWXU | stat.S_IRWXG | stat.S_IRWXG |
                             stat.S_ISGID)
                    if uid and gid:
                        os.chown(path, uid, gid)
                    elif uid:
                        os.chown(path, uid, -1)
                    elif gid:
                        os.chown(path, -1, gid)
                os.umask(mask)
            else:
                raise mailbox.NoSuchMailboxError(self._path)
        self._toc = {}
        self._toc_mtimes = {'cur': 0, 'new': 0}
        self._last_read = 0  # Records last time we read cur/new
        self._skewfactor = 0.1  # Adjust if os/fs clocks are skewing

    def __getitem__(self, key):
        """Like the parent, but ensures that the date is set when using the
        factory (the factory is no longer able to set the date).  This is
        necessary, because we typically get the date from the filesystem,
        and the factory doesn't know what the path in the filesystem is."""
        if not self._factory:
            return self.get_message(key)
        else:
            item = self._factory(self.get_file(key))
            item.set_date(os.path.getmtime(os.path.join(self._path,
                                                        self._lookup(key))))
            return item

    def get_folder(self, folder):
        """Return a Maildir instance for the named folder."""
        # This is the same as the parent, but uses the class.  The Maildir
        # class should really do this.  It would probably be nicer to do
        # type(self) than self.__class__, but mailbox.Maildir is an old-
        # style class.
        return self.__class__(os.path.join(self._path, '.' + folder),
                              factory=self._factory, create=False)

    def add_folder(self, folder):
        """Create a folder and return a Maildir instance representing it."""
        # This is the same as the parent, but uses the class.  The Maildir
        # class should really do this.  It would probably be nicer to do
        # type(self) than self.__class__, but mailbox.Maildir is an old-
        # style class.
        path = os.path.join(self._path, '.' + folder)
        result = self.__class__(path, factory=self._factory)
        maildirfolder_path = os.path.join(path, 'maildirfolder')
        if not os.path.exists(maildirfolder_path):
            os.close(os.open(maildirfolder_path, os.O_CREAT | os.O_WRONLY))
        return result

    def get_message(self, key):
        """Return a Message representation or raise a KeyError."""
        # Basically the same as the parent, but uses self.get_file rather
        # than opening the file separately, and use the factory to
        # determine what type of object is returned.
        subpath = self._lookup(key)
        messagef = self.get_file(key)
        try:
            if self._factory:
                msg = self._factory(messagef)
            else:
                msg = mailbox.MaildirMessage(messagef)
        finally:
            messagef.close()
        subdir, name = os.path.split(subpath)
        msg.set_subdir(subdir)
        if self.colon in name:
            msg.set_info(name.split(self.colon)[-1])
        msg.set_date(os.path.getmtime(os.path.join(self._path, subpath)))
        return msg
