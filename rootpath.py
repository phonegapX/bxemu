#-*- coding:utf-8 –*-

import os


SOURCE_ROOT_DIR = os.path.dirname(os.path.abspath(__file__))

def join_relative_path(*paths):
    """
    Get absolute path using paths that are relative to project root.
    """
    return os.path.abspath(os.path.join(SOURCE_ROOT_DIR, *paths))