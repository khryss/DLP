#!/usr/bin/env python
from setuptools import setup, find_packages


setup(
    name='quiz',
    version='1.1',
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        "Django >= 1.8",
    ]
)
