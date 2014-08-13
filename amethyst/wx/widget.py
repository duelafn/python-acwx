# -*- coding: utf-8 -*-
"""Base GUI component class"""
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
__all__ = 'widget subwidget WidgetMixin Widget Dialog GridWidget ScrolledWidget'.split()

import wx, weakref, wx.lib.scrolledpanel, json, six
from amethyst import cached_property
from .util import BORDER_SIZE
import amethyst.wx.util

class widget(cached_property):
    pass

class subwidget(widget):
    def __call__(self, method):
        self.name = self.name if self.name is not None else method.__name__
        def _build(me):
            widget = method(me)
            me.subwidgets.append(widget)
            return widget

        return super(subwidget,self).__call__(_build)


class WidgetMixin(object):
    @cached_property
    def large_font(self):
        return wx.Font(24, wx.DEFAULT, wx.NORMAL, wx.NORMAL)

    def __init__(
            self, parent, id=wx.ID_ANY,
            app=None, require_app=True, stash_namespace=None,
            **kwargs
        ):

        for attr in 'machine galil settings stash user'.split():
            if attr in kwargs:
                setattr(self, attr, kwargs.pop(attr))

        super(WidgetMixin,self).__init__(parent, id, **kwargs)

        self.stash_namespace = getattr(parent, 'stash_namespace', '') if stash_namespace is None else stash_namespace
        if self.stash_namespace and self.stash_namespace[-1] != '.':
            self.stash_namespace += '.'

        self.app = app
        if app is None and hasattr(parent, "app"):
            self.app = parent.app

        if require_app and self.app is None:
            raise Exception("Must provide app in either parent or as named parameter")

        self.subwidgets = []
        self.parent = parent

    @property
    def parent(self):
        return self._parent() if self._parent is not None else None
    @parent.setter
    def parent(self, value):
        self._parent = weakref.ref(value) if value is not None else None

    def wx_text(self, text, **kwargs):
        return wx.StaticText(self, wx.ID_ANY, unicode(text), **kwargs)

    def file_save_dialog(self, title, wildcard, filename):
        return amethyst.wx.util.file_save_dialog(self, title, wildcard, filename)

    def file_open_dialog(self, title, wildcard):
        return amethyst.wx.util.file_open_dialog(self, title, wildcard)

    def show_error(self, *args, **kwargs):
        kwargs.setdefault('parent', self)
        return self.app.show_error(*args, **kwargs)

    def modal_message(self, *args, **kwargs):
        kwargs.setdefault('parent', self)
        return self.app.modal_message(*args, **kwargs)

    def run_galil(self, *args, **kwargs):
        kwargs.setdefault('parent', self)
        return self.app.run_galil(*args, **kwargs)

    def Enable(self, enable=True):
        for w in self.subwidgets:
            w.Enable(enable)

    @cached_property
    def machine(self):
        return self.parent.machine  if hasattr(self.parent, "machine")   else self.app.machine
    @property
    def galil(self):
        return self.app.galil
    @cached_property
    def settings(self):
        return self.parent.settings if hasattr(self.parent, "settings")  else self.app.settings
    @cached_property
    def stash(self):
        return self.parent.stash    if hasattr(self.parent, "stash")     else self.app.stash
    @property
    def user(self):
        return self.app.user

    def get_stash(self, key, dflt=None):
        return self.stash.get(self.stash_namespace + key, dflt)
    def set_stash(self, key, value):
        return self.stash.set(self.stash_namespace + key, value)

    def json_get_stash(self, key, dflt=None):
        val = self.get_stash(key, None)
        return dflt if val is None else json.loads(val)
    def json_set_stash(self, key, value):
        val = None if value is None else json.dumps(value, separators=(',',':'))
        return self.set_stash(key, val)

    def _(self, term):
        return self.app.term(term)


class _Widget(WidgetMixin):

    def __init__(
            self, parent, id=wx.ID_ANY,
            legend=None,
            orientation=wx.VERTICAL,
            frame_orientation=wx.HORIZONTAL,
            sizer=None,  # Custom backing sizer, but still gain app, id, and legend support
            frame=None,  # border around entire widget
            **kwargs
        ):

        super(_Widget,self).__init__(parent, id, **kwargs)

        self._frame = frame
        self._sizer = sizer
        self._legend = legend
        self._orientation = orientation
        self._frame_orientation = frame_orientation

        self.SetSizer(self.frame)

    @widget
    def sizer(self):
        if self._legend is None:
            self._box = None
            widget = self._sizer if self._sizer is not None else wx.BoxSizer(self._orientation)
        else:
            self._box = wx.StaticBox(self, wx.ID_ANY, self._legend)
            widget = wx.StaticBoxSizer(self._box, self._orientation)
            if self._sizer is not None:
                widget.Add(self._sizer, 1, wx.EXPAND)
                widget = self._sizer
        return widget

    @cached_property
    def frame(self):
        if self._frame is not None:
            frame = wx.BoxSizer(self._frame_orientation)
            frame.Add(self.sizer, 1, wx.EXPAND|wx.ALL, self._frame)
            return frame
        else:
            return self.sizer

    @property
    def legend(self):
        if self._box is None:
            return None
        else:
            return self._box.GetLabel()
    @legend.setter
    def legend(self, label):
        self._box.SetLabel(label)


class Dialog(_Widget, wx.Dialog):
    def __init__(self, parent=None, title="", buttons=(), **kwargs):
        kwargs['legend'] = None
        kwargs['frame']  = 0
        kwargs['frame_orientation'] = wx.VERTICAL
        kwargs.setdefault('style', wx.CAPTION|wx.CLOSE_BOX|wx.SYSTEM_MENU|wx.RESIZE_BORDER|wx.MAXIMIZE_BOX|wx.MINIMIZE_BOX)
        super(Dialog,self).__init__(parent, title=title, **kwargs)

        self.frame.Add(self.button_box, 0, wx.EXPAND)
        for spec in buttons:
            if spec:
                self.add_button(*spec)
            else:
                self.add_button_spaceer()

    @property
    def title(self):
        return self.GetTitle()
    @title.setter
    def title(self, value):
        return self.SetTitle(value)

    @cached_property
    def button_box(self):
        return wx.BoxSizer(wx.HORIZONTAL)

    def add_button_spacer(self):
        """Add a spacer to the dialog button box"""
        self.button_box.Add((0,0), 1)

    def add_button(self, btn_id, callback):
        """Add a button to the dialog.

        When passed a stadard button ID
        (http://docs.wxwidgets.org/2.8.12/wx_stockitems.html), will
        construct the standard button. Else, can be passed a string which
        will be used as the button label text.
        """
        if isinstance(btn_id, (tuple, list)):
            widget = wx.Button(self, *btn_id)
        elif isinstance(btn_id, six.string_types):
            widget = wx.Button(self, wx.ID_ANY, btn_id)
        else:
            widget = wx.Button(self, btn_id)

        widget.Bind(wx.EVT_BUTTON, callback)
        self.button_box.Add(widget, 0, wx.ALL, BORDER_SIZE)


class Widget(_Widget, wx.Panel):
    pass

class GridWidget(Widget):
    default_font = None
    default_flag = wx.ALIGN_CENTER_VERTICAL
    default_border = 0

    def __init__(self, parent, **kwargs):
        super(GridWidget,self).__init__(parent, **kwargs)
        self._sizer_row_names = dict()
        self._sizer_last_row  = -1
        self._row_visibility  = dict()

    def iter_col(self, col):
        for row in xrange(self.sizer.GetRows()):
            item = self.sizer.FindItemAtPosition((row, col))
            if item is not None:
                yield item.GetWindow()

    @widget
    def sizer(self):
        widget = wx.GridBagSizer(BORDER_SIZE, BORDER_SIZE)
        widget.SetEmptyCellSize((-BORDER_SIZE,-BORDER_SIZE))
        return widget

    @cached_property
    def frame(self):
        if self._legend is None:
            self._box = None
            if self._frame:
                frame = wx.BoxSizer()
                frame.Add(self.sizer, 1, wx.EXPAND|wx.ALL, self._frame)
                return frame
            else:
                return self.sizer

        else:
            self._box = wx.StaticBox(self, wx.ID_ANY, self._legend)
            widget = wx.StaticBoxSizer(self._box, self._orientation)
            if self._frame:
                widget.Add(self.sizer, 1, wx.EXPAND|wx.ALL, self._frame)
            else:
                widget.Add(self.sizer, 1, wx.EXPAND)
        return widget

    def add_grid_row(self, *items, **kwargs):
        """Adds one or more items to a row of the grid. The span argument
        is a scalar, list, or tuple specifying the span of the
        corresponding items. The last span will be repeated for any surplus
        items so passing C{(2,1)} is exactly the same as passing
        C{(2,1,1,1,1)}.

        @param name: row name for show_row, hide_row
        @param row: row number (autocomputed by default)
        @param span: tuple of column spans
        @param flag: flags passed to all cells
        @param border: border size
        @param grow: boolean, will create a growable row when C{True}
        """
        name   = kwargs.get("name",   None)
        row    = kwargs.get("row",    None)
        font   = kwargs.get("font",   self.default_font)
        span   = kwargs.get("span",   (1,))
        flag   = kwargs.get("flag",   self.default_flag)
        border = kwargs.get("border", self.default_border)

        if span and not isinstance(span, (list,tuple)):
            span = (span,)

        if row is None:
            row = self._sizer_last_row + 1
        self._sizer_last_row = row

        if name is not None:
            self._sizer_row_names[name] = row
            self._row_visibility[name]  = True

        if kwargs.get("grow", False):
            self.sizer.AddGrowableRow(row)

        col, idx = 0, 0
        for item in items:
            this_span = span[min(idx,len(span)-1)]
            if isinstance(this_span, (list, tuple)):
                this_row_span = this_span[0]
                this_col_span = this_span[1]
            else:
                this_row_span = 1
                this_col_span = this_span

            if isinstance(item, six.string_types):
                item = wx.StaticText(self, wx.ID_ANY, item)
                if font:
                    item.SetFont(font)

            this_flag = flag
            if this_flag & wx.EXPAND and isinstance(item, (wx.StaticText, wx.StaticBitmap)):
                this_flag ^= wx.EXPAND
                this_flag |= wx.ALIGN_CENTER_VERTICAL
            elif isinstance(item, (wx.StaticText, wx.StaticBitmap)):
                this_flag |= wx.ALIGN_CENTER_VERTICAL

            self.sizer.Add(item, pos=(row, col), span=(this_row_span, this_col_span), flag=this_flag, border=border)
            col += this_col_span
            idx += 1

    def row_num(self, name):
        return self._sizer_row_names.get(name, name)

    def get_cell(self, name=None, col=None, row=None):
        if row is None:
            row = self.row_num(name)
        item = self.sizer.FindItemAtPosition((row, col))
        return item.GetWindow() if item else None

    def show_row(self, name, show=True):
        row = self.row_num(name)
        self._row_visibility[name] = show
        for col in xrange(self.sizer.GetCols()):
            item = self.sizer.FindItemAtPosition((row, col))
            if item:
                if hasattr(item, "Show"):
                    item.Show(show)
                wind = item.GetWindow()
                if wind and hasattr(wind, "Show"):
                    wind.Show(show)
        self.GetParent().SendSizeEvent()

    def hide_row(self, name, hide=True):
        self.show_row(name, show=not hide)

    def visible_rows(self):
        return [ name for name in self._row_visibility if self._row_visibility[name] ]

    def is_row_visible(self, name):
        return self._row_visibility[name]

class ScrolledWidget(_Widget, wx.lib.scrolledpanel.ScrolledPanel):
    pass
