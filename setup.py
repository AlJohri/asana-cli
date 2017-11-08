#!/usr/bin/env python3

from setuptools import setup, find_packages

readme = open('README.rst').read()
exec(open('asana_cli/version.py').read())

setup(
    name='asana-cli',
    version=__version__,
    description='CLI for asana.',
    long_description=readme,
    author='Al Johri',
    author_email='al.johri@gmail.com',
    url='https://github.com/AlJohri/asana-cli',
    license='MIT',
    packages=find_packages(),
    install_requires=['requests', 'click',],
    setup_requires=['pytest-runner'],
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'asana=asana_cli.cli:main'
        ]
    },
    classifiers=[
        'Programming Language :: Python :: 3 :: Only',
        'Programming Language :: Python :: 3.6',
        'License :: OSI Approved :: MIT License',
    ]
)
