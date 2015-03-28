# -*- coding: utf-8 -*-
"""Various utility functions for GUI management"""
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
__all__ = 'NULL_FIELD BORDER_SIZE build_menus update_min_size file_save_dialog file_open_dialog'.split()

import wx, os.path


NULL_FIELD = u'—'

BORDER_SIZE=4


def build_menus(widget, parent, menus, roles=set()):
    """
    Builds a menu structure into the parent object. "parent" must be a
    wxMenu or wxMenuBar (or do the right thing when C{Append()} and
    C{AppendSeparator()} are called).

    If any menu items requires specific roles (or their callbacks use the
    C{@user_roles} function decorator), the item roles will be matched
    against the passed roles parameter and a match will be required before
    for the menu to be added to the widget.

    Recognized Menu Item Keys:

        roles: list of role names which will be compared against roles
            passed to build_menus. If intersection is non-empty, menu item
            will be shown.

        callback: function which will be called when menu item is clicked.

        label: text content of the menu item. Include & and \t escapes for
            quick key and keyboard shortcuts.

        submenu: array of more menus will be used as a submenu.

        show: if present and False, menu item will be excluded. Default is
            to show.
    """

    # used to avoid placing two consecutive separators (when items hidden due to permissions)
    have_items = 0
    need_separator = False

    for m in menus:
        # Handle the only non-reference menu item:
        if m == '---':
            need_separator = True
            continue

        # If user lacks proper permissions, do not display item
        if not m.get("show", True):
            continue
        if "roles" in m and not(roles & m["roles"]):
            continue
        if "callback" in m and hasattr(m["callback"], "role_allowed") and not(m["callback"].role_allowed(*roles)):
            continue

        if need_separator and have_items:
            parent.AppendSeparator()
            need_separator = False

        # Displaying an item
        have_items += 1
        menu_item = None

        if "submenu" in m:
            menu_item = wx.Menu()
            if build_menus(widget, menu_item, m["submenu"], roles=roles):
                parent.Append(menu_item, m["label"])
            else:
                have_items -= 1

        elif "callback" in m:
            menu_item = parent.Append(wx.NewId(), m["label"])
            widget.Bind(wx.EVT_MENU, m["callback"], menu_item)

        if not menu_item:
            raise Exception("Unknown menu type "+str(m))

    return have_items


def user_roles(*roles):
    """
    Function decorator for requiring specific roles to call a method.
    Defines three attributes on the function:

        - func.user_allowed(user)       - function returning true if the user has any of the required roles
        - func.role_allowed(role, ...)  - function returning true if any of the required roles are listed
        - func.roles_sufficient         - set of the sufficient roles

    @attention: This decorator will NOT wrap the function with a permission
    check. It only defines the above attributes for introspection purposes.
    """
    roles_set = set(roles)
    def user_allowed(user):
        return roles_set & user.role_names()
    def role_allowed(*r):
        return roles_set & set(r)

    def role_adder(func):
        func.user_allowed  = user_allowed
        func.role_allowed  = role_allowed
        func.roles_sufficient = roles_set
        return func
    return role_adder


def update_min_size(widget, width=None, height=None, size=None):
    """Utility function to set minimum width/height of a widget."""
    size = size or widget.GetMinSize()
    if width:  size.SetWidth( max(width,  size.GetWidth()))
    if height: size.SetHeight(max(height, size.GetHeight()))
    widget.SetMinSize(size)
    return size


def file_save_dialog(parent, title, wildcard, filename, app=None):
    """File Save Dialog with default values from app-stash"""
    if app is None:
        app = parent.app

    file_dialog = wx.FileDialog(
        parent,
        title,
        defaultDir=app.file_dialog_path,
        defaultFile=filename,
        wildcard=wildcard,
        style=wx.FD_SAVE|wx.FD_OVERWRITE_PROMPT,
    )

    if (file_dialog.ShowModal() == wx.ID_OK):
        app.file_dialog_path = os.path.dirname(file_dialog.GetPath())
        ret = file_dialog.GetPath()
    else:
        ret = None

    file_dialog.Destroy()
    return ret


def file_open_dialog(parent, title, wildcard, app=None):
    """File Open Dialog with default values from app-stash"""
    if app is None:
        app = parent.app

    file_dialog = wx.FileDialog(
        parent,
        title,
        defaultDir=app.file_dialog_path,
        wildcard=wildcard,
        style=wx.FD_OPEN|wx.FD_FILE_MUST_EXIST,
    )

    if (file_dialog.ShowModal() == wx.ID_OK):
        app.file_dialog_path = os.path.dirname(file_dialog.GetPath())
        ret = file_dialog.GetPath()
    else:
        ret = None

    file_dialog.Destroy()
    return ret
