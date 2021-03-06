#!/usr/bin/env python
"""acwx wx-App Library"""
# This software is Copyright (c) 2013 APCI, LLC.
#
# This program is free software: you can redistribute it and/or modify it
# under the terms of the MIT (Expat) license.

import re, os.path
__version__ = re.search(r'(?m)^__version__\s*=\s*"([\d.]+(?:[\-\+~.]\w+)*)"', open('acwx/__init__.py').read()).group(1)

from distutils.core import setup
from os import walk
from os.path import join, relpath


def find_packages(path):
    """Recursively search through C{path} looking for __init__.py files.
    Returns a list of all module names found.
    """
    val = []

    for root, subFolders, files in walk(path):
        if "__init__.py" in files:
            components = [ relpath(root, join(path, '..')) ]
            while components[0] != '':
                components = list(os.path.split(components[0])) + components[1:]
            val.append(".".join(components[1:]))
    return val

setup(
    name         = 'acwx',
    version      = __version__,
    url          = 'https://github.com/duelafn/python-acwx',
    author       = "Dean Serenevy",
    author_email = 'dean@serenevy.net',
    description  = "acwx wx-App Library",
    packages     = find_packages("acwx"),
    provides     = "acwx",
    requires     = [# Only strict requirements
        "six",
    ],
)
