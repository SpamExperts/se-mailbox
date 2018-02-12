#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup

with open('README.rst') as readme_file:
    readme = readme_file.read()

with open('HISTORY.rst') as history_file:
    history = history_file.read()

requirements = [
    "scandir==1.7",
]

test_requirements = [
    # TODO: put package test requirements here
]

setup(
    name='se_mailbox',
    version='0.1.1',
    description="Additional mailbox functionality.",
    long_description=readme + '\n\n' + history,
    author="SpamExperts B.V.",
    author_email='support@spamexperts.com',
    url='https://github.com/spamexperts/se-mailbox',
    packages=[
        'se_mailbox',
    ],
    package_dir={'se_mailbox':
                 'se_mailbox'},
    include_package_data=True,
    install_requires=requirements,
    zip_safe=False,
    keywords='se_mailbox',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'Natural Language :: English',
        "Programming Language :: Python :: 2",
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
    ],
    test_suite='tests',
    tests_require=test_requirements
)
