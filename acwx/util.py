# -*- coding: utf-8 -*-
"""Various generic utility functions"""
# Author: Dean Serenevy  <dean@serenevy.net>
# This software is Copyright (c) 2013 APCI, LLC.
#
# This program is free software: you can redistribute it and/or modify it
# under the terms of the MIT (Expat) license.
from __future__ import division, absolute_import, print_function, unicode_literals
__all__ = 'ContextualCounter cached_property'.split()

import weakref



class ContextualCounter(object):
    """Provides a contextual flag.

    Useful to prevent (or count) nesting. Example use:

        flag = ContextualCounter()
        def my_func():
            print("my_func, depth", flag.depth)
            if flag:
                return
            with flag:
                do_stuff()

    Now if my_func is called from do_stuff, you will not enter an infinite
    recursion.
    """
    def __init__(self):
        self.depth = 0
    def __enter__(self):
        self.depth += 1
    def __exit__(self, type, value, traceback):
        self.depth -= 1

    def __nonzero__(self):
        return self.depth > 0
    def __int__(self):
        return self.depth


class cached_property(object):
    '''Computes attribute value and caches it in the instance.

    This decorator allows you to create a property which can be computed
    once and accessed many times. Sort of like memoization

    Source: Python Cookbook
    Author: Denis Otkidach  http://stackoverflow.com/users/168352/denis-otkidach
    Extended by: http://stackoverflow.com/questions/3237678/how-to-create-decorator-for-lazy-initialization-of-a-property
    Further extended by Dean Serenevy for APCI LLC.
    '''
    def __init__(self, method=None, name=None, weak=False, debug=False):
        self.name = name
        self.debug = debug
        self.weak = weak
        if method is not None:
            self(method)

    def __call__(self, method):
        self.method = method
        self.name = self.name if self.name is not None else method.__name__
        self.__doc__ = method.__doc__
        return self

    def __get__(self, inst, cls):
        if inst is None:
            return self
        elif self.name in inst.__dict__:
            value = inst.__dict__[self.name]
        else:
            value = self.method(inst)
            if self.weak:
                try:
                    value = weakref.ref(value)
                except TypeError:
                    pass
            inst.__dict__[self.name] = value

        return value() if self.weak and isinstance(value, weakref.ref) else value

    def __set__(self, inst, value):
        if self.weak:
            inst.__dict__[self.name] = weakref.ref(value)
        else:
            inst.__dict__[self.name] = value

    def __delete__(self,inst):
        if self.name in inst.__dict__:
            del inst.__dict__[self.name]
