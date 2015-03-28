# -*- coding: utf-8 -*-
"""Data series object"""
# Author: Dean Serenevy  <dean@serenevy.net>
# This software is Copyright (c) 2014 CMM, Inc.
#
# This program is free software: you can redistribute it and/or modify it
# under the terms of the MIT (Expat) license.
from __future__ import division, absolute_import, print_function, unicode_literals
__all__ = 'Series'.split()


class Series(object):
    def __init__(
            self, name, axis=0, color='b',
            xmin=None, xmax=None, ymin=None, ymax=None,
            format=None, min_width=1, min_height=1,
            X=None, Y=None
        ):
        super(Series,self).__init__()
        self.min_width  = min_width
        self.min_height = min_height
        self.format = format
        self.color = color
        self.name = name
        self.axis = axis
        self.xmin = self._xmin = xmin
        self.xmax = self._xmax = xmax
        self.ymin = self._ymin = ymin
        self.ymax = self._ymax = ymax
        self.X = [] if X is None else X
        self.Y = [] if Y is None else Y
        self.empty = True

    def __len__(self):
        return len(self.X)

    def update_bbox(self, box):
        """Updates the passed bounding box with the series' x/y min/max values.

        @param bbox: list or tuple of form: C{[ x0, y0, x1, y1 ]}
        """
        if box[0] is None or self.xmin < box[0]: box[0] = self.xmin
        if box[1] is None or self.ymin < box[1]: box[1] = self.ymin
        if box[2] is None or self.xmax > box[2]: box[2] = self.xmax
        if box[3] is None or self.ymax > box[3]: box[3] = self.ymax

    def add_point(self, x, y):
        """Add a point and update the bounding box"""
        if self.empty:
            self.initial_point(x,y)

        self.X.append(x)
        self.Y.append(y)

        if x < self.xmin:
            self.xmin = x
        elif self.xmax < x:
            self.xmax = x

        if y < self.ymin:
            self.ymin = y
        elif self.ymax < y:
            self.ymax = y

    def trim_to_domain(self, x1, x2):
        """Trim data to only points where x1 <= x <= x2

        Assumes that the graph x-values are monotonic."""
        try:
            a = next(i for i in xrange(len(self.X)) if self.X[i] >= x1)
        except StopIteration:# failed to match
            a = b = 0
        else:
            try:
                b = next(i for i in xrange(len(self.X)-1, a, -1) if self.X[i] <= x2) + 1
            except StopIteration:# failed to match
                b = len(self.X)

        self.X = self.X[a:b]
        self.Y = self.Y[a:b]
        self.recompute_bbox()

    def trim_to_count(self, n):
        """Trim to the most recently added n points"""
        self.X = self.X[-n:]
        self.Y = self.Y[-n:]
        self.recompute_bbox()

    def initial_point(self, x, y):
        """Initialization of min and max values. Called automatically"""
        if self.xmin is None:
            if self.xmax is None:
                self.xmax = x + self.min_width/2
            self.xmin = self.xmax - self.min_width

        if self.ymin is None:
            if self.ymax is None:
                self.ymax = y + self.min_height/2
            self.ymin = self.ymax - self.min_height

        if self.xmax is None:
            self.xmax = self.xmin + self.min_width

        if self.ymax is None:
            self.ymax = self.ymin + self.min_height

        self.empty = False

    def recompute_bbox(self):
        """Internal method: Called automatically when line is trimmed"""
        if not len(self):
            self.empty = True
            return

        self.xmin, self.xmax = min(self.X), max(self.X)
        self.ymin, self.ymax = min(self.Y), max(self.Y)

        if self._xmin is not None and self.xmin > self._xmin: self.xmin = self._xmin
        if self._xmax is not None and self.xmax < self._xmax: self.xmax = self._xmax
        if self._ymin is not None and self.ymin > self._ymin: self.ymin = self._ymin
        if self._ymax is not None and self.ymax < self._ymax: self.ymax = self._ymax

        xmid = (self.xmin+self.xmax)/2
        self.xmin = min(self.xmin, xmid - self.min_width/2)
        self.xmax = max(self.xmax, xmid + self.min_width/2)

        ymid = (self.ymin+self.ymax)/2
        self.ymin = min(self.ymin, ymid - self.min_height/2)
        self.ymax = max(self.ymax, ymid + self.min_height/2)
