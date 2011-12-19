#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2007, One Laptop Per Child
#
# License: GPLv2
#
# Usage:
#  expandtemplates.py <dbdir/dbfile> 2>expand.log | bzip -c -9 - > foo/bar.processed
# Or generate the proccessed file and compress it later
# Ex:
# python ./tools2/expandtemplates.py es_new/eswiki-20111112-pages-articles.xml \
#     > es_new/eswiki-20111112-pages-articles.xml.processed

import sys
reload(sys)
# Important! We'll be using stdout and stderr with
# UTF-8 chars. Without this, errors galore.
sys.setdefaultencoding('utf-8')

sys.path.append('.')

import os
import re

from server import WPWikiDB
from server import ArticleIndex

START_HEADING = chr(1)
START_TEXT = chr(2)
END_TEXT = chr(3)


# __main__

path = sys.argv[1]
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

for title in index.article_index:  # ['Argentina', '1857 revolt']:
    if rx.match(title):
        sys.stderr.write('SKIPPING: ' + title + "\n")
        continue

    sys.stderr.write('PROCESSING: ' + title + "\n")

    article_text = wikidb.getRawArticle(title, followRedirects=False)
    if article_text == None:
        sys.stderr.write('ERROR - SKIPPING: ' + title + "\n")
        continue

    sys.stdout.write(START_HEADING + '\n')
    sys.stdout.write(title + '\n')
    # in Python 2.x, len() over a unicode string
    # gives us the bytecount. Not compat w Python 3.
    sys.stdout.write("%s\n" % len(article_text))
    sys.stdout.write(START_TEXT + '\n')
    sys.stdout.write(article_text + '\n')
    sys.stdout.write(END_TEXT + '\n')
