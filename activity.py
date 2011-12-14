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

OLD_TOOLBAR = False
try:
    from sugar3.graphics.toolbarbox import ToolbarBox, ToolbarButton
except ImportError:
    OLD_TOOLBAR = True

#from sugar.activity import registry
#activity_info = registry.get_registry().get_activity('org.laptop.WebActivity')

#sys.path.append(activity_info.path)
if os.path.exists('../Browse.activity'):
    sys.path.append('../Browse.activity')
elif os.path.exists('/usr/share/sugar/activities/Browse.activity'):
    sys.path.append('/usr/share/sugar/activities/Browse.activity')
else:
    print 'This activity need a Browser activity installed to run'

import webactivity

from searchtoolbar import SearchToolbar


# Activity class, extends WebActivity.
class WikipediaActivity(webactivity.WebActivity):
    def __init__(self, handle):

        logging.error("Starting server database: %s port: %s" %
                (self.WIKIDB, self.HTTP_PORT))

        os.chdir(os.environ['SUGAR_BUNDLE_PATH'])

        #server.load_db(self.WIKIDB)
        server.run_server({'path': self.WIKIDB,
                           'port': int(self.HTTP_PORT)})

        handle.uri = 'http://localhost:%s%s' % (self.HTTP_PORT, self.HOME_PAGE)

        webactivity.WebActivity.__init__(self, handle)

        self.searchtoolbar = SearchToolbar(self)
        if OLD_TOOLBAR:
            self.toolbox.add_toolbar(_('Search'), self.searchtoolbar)
        else:
            search_toolbar_button = ToolbarButton()
            search_toolbar_button.set_page(self.searchtoolbar)
            search_toolbar_button.props.icon_name = 'search-wiki'
            search_toolbar_button.props.label = _('Search')
            self.get_toolbar_box().toolbar.insert(search_toolbar_button, 1)
            search_toolbar_button.show()
            # Hide add-tabs button
            if hasattr(self._primary_toolbar, '_add_tab'):
                self._primary_toolbar._add_tab.hide()

        self.searchtoolbar.show()

    def _get_browser(self):
        if hasattr(self, '_browser'):
            # Browse < 109
            return self._browser
        else:
            return self._tabbed_view.props.current_browser

    def _go_home_button_cb(self, button):
        home_url = 'http://localhost:%s%s' % (self.HTTP_PORT, self.HOME_PAGE)
        browser = self._get_browser()
        browser.load_uri(home_url)
