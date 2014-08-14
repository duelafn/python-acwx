# -*- coding: utf-8 -*-
"""
Parent class for editors with a panel containing a list of items and
another panel with an item editor. This class provides an ObjectListView of
the editable items and optional "Save", "Save New", "Delete", "Clear", and
"Close" buttons. These buttons will invoke corresponding on_*() handlers
which do reasonable things.

@requires: Child must implement a C{columns} attribute, a list of
    ObjectListView Column objects. It must be a class attribute or else
    must be populated before calling this C{__init__()}.

@requires: Child must implement an C{editor} subwidget

@requires: Child must set the C{dirty} attribute whenever changes are made
    in the editor (clearing the dirty flag will be done by the parent).

@requires: Child must implement a C{load(obj)} method which discards any
    current edits and populates the editor with the passed object.

@requires: Child must implement a C{delete()} method which deletes the
    current item (the parent will not call C{delete()} if C{current_item}
    is undefined and will not call C{delete()} if "delete" is not included
    in the button list).

@requires: Child must implement a C{save()} method which saves the current
    item (the parent will not call C{save()} if C{current_item} is
    undefined).

@requires: Child must implement a C{save_new()} method which creates a new
    item from the editor data (even if it is already associated with a
    current item). This method must return the new object (which will be
    passed to C{refresh(obj)}). This object will not call save_new unless
    the save_new button is enabled.

@requires: Child must implement a C{clear()} method which discards changes
    and clears the editor

Child may wish to override C{validation_errors()} to return a list of
string errors (or C{validate()} for more control).

Child may wish to override C{refresh(obj)} to refresh the item list.

Child may wish to implement a C{hash()} method which computes a hash of the
form values. This will be used to implement a C{modified} dynamic attribute
which is True when the item is actually modified, otherwise, the C{dirty}
attribute will be used, but since a record can be dirty but unmodified, may
result in unnecessary saving or popup notifications.
"""
# Author: Dean Serenevy  <deans@apcisystems.com>
# This software is Copyright (c) 2014 APCI, LLC.
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
__all__ = 'EditorContainerOLV'.split()

import wx
from amethyst.wx.widget import Widget, widget, subwidget
from amethyst.wx.util   import BORDER_SIZE, NULL_FIELD
from amethyst.util      import ContextualCounter

from ObjectListView  import FastObjectListView

import wx.lib.newevent

SaveEvent,    EVT_SAVE     = wx.lib.newevent.NewCommandEvent()
SaveNewEvent, EVT_SAVE_NEW = wx.lib.newevent.NewCommandEvent()
DeleteEvent,  EVT_DELETE   = wx.lib.newevent.NewCommandEvent()
ClearEvent,   EVT_CLEAR    = wx.lib.newevent.NewCommandEvent()
CloseEvent,   EVT_CLOSE    = wx.lib.newevent.NewCommandEvent()
SelectEvent,  EVT_SELECT   = wx.lib.newevent.NewCommandEvent()



class EditorContainerOLV(Widget):
    def __init__(self, parent, buttons=frozenset("save save_new clear delete".split()), orientation=wx.HORIZONTAL, verify_delete=False, **kwargs):
        """
        @param orientation: orientation of box holding table and editor
        @param buttons: list/tuple/set of buttons which should be included. A subset of: close, save, save_new, clear
        """
        super(EditorContainerOLV,self).__init__(parent, **kwargs)
        self.suppress_select_event = ContextualCounter()
        self._in_select = ContextualCounter()
        self.buttons = buttons
        self.last_hash = None
        self.current_item = None
        self.orientation = orientation
        self.verify_delete = verify_delete
        self.dirty = False
        self.build()

    def build(self):
        """Build the interface. May override or extend"""
        hbox = wx.BoxSizer(self.orientation)
        hbox.Add(self.table,          1, wx.EXPAND|wx.ALL, BORDER_SIZE)
        hbox.Add(self.editor,         2, wx.EXPAND|wx.ALL, BORDER_SIZE)

        self.sizer.Add(hbox, 1, wx.EXPAND|wx.ALL, BORDER_SIZE)
        self.sizer.Add(self.buttonbox, 0, wx.EXPAND|wx.ALL, BORDER_SIZE)

    @property
    def items(self):
        return self.table.GetObjects()
    @items.setter
    def items(self, items):
        self.table.SetObjects(items)

    def add_items(self, *items):
        self.table.AddObjects(items)

    def del_items(self, *items):
        self.table.RemoveObjects(items)

    @property
    def modified(self):
        if not self.dirty:
            return False

        if hasattr(self, "hash"):
            hash = self.hash()
            self.dirty = (hash != self.last_hash)

        return self.dirty

    def rehash(self):
        self.dirty = False
        if hasattr(self, "hash"):
            self.last_hash = self.hash()

    def prompt_validation_errors(self, errors):
        self.show_error(errors, "Invalid Item")

    def prompt_discard_changes(self):
        return self.app.boolean_prompt("Discard Changes?", "Discard all unsaved changes?")

    def validation_errors(self):
        """Override to return a list of validation errors found"""
        return []

    def validate(self, new):
        """Called before save or save_new, returns True if save can
        proceed. May be overridden.

        When called, C{new} will be true if and only if we are validating a
        new object.
        """
        errors = self.validation_errors()
        if errors:
            self.prompt_validation_errors(errors)
            return False
        return True

    def delete_ok(self):
        if not self.verify_delete:
            return True
        return self.app.boolean_prompt("Really Delete?", "Really delete this entry?")

    def select(self, item, ask=True):
        """
        Selects the given item in the list and updates the display.

        Returns true if selection succeeds/is approved and false otherwise.

        @param item: Item to select. If None, will clear the editor.

        @param ask: When true, user will be prompted if there are unsaved changes.
        """
        if self._in_select:
            return True

        with self._in_select:
            if item == self.current_item:
                with self.suppress_select_event:
                    self.table.SelectObject(item, deselectOthers=True, ensureVisible=True)
                return True

            if ask and self.modified:
                if not self.prompt_discard_changes():
                    if self.current_item:
                        self.table.SelectObject(self.current_item, deselectOthers=True, ensureVisible=True)
                    else:
                        self.table.DeselectAll()
                    return False

            self.current_item = item
            if item is None:
                self.clear()
                self.rehash()
                self.table.DeselectAll()
            else:
                self.load(item)
                self.rehash()
                self.table.SelectObject(item, deselectOthers=True, ensureVisible=True)

            return True

    def refresh(self, item=None):
        """Refresh / add to the item list

        By default just calls C{add_items()} if the passed item is not
        already present.
        """
        if item is not None and item not in self.items:
            self.add_items(item)
        if item is not None:
            self.table.RefreshObject(item)

    @subwidget
    def table(self):
        widget = FastObjectListView(self)
        widget.Bind(wx.EVT_LIST_ITEM_SELECTED, self.on_select)
        widget.SetColumns(self.columns)
        widget.SortBy(0, True)
        return widget

    @widget
    def buttonbox(self):
        btn_args = [ 0, wx.ALL, BORDER_SIZE ]

        hbox = wx.BoxSizer(wx.HORIZONTAL)
        if "close" in self.buttons:
            btn = wx.Button(self, label="Close")
            btn.Bind(wx.EVT_BUTTON, self.on_close)
            hbox.Add(btn, *btn_args)

        hbox.Add((BORDER_SIZE,BORDER_SIZE), 1, wx.ALL, BORDER_SIZE)

        if "delete" in self.buttons:
            btn = wx.Button(self, label="Delete")
            btn.Bind(wx.EVT_BUTTON, self.on_delete)
            hbox.Add(btn, *btn_args)
            self.subwidgets.append(btn)

        if "clear" in self.buttons:
            btn = wx.Button(self, label="Clear")
            btn.Bind(wx.EVT_BUTTON, self.on_clear)
            hbox.Add(btn, *btn_args)
            self.subwidgets.append(btn)

        if "save_new" in self.buttons:
            btn = wx.Button(self, label="Save As New")
            btn.Bind(wx.EVT_BUTTON, self.on_save_new)
            hbox.Add(btn, *btn_args)
            self.subwidgets.append(btn)

        if "save" in self.buttons:
            btn = wx.Button(self, label="Save")
            btn.Bind(wx.EVT_BUTTON, self.on_save)
            hbox.Add(btn, *btn_args)
            self.subwidgets.append(btn)

        return hbox

    def on_save(self, evt=None):
        """Validate, save, refresh, re-select

        Forwards to on_save_new if current_item is None.
        """
        if evt: evt.Skip()
        if self.current_item is None:
            return self.on_save_new(evt)
        if self.validate(new=False):
            self.save()
            self.refresh(self.current_item)
            self.select(self.current_item, ask=False)
            self.rehash()
            my_evt = SaveEvent(self.GetId())
            my_evt.SetEventObject(self)
            wx.PostEvent(self, my_evt)

    def on_save_new(self, evt=None):
        """Validate, save_new, refresh, select"""
        if evt: evt.Skip()
        if "save_new" in self.buttons and self.validate(new=True):
            item = self.save_new()
            if item is None:
                raise Exception("Failed to save new item!")
            self.refresh(item)
            self.select(item, ask=False)
            my_evt = SaveNewEvent(self.GetId())
            my_evt.SetEventObject(self)
            wx.PostEvent(self, my_evt)

    def on_clear(self, evt=None):
        """Clear editor with user verification if unsaved changes"""
        if evt: evt.Skip()
        if self.select(None):
            my_evt = ClearEvent(self.GetId())
            my_evt.SetEventObject(self)
            wx.PostEvent(self, my_evt)

    def on_delete(self, evt=None):
        """Delete current item with user verification"""
        if evt: evt.Skip()
        if "delete" in self.buttons and self.current_item and self.delete_ok():
            self.delete()
            self.del_items(self.current_item)
            self.select(None, ask=False)
            my_evt = DeleteEvent(self.GetId())
            my_evt.SetEventObject(self)
            wx.PostEvent(self, my_evt)

    def on_close(self, evt=None):
        """Post close event with user verification if unsaved changes"""
        if evt: evt.Skip()
        if self.modified and not self.prompt_discard_changes():
            return
        my_evt = CloseEvent(self.GetId())
        my_evt.SetEventObject(self)
        wx.PostEvent(self, my_evt)

    def on_select(self, evt=None):
        """Select from list event with user verification if unsaved changes"""
        # table.SelectObject() triggers this event which give us infinite recursion.
        # Check to see whether we need to suppress the select event.
        if self.suppress_select_event:
            return
        with self.suppress_select_event:
            if evt: evt.Skip()
            if self.select(self.table.GetSelectedObject()):
                my_evt = SelectEvent(self.GetId())
                my_evt.SetEventObject(self)
                wx.PostEvent(self, my_evt)
