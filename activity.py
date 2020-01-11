# Copyright (C) 2007, One Laptop Per Child
# -*- coding: utf-8 -*-
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA

from gettext import gettext as _

import os
import sys
import server
import logging
from gi.repository import Gtk, Gdk


from sugar3.activity import activity
from sugar3.graphics.toolbarbox import ToolbarButton
from sugar3.activity.widgets import StopButton
from sugar3.activity.widgets import ActivityToolbarButton
from sugar3.graphics.toolbarbox import ToolbarBox
from sugar3.activity.activity import get_bundle_path


from utils import read_conf_from_info

browse_path = None
try:
    from sugar3.activity.activity import get_bundle
    browse_bundle = get_bundle('org.sugarlabs.WebActivity')
    browse_path = browse_bundle.get_path()
except:
    if os.path.exists('../Browse.activity'):
        browse_path = '../Browse.activity'
    elif os.path.exists('/usr/share/sugar/activities/Browse.activity'):
        browse_path = '/usr/share/sugar/activities/Browse.activity'
    elif os.path.exists(os.path.expanduser('~/Activities/Browse.activity')):
        browse_path = os.path.expanduser('~/Activities/Browse.activity')

if browse_path is None:
    print('This activity need a Browser activity installed to run')

sys.path.append(browse_path)
import webactivity


from searchtoolbar import SearchToolbar


# Activity class, extends WebActivity.
class WikipediaActivity(webactivity.WebActivity):
    def __init__(self, handle):

        if not hasattr(self, 'confvars'):
            self.confvars = read_conf_from_info(get_bundle_path())

        logging.error("Starting server database: %s port: %s" %
                      (self.confvars['path'], self.confvars['port']))

        os.chdir(os.environ['SUGAR_BUNDLE_PATH'])

        self.confvars['ip'] = '0.0.0.0'
        server.run_server(self.confvars)

        handle.uri = 'http://%s:%s%s' % (
            self.confvars['ip'], self.confvars['port'],
            self.confvars['home_page'])

        webactivity.WebActivity.__init__(self, handle)
        self.browser = self._get_browser()
        self.build_toolbar()

    def build_toolbar(self):
        toolbar_box = ToolbarBox()
        
        activity_button = ActivityToolbarButton(self)
        toolbar_box.toolbar.insert(activity_button, 0)
        activity_button.show()

        # Search Gtk Entry
        search_item = Gtk.ToolItem()

        self.search_entry = Gtk.Entry()
        self.search_entry.connect('activate', self.search_entry_activate_cb)

        width = int(Gdk.Screen.width() / 3)
        self.search_entry.set_size_request(width, -1)

        self.search_entry.props.sensitive = True

        search_item.add(self.search_entry)
        self.search_entry.show()

        toolbar_box.toolbar.insert(search_item, -1)
        search_item.show()

        separator = Gtk.SeparatorToolItem()
        separator.props.draw = False
        separator.set_size_request(0, -1)
        separator.set_expand(True)
        toolbar_box.toolbar.insert(separator, -1)
        separator.show()

        stop = StopButton(self)
        toolbar_box.toolbar.insert(stop, -1)
        stop.show()

        self.set_toolbar_box(toolbar_box)
        toolbar_box.show_all()

    def _get_browser(self):
        if hasattr(self, '_browser'):
            # Browse < 109
            return self._browser
        else:
            return self._tabbed_view.props.current_browser

    def _go_home_button_cb(self, button):
        home_url = 'http://%s:%s%s' % (
            self.confvars['ip'], self.confvars['port'],
            self.confvars['home_page'])
        browser = self._get_browser()
        browser.load_uri(home_url)
        
    def normalize_title(self, title):
        s = title.strip().replace(' ', '_')
        return s[0].capitalize() + s[1:]

    def search_entry_activate_cb(self, entry):
        text = entry.get_text()
        text = self.normalize_title(text)
        home_url = 'http://%s:%s/wiki/%s' % (
            self.confvars['ip'], self.confvars['port'],
            text)
        browser = self._get_browser()
        browser.load_uri(home_url)
        
