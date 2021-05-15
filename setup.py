#!/usr/bin/env python3

import re
import setuptools
from setuptools import find_packages


def find_version():
    return re.search(r"^__version__ = '(.*)'$",
                     open('asyncudp/version.py', 'r').read(),
                     re.MULTILINE).group(1)


setuptools.setup(
    name='asyncudp',
    version=find_version(),
    description='Asyncio high level UDP sockets.',
    long_description=open('README.rst', 'r').read(),
    author='Erik Moqvist',
    author_email='erik.moqvist@gmail.com',
    license='MIT',
    classifiers=[
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
    ],
    keywords=['asyncio'],
    url='https://github.com/eerimoq/asyncudp',
    packages=find_packages(exclude=['tests']),
    test_suite="tests")
