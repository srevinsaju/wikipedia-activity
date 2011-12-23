#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2007, One Laptop Per Child
#
# License: GPLv2
#
# Usage:
# ./tools2/expandtemplates.py directory 2>expand.log
# Ex:
# ./tools2/expandtemplates.py es_lat

import sys
reload(sys)
# Important! We'll be using stdout and stderr with
# UTF-8 chars. Without this, errors galore.
sys.setdefaultencoding('utf-8')

sys.path.append('.')

import os
import re
import codecs
from server import WPWikiDB
from server import ArticleIndex

START_HEADING = chr(1)
START_TEXT = chr(2)
END_TEXT = chr(3)

import config

# __main__

if len(sys.argv) > 1:
    directory = sys.argv[1]
else:
    print "Use expandtemplates.py directory"
    exit()

xml_file_name = config.input_xml_file_name
if xml_file_name.find('/') > -1:
    xml_file_name = xml_file_name[xml_file_name.find('/') + 1:]
path = os.path.join(directory, xml_file_name)

index = ArticleIndex('%s.processed.idx' % path)

lang = os.path.basename(path)[0:2]
## FIXME GETTEXT
templateprefixes = {'en': 'Template:', 'es': 'Plantilla:'}
templateprefix = templateprefixes[lang]

# load blacklist only once
templateblacklist = set()
templateblacklistpath = os.path.join(os.path.dirname(path),
                                     'template_blacklist')
if os.path.exists(templateblacklistpath):
    with open(templateblacklistpath, 'r') as f:
        for line in f.readlines():
            templateblacklist.add(line.rstrip().decode('utf8'))

wikidb = WPWikiDB(path, lang, templateprefix, templateblacklist)
rx = re.compile('(' + templateprefix + '|Wikipedia:)')

_output = codecs.open('%s.processed_expanded' % path,
        encoding='utf-8', mode='w')

for title in index.article_index:  # ['Argentina', '1857 revolt']:
    if rx.match(title):
        sys.stderr.write('SKIPPING: ' + title + "\n")
        continue

    sys.stderr.write('PROCESSING: ' + title + "\n")

    article_text = wikidb.getExpandedArticle(title)
    if article_text == None:
        sys.stderr.write('ERROR - SKIPPING: ' + title + "\n")
        continue

    _output.write(START_HEADING + '\n')
    _output.write(title + '\n')
    # in Python 2.x, len() over a unicode string
    # gives us the bytecount. Not compat w Python 3.
    _output.write("%s\n" % len(article_text))
    _output.write(START_TEXT + '\n')
    _output.write(article_text + '\n')
    _output.write(END_TEXT + '\n')

_output.close()
