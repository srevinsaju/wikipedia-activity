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
from sugar3.graphics.toolbarbox import ToolbarButton
from sugar3.activity.activity import get_bundle_path
from sugar3.graphics.toolbarbox import ToolbarBox
from utils import read_conf_from_info

browse_path = None

from sugar3.activity.activity import get_bundle
browse_bundle = get_bundle('org.sugarlabs.BrowseActivity')
browse_path = browse_bundle.get_path()

if browse_path is None:
    print('This activity need a Browser activity installed to run')

sys.path.append(browse_path)

from sugar3.activity import activity

from searchtoolbar import SearchToolbar

class WikipediaActivity(activity.Activity):
    def __init__(self, handle):

        if not hasattr(self, 'confvars'):
            self.confvars = read_conf_from_info(get_bundle_path())

        logging.error("Starting server database: %s port: %s" %
                      (self.confvars['path'], self.confvars['port']))
        os.chdir(os.environ['SUGAR_BUNDLE_PATH'])
        port = 8000
        start_server = 'python3 -m http.server --directory static {}'.format(port)
        os.system(start_server)
        activity.Activity.__init__(self, handle)
        toolbar_box = ToolbarBox()
        self.searchtoolbar = SearchToolbar(self)
        search_toolbar_button = ToolbarButton()
        search_toolbar_button.set_page(self.searchtoolbar)
        search_toolbar_button.props.icon_name = 'search-wiki'
        search_toolbar_button.props.label = _('Search')
        toolbar_box.toolbar.insert(search_toolbar_button, 1)
        search_toolbar_button.show()
        # Hide add-tabs button
        #toolbar_box.toolbar._add_tab.hide()
        self.searchtoolbar.show()
        self.set_toolbar_box(toolbar_box)
        toolbar_box.show_all()

    def _get_browser(self):
        if hasattr(self, '_browser'):
            # Browse < 109
            return self._browser
        else:
            return self._tabbed_view.props.current_browser

    def _go_home_button_cb(self, button):
        lang = 'en'
        home_url = 'http://0.0.0.0:{}/index_{}.html'.format(port, lang)
        browser = self._get_browser()
        browser.load_uri(home_url)
