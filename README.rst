===============================
SpamExperts Mailbox Package
===============================


.. image:: https://img.shields.io/pypi/v/se_mailbox.svg
        :target: https://pypi.python.org/pypi/se_mailbox
.. image:: https://img.shields.io/travis/SpamExperts/se-mailbox.svg
        :target: https://travis-ci.org/SpamExperts/se-mailbox
.. image:: https://readthedocs.org/projects/se-mailbox/badge/?version=latest
        :target: https://se-mailbox.readthedocs.io/en/latest/?badge=latest
        :alt: Documentation Status
.. image:: https://codeclimate.com/github/SpamExperts/se-mailbox/badges/gpa.svg
        :target: https://codeclimate.com/github/SpamExperts/se-mailbox
.. image:: https://coveralls.io/repos/SpamExperts/se-mailbox/badge.svg?branch=master&service=github
        :target: https://coveralls.io/github/SpamExperts/se-mailbox?branch=master
.. image:: https://pyup.io/repos/github/spamexperts/se_mailbox/shield.svg
     :target: https://pyup.io/repos/github/spamexperts/se_mailbox/
     :alt: Updates
.. image:: https://requires.io/github/SpamExperts/se-mailbox/requirements.svg?branch=master
     :target: https://requires.io/github/SpamExperts/se-mailbox/requirements/?branch=master
     :alt: Requirements Status


Additional mailbox functionality.


* Free software: GNU General Public License v2
* Documentation: https://se-mailbox.readthedocs.io.


Features
--------

* ``filelock.Filelock`` offers a file locking mechanism that has context-manager support so
    you can use it in a with statement.

* ``smaildir.Maildir`` offers support for maildir mailbox. It uses scandir() instead of listdir(). It also provides a new iter_folders() method that works like list_folders(), put provides a generator instead of returning a list.

* ``se_mailbox.QuotaMixin`` implements the Maildir++ quota size system, as described here: http://www.inter7.com/courierimap/README.maildirquota.html. Quotas are not enforced - this would be good to add

* ``se_mailbox.SubclassableMaildir`` implements a mailbox.Maildir class that is more easily subclassed.

Credits
---------

This package was created with Cookiecutter_ and the `audreyr/cookiecutter-pypackage`_ project template.

.. _Cookiecutter: https://github.com/audreyr/cookiecutter
.. _`audreyr/cookiecutter-pypackage`: https://github.com/audreyr/cookiecutter-pypackage

