# -*- coding: utf-8 -*-
"""Various generic utility functions"""
# Author: Dean Serenevy  <dean@serenevy.net>
# This software is Copyright (c) 2013 APCI, LLC.
#
# This program is free software: you can redistribute it and/or modify it
# under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, version 3 of the License.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE. See the GNU Lesser General Public License
# for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
from __future__ import division, absolute_import, print_function, unicode_literals
__all__ = 'cached_property'.split()

import weakref


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
