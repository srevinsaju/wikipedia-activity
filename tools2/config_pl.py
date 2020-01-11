#!/usr/bin/env python
# -*- coding: utf-8 -*-
# These configuration params are used in the process to create
# a new wikipedia activity

import os
files_list = os.listdir()
for i in file_list:
    if i.endswith('.xml'):
        input_xml_file_name = i
        break
    else:
        input_xml_file_name = './plwiki-20111227-pages-articles.xml'

favorites_file_name = './favorites_pl.txt'
blacklist_file_name = './blacklist_pl.txt'

REDIRECT_TAGS = ['#REDIRECT', '#REDIRECCIÓN']

BLACKLISTED_NAMESPACES = ['WIKIPEDIA:', 'MEDIAWIKI:']

TEMPLATE_NAMESPACES = ['Szablon:']

LINKS_NAMESPACES = ['Kategoria']

FILE_TAG = 'Plik:'

MAX_IMAGE_SIZE = 300

# This part should not be changed
import platform

system_id = "%s%s" % (platform.system().lower(),
                          platform.architecture()[0][0:2])
if platform.processor().startswith('arm'):
    system_id = platform.processor()
