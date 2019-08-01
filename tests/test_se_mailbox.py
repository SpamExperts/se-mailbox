import os
import stat
import time
import shutil
import unittest

from se_mailbox import se_mailbox


class SubclassableMaildirTest(unittest.TestCase):
    """Test functionality unique to the SubclassableMaildir class."""
    def setUp(self):
        """Setup code"""
        self.mailbox_dir = os.path.join(os.path.dirname(
            os.path.join(__file__)), "testmailbox")

    def tearDown(self):
        """Clean up after a single test."""
        if os.path.exists(self.mailbox_dir):
            shutil.rmtree(self.mailbox_dir)

    def test_mail_create_subdirectories(self):
        """Test create mail subdirectories"""
        se_mailbox.SubclassableMaildir(self.mailbox_dir,
                                       create=True)

        self.assertTrue(os.path.exists(self.mailbox_dir))
        self.assertTrue(os.path.exists(os.path.join(self.mailbox_dir, "new")))

        file_mode = os.stat(
            os.path.join(self.mailbox_dir, "new")).st_mode
        self.assertEqual(stat.S_IMODE(file_mode), 0o02770)

    def test_mail_no_create_subdirectories(self):
        """Test skipping create mail subdirectories"""
        with self.assertRaises(se_mailbox.mailbox.NoSuchMailboxError):
            se_mailbox.SubclassableMaildir(self.mailbox_dir,
                                           create=False)

        self.assertFalse(os.path.exists(self.mailbox_dir))

    def test_message_time_from_file(self):
        """Test message time from file"""

        message = ("Subject: Test\n"
                   "To: Testers <testers@spamexperts.com>\n"
                   "From: Testers <testers@spamexperts.com>\n"
                   "\n"
                   "This is a test message.\n")
        mbox = se_mailbox.SubclassableMaildir(
            self.mailbox_dir, create=True)
        key = mbox.add(message)

        # change file time to point to 10 seconds in the future
        msg_filename = os.path.join(mbox._path, mbox._lookup(key))
        new_time = time.time() + 10
        os.utime(msg_filename, (new_time, new_time))

        # check that we get the modified time
        message = mbox[key]
        self.assertAlmostEqual(new_time, message.get_date(), places=3)

    def test_folder_subclass(self):
        """Test add and get a folder from new mbox subclass"""
        class TestMbox(se_mailbox.SubclassableMaildir):
            pass
        mbox = TestMbox(self.mailbox_dir, create=True)
        child_mbox = mbox.add_folder("test")

        self.assertTrue(isinstance(child_mbox, TestMbox))

        # A subfolder should have the 'maildirfolder' file
        self.assertTrue(os.path.exists(os.path.join(
            self.mailbox_dir, ".test", "maildirfolder")))

        child_mbox = mbox.get_folder("test")

        self.assertTrue(isinstance(child_mbox, TestMbox))
