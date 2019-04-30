#-*- coding:utf-8 –*-

'''
bxemu - bitmex xbt emulator.
'''

from setuptools import setup, find_packages
import codecs
import os


def read_install_requires():
    with codecs.open('requirements.txt', 'r', encoding='utf-8') as f:
        res = f.readlines()
    res = list(map(lambda s: s.replace('\n', ''), res))
    return res

setup(
    # Package Information
    name='bxemu',
    url='https://github.com/phonegapX/bxemu',
    version='1.0.0',
    license='MIT',
    # information
    description='Open source quantitative research framework.',
    long_description=__doc__,
    keywords="quantiatitive trading research finance",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: Education",
        "Intended Audience :: End Users/Desktop",
        "Intended Audience :: Financial and Insurance Industry",
        "Intended Audience :: Information Technology",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: Apache Software License",
        "Natural Language :: Chinese (Simplified)",
        "Natural Language :: English",
        "Operating System :: Microsoft :: Windows",
        "Operating System :: Unix",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3.7",
    ],
    # install
    install_requires=read_install_requires(),
    packages=find_packages(),
    # author
    author='moseszhang'
)
