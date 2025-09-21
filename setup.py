# -*- coding:utf-8 -*-

from setuptools import setup, find_packages

##############################################################################################################################

with open('./README.md', encoding = 'utf-8') as f:
    LongDescription = f.read()

##############################################################################################################################

setup(
    name = "PyEasyUtils",
    version = '0.3.1',
    description = 'A simple python util library',
    long_description = LongDescription,
    long_description_content_type = 'text/markdown',
    license = 'MIT',
    author = "Spr_Aachen",
    author_email = '2835946988@qq.com',
    url = 'https://github.com/Spr-Aachen/PyEasyUtils',
    project_urls = {
        'Source Code': 'https://github.com/Spr-Aachen/PyEasyUtils',
        'Bug Tracker': 'https://github.com/Spr-Aachen/PyEasyUtils/issues',
    },
    packages = find_packages(
        where = '.',
        exclude = ()
    ),
    include_package_data = True,
    install_requires = [
        "psutil",
        "polars",
        "sqlalchemy",
        "PyGithub"
    ],
    classifiers = [
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
    ]
)

##############################################################################################################################