# -*- coding: utf-8 -*-
"""Real-Time Graphing GUI Component"""
# Author: Dean Serenevy  <dean@serenevy.net>
# This software is Copyright (c) 2014 CMM Inc.
#
# This program is free software: you can redistribute it and/or modify it
# under the terms of the MIT (Expat) license.
from __future__ import division, absolute_import, print_function, unicode_literals
__all__ = 'RealtimeGraph'.split()

from acwx.util import cached_property
from acwx.wx   import subwidget, widget, Widget
from .series  import Series

import wx, sys
import matplotlib
matplotlib.use('WXAgg')
from matplotlib.figure import Figure
from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg as FigCanvas
from matplotlib.ticker import ScalarFormatter
import pylab

# Avoid zero-width plot windows
EPS = 10 * sys.float_info.epsilon

def coalesce(*arg):
    return next(x for x in arg if x is not None)


class RealtimeGraph(Widget):
    """Real-time graphing with support for dual-axis graphs and real-time limit updates.

    After initialization, you must add lines to the graph before plotting
    any points AND BEFORE SETTING TITLE!

    Even thoug this widget is written for real-time plotting, nothing
    prevents it from being useful as a static graph widget. Simply pass
    your X and Y data into the C{add_series()} method and call C{redraw()}.
    """

    def __init__(self, parent, bbox=None, bbox2=None, initial_bbox=None, initial_bbox2=None, pad=None, xpad=0, ypad=0, ypad2=0, **kwargs):
        """
        Bounding boxes have form: [ x0, y0, x1, y1 ]

        Note: Both axes share an x-axis, so there is limited use in
        specifying different x-ranges between the left and right axes.

        @param bbox, bbox2: strict bounding box for primary / secondary axis, any values may be None
        @param initial_bbox, initial_bbox2: Intial / minimal bounding boxes, any values may be None
        @param xpad: padding to apply to x axis (data will not be closer than this to edge)
        @param ypad, ypad2: padding to apply to y axis
        @param pad: set ypad and ypad2 simultaneously
        """
        super(RealtimeGraph,self).__init__(parent, **kwargs)
        self.plot_kwargs = dict(linewidth=1)
        self.title_size  = 12
        self.series      = []
        self.xpad        = xpad
        self.ypad        = ypad  or pad
        self.ypad2       = ypad2 or pad
        self.bbox        = bbox  or [None]*4
        self.bbox2       = bbox2 or [None]*4
        self.init_bbox   = initial_bbox  or [None]*4
        self.init_bbox2  = initial_bbox2 or [None]*4
        self.sizer.Add(self.canvas, 1, wx.EXPAND)

    def add_series(self, name=None, axis=0, color=(1,1,0), **kwargs):
        """Add a data series to the graph

        @param name: Name of the data series
        @param axis: 0 for left (default) or 1 for right
        @param color: any color recognized by matplotlib
        @param format: matplotlib format token such as, 'go-'
        @param xmin, xmax, ymin, xmax: initial bounding box
        @param X, Y: lists containing plot data
        """
        self.series.append(Series(name,axis,color,**kwargs))

    def add_points(self, *points):
        for i, pt in enumerate(points):
            self.series[i].add_point(*pt)
        self.redraw()

    def redraw(self):
        axes  = [ False, False ]
        boxes = [ list(self.init_bbox), list(self.init_bbox2) ]

        # Update the line data (internally, just sets a dirty flag)
        for i, series in enumerate(self.series):
            axes[series.axis] = True
            series.update_bbox(boxes[series.axis])
            self.lines[i].set_xdata(series.X)
            self.lines[i].set_ydata(series.Y)

        # With 2 axes we have a shared x-axis, thus we have to make them agree.
        if axes[1] and axes[0]:
            xmin = coalesce(self.bbox2[0], self.bbox[0], min(boxes[0][0], boxes[1][0])-self.xpad)
            xmax = max(xmin+EPS, coalesce(self.bbox2[2], self.bbox[2], max(boxes[0][2], boxes[1][2])+self.xpad))
        elif axes[0]:
            xmin = coalesce(self.bbox[0], boxes[0][0]-self.xpad)
            xmax = max(xmin+EPS, coalesce(self.bbox[2], boxes[0][2]+self.xpad))
        elif axes[1]:
            xmin = coalesce(self.bbox2[0], boxes[1][0]-self.xpad)
            xmax = max(xmin+EPS, coalesce(self.bbox2[2], boxes[1][2]+self.xpad))
        else:
            # No series!?
            return

        # Update windows
        if axes[0]:
            ymin = coalesce(self.bbox[1], boxes[0][1]-self.ypad)
            ymax = max(ymin+EPS, coalesce(self.bbox[3], boxes[0][3]+self.ypad))
            self.axes.set_xbound(lower=xmin, upper=xmax)
            self.axes.set_ybound(lower=ymin, upper=ymax)

        if axes[1]:
            ymin = coalesce(self.bbox2[1], boxes[1][1]-self.ypad2)
            ymax = max(ymin+EPS, coalesce(self.bbox2[3], boxes[1][3]+self.ypad2))
            self.axes2.set_xbound(lower=xmin, upper=xmax)
            self.axes2.set_ybound(lower=ymin, upper=ymax)

        # Redraw
        self.canvas.draw()

    @property
    def title(self):
        return self.axes.get_title()
    @title.setter
    def title(self, title):
        self.axes.set_title(title, size=self.title_size)

    @subwidget
    def canvas(self):
        """Figure canvas

        See: http://matplotlib.org/api/backend_bases_api.html#matplotlib.backend_bases.FigureCanvasBase

        Save image using: .canvas.print_figure(path)
        """
        return FigCanvas(self, wx.ID_ANY, self.fig)

    @subwidget
    def fig(self):
        return Figure()

    @cached_property
    def v_formatter(self):
        """Formatter that won't use the "+1.XeY" horribleness that occurs by default when labels get long"""
        return ScalarFormatter(False)

    @cached_property
    def axes(self):
        ax = self.fig.add_subplot(111)
        pylab.setp(ax.get_xticklabels(), fontsize=8)
        pylab.setp(ax.get_yticklabels(), fontsize=8)

        ax.xaxis.set_major_formatter( self.v_formatter )
        ax.xaxis.set_minor_formatter( self.v_formatter )
        ax.yaxis.set_major_formatter( self.v_formatter )
        ax.yaxis.set_minor_formatter( self.v_formatter )
        return ax

    @cached_property
    def axes2(self):
        ax = self.axes.twinx()

        ax.xaxis.set_major_formatter( self.v_formatter )
        ax.xaxis.set_minor_formatter( self.v_formatter )
        ax.yaxis.set_major_formatter( self.v_formatter )
        ax.yaxis.set_minor_formatter( self.v_formatter )
        return ax

    @cached_property
    def lines(self):
        # Ugh, I don't think I'm a fan of the matplotlib API... I suspect
        # this could probably be done better using a lower level API, but
        # all the tutorials only show the high-level and I don't find it
        # intuitive.
        indices = [ [], [] ]
        args    = [ [], [] ]
        colors  = [ [], [] ]
        lines   = [None]*len(self.series)

        # Lock the series (prevent any additions)
        self.series = tuple(self.series)

        for idx, series in enumerate(self.series):
            indices[series.axis].append(idx)
            args[series.axis].append(series.X)
            args[series.axis].append(series.Y)
            if series.format:
                args[series.axis].append(series.format)
            colors[series.axis].append(series.color)

        if indices[0]:
            self.axes.set_color_cycle(colors[0])
            for idx, line in zip(indices[0], self.axes.plot(*args[0], **self.plot_kwargs)):
                lines[idx] = line

        if indices[1]:
            self.axes2.set_color_cycle(colors[1])
            for idx, line in zip(indices[1], self.axes2.plot(*args[1], **self.plot_kwargs)):
                lines[idx] = line

        return tuple(lines)
