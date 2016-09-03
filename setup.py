#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup

with open('README.rst') as readme_file:
    readme = readme_file.read()

with open('HISTORY.rst') as history_file:
    history = history_file.read()

requirements = [
    'future>=0.15.2',
    'Click>=6.0',
    'python-crontab>=2.1.1',
    'send2trash>=1.3.0',
]

test_requirements = [
    # TODO: put package test requirements here
]

setup(
    name='garbagetruck',
    version='0.1.0',
    description="A small tool to periodically move old files into the local file system trash.",
    long_description=readme + '\n\n' + history,
    author="Brad Robel-Forrest",
    author_email='brad@bitpony.com',
    url='https://github.com/bradrf/garbagetruck',
    packages=[
        'garbagetruck',
    ],
    package_dir={'garbagetruck':
                 'garbagetruck'},
    entry_points={
        'console_scripts': [
            'garbagetruck=garbagetruck.cli:main'
        ]
    },
    include_package_data=True,
    install_requires=requirements,
    license="MIT license",
    zip_safe=False,
    keywords='garbagetruck',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        "Programming Language :: Python :: 2",
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
    ],
    test_suite='tests',
    tests_require=test_requirements
)
