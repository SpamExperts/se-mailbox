#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup

with open('README.rst') as readme_file:
    readme = readme_file.read()

with open('HISTORY.rst') as history_file:
    history = history_file.read()

requirements = [
    "scandir==1.10.0",
]

test_requirements = [
    "mock==5.1.0",
    "pytest==7.1.2",
]

setup(
    name='se_mailbox',
    version='1.0.0',
    description="Additional mailbox functionality.",
    long_description=readme + '\n\n' + history,
    author="SolarWinds Mail WG",
    author_email='mail-plg-engineering@solarwinds.com',
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
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.7',
    ],
    test_suite='tests',
    tests_require=test_requirements
)
