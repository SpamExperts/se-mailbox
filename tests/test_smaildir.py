import time
import unittest
from mock import patch, MagicMock

from se_mailbox import smaildir


class TestMaildir(unittest.TestCase):
    """Tests for the smaildir.Maildir class."""

    def setUp(self):
        self.mock_scandir = patch("se_mailbox.smaildir.scandir.scandir").start()
        self.mock_walk = patch("se_mailbox.smaildir.scandir.walk").start()
        self.mock_isdir = patch("se_mailbox.smaildir.os.path.isdir",
                                return_value=True).start()
        self.mock_exists = patch("se_mailbox.smaildir.os.path.exists",
                                 return_value=True).start()
        self.mock_remove = patch("se_mailbox.smaildir.os.remove").start()
        self.mock_rmdir = patch("se_mailbox.smaildir.os.rmdir").start()

    def tearDown(self):
        patch.stopall()

    def mock_scandir_values(self, names):
        """Helper function for mocking scandir.scandir results
        with given names."""
        folders = []
        for name in names:
            # name is an argument to the Mock constructor
            folder = MagicMock()
            folder.configure_mock(name=name)
            folders.append(folder)

        return folders

    def test_list_folders(self):
        """Test list_folders functionality."""
        folders = self.mock_scandir_values([".", ".spam", ".ham", "test"])
        self.mock_scandir.return_value = folders

        result = smaildir.Maildir("/test/path").list_folders()
        self.assertEqual(result, ["spam", "ham"])

    def test_iter_folders(self):
        """Test iter_folders functionality."""
        folders = self.mock_scandir_values([".", ".spam", ".ham", "test"])
        self.mock_scandir.return_value = folders

        result = smaildir.Maildir("/test/path").iter_folders()
        self.assertEqual(list(result), ["spam", "ham"])

    def test_remove_folder(self):
        """Test remove_folder functionality."""
        # assume there's nothing in any folder (new or cur)
        # and only the new, cur and tmp subfolders in path
        folders = self.mock_scandir_values(["cur", "new", "tmp"])
        self.mock_scandir.side_effect = [[], [], folders]
        self.mock_walk.return_value = [("/test/path", ["new", "cur", "tmp"], [])]

        smaildir.Maildir("/test/path").remove_folder("ham")

        self.mock_rmdir.assert_called_with("/test/path/.ham")
        self.mock_remove.assert_not_called()

    def test_remove_folder_new_messages(self):
        """Test remove_folder when there are files in the new folder."""
        files = self.mock_scandir_values(["test_message.file"])
        self.mock_scandir.return_value = files

        with self.assertRaises(smaildir.mailbox.NotEmptyError):
            smaildir.Maildir("/test/path").remove_folder("ham")

    def test_remove_folder_cur_messages(self):
        """Test remove_folder when there are files in the cur folder."""
        files = self.mock_scandir_values(["test_message.file"])
        self.mock_scandir.side_effect = [[], files]

        with self.assertRaises(smaildir.mailbox.NotEmptyError):
            smaildir.Maildir("/test/path").remove_folder("ham")

    def test_remove_folder_with_subdirectories(self):
        """Test remove_folder when there are subdirectories in the folder."""
        names = ["cur", "new", "tmp", "test"]
        folders = self.mock_scandir_values(names)
        self.mock_scandir.side_effect = [[], [], folders]

        with self.assertRaises(smaildir.mailbox.NotEmptyError):
            smaildir.Maildir("/test/path").remove_folder("ham")

    def test_clean(self):
        files = self.mock_scandir_values(["test.file"])
        self.mock_scandir.return_value = files
        expired_timestamp = time.time() - 130000
        patch("se_mailbox.smaildir.os.path.getatime",
              return_value=expired_timestamp).start()

        smaildir.Maildir("/test/path").clean()

        self.mock_remove.assert_called_with("/test/path/tmp/test.file")

    def test_clean_not_expired(self):
        files = self.mock_scandir_values(["test.file"])
        self.mock_scandir.return_value = files
        patch("se_mailbox.smaildir.os.path.getatime",
              return_value=time.time()).start()

        smaildir.Maildir("/test/path").clean()

        self.mock_remove.assert_not_called()

