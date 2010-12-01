#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2007, One Laptop Per Child
#
# License: GPLv2
#
# Usage:
#  expandtemplates.py <dbdir/dbfile> 2>expand.log | bzip -c -9 - > foo/bar.processed
#
from __future__ import with_statement
import sys
reload(sys)
# Important! We'll be using stdout and stderr with
# UTF-8 chars. Without this, errors galore.
sys.setdefaultencoding('utf-8')

sys.path.append('.')

import os, select, time
import subprocess
import codecs
from StringIO import StringIO
import cgi
import errno
import tempfile
import re
import wp
import xml.dom.minidom
from pylru import lrudecorator

START_HEADING = chr(1)
START_TEXT = chr(2)
END_TEXT = chr(3)

# Uncomment to print out a large dump from the template expander.
#os.environ['DEBUG_EXPANDER'] = '1'

try:
    from hashlib import md5
except ImportError:
    from md5 import md5

import mwlib.htmlwriter
from mwlib import parser, scanner, expander


class ArticleIndex:
    # Prepare an in-memory index, using the already generated 
    # index file.  

    def __init__(self, path):
        self.article_index = []
        with codecs.open(path, mode='r', encoding='utf-8') as f:
            for line in f.readlines():
                m = re.search(r'(.*?)\s*\d+$', line)
                if m is None:
                    raise AssertionError("Match didn't work")
                self.article_index.append(m.group(1))
        self.article_index.sort()
        
    def __contains__(self, x):
        return x in self.article_index

    def rawindex(self):
        return self.article_index
    
class WPWikiDB:
    """Retrieves article contents for mwlib."""

    def getRawArticle(self, title, followRedirects=True):
        # Retrieve article text, recursively following #redirects.
        if title == '':
            return ''

        oldtitle = ""
        while True:
            # Replace underscores with spaces in title.
            title = title.replace("_", " ")
            # Capitalize the first letter of the article -- Trac #6991.
            title = title[0].capitalize() + title[1:]

            if title == oldtitle:
                article_text = ""
                break

            article_text = wp_load_article(title.encode('utf8'))
            if article_text == None:
                # something's wrong
                return None
            #sys.stderr.write("!!!%s!!!" % article_text)
            article_text = unicode(article_text, 'utf8')
            
            # To see unmodified article_text, uncomment here.
            # print article_text
            if not followRedirects:
                break

            m = re.match(r'^\s*\#?redirect\s*\:?\s*\[\[(.*)\]\]', article_text, re.IGNORECASE|re.MULTILINE)
            if not m:
                break

            oldtitle = title
            title = m.group(1)

        # Stripping leading & trailing whitespace fixes template expansion.
        article_text = article_text.lstrip()
        article_text = article_text.rstrip()

        return article_text

    def getTemplate(self, title, followRedirects=False):
        return self.getRawArticle(title)

    def expandArticle(self, article_text, title):
        template_expander = expander.Expander(article_text, pagename=title, wikidb=self)
        return template_expander.expandTemplates()
        
    def getExpandedArticle(self, title):
        return self.expandArticle(self.getRawArticle(title), title)

class HTMLOutputBuffer:
    """Buffers output and converts to utf8 as needed."""

    def __init__(self):
        self.buffer = ''

    def write(self, obj):
        if isinstance(obj, unicode):
            self.buffer += obj.encode('utf8')
        else:
            self.buffer += obj
    
    def getvalue(self):
        return self.buffer

def load_db(dbname):
    wp.wp_load_dump(
        dbname + '.processed',
        dbname + '.locate.db',
        dbname + '.locate.prefixdb',
        dbname + '.blocks.db')

# Cache articles and specially templates
@lrudecorator(100)
def wp_load_article(title):
   return wp.wp_load_article(title)
   #return wp_load_article_fork(title) 

# Fork the wp lookup as a subprocess, so it can return None on error
# wp.wp_load_article() exit(1)s on error .
# We pay a 20% wall time penalty in forking and reading/waiting for
# the child process.
def wp_load_article_fork(title):
    pid, fd = os.forkpty()
    if pid ==  0:
        # child only does wp lookup
        article_text = wp.wp_load_article(title)
        sys.stdout.write(article_text)
        sys.exit(os.EX_OK)

    article_text = ''
    while True: #os.kill(pid, 0):
        try: # try catch, as it may have died
            b = os.read(fd, 1024 * 1024)
        except:
            break
        if not b:
            break
        article_text = article_text + b

    (pid, ex_status) = os.waitpid(pid, 0)
    #print "%s %s " % (pid, ex_status)
    if ex_status == os.EX_OK:
        return article_text
    else:
        return None

# __main__

# prep a isting of redirects. wp.so hides them from
# us, which would bloat our

load_db(sys.argv[1])
index = ArticleIndex('%s.index.txt' % sys.argv[1])

rawindex = index.rawindex()

wikidb = WPWikiDB()
rx = re.compile('(Plantilla|Template|Wikipedia):')

for title in rawindex: #['1812 invasion of Russia', '1857 revolt']: #rawindex:
    if rx.match(title):
        continue
    
    sys.stderr.write('PROCESSING: ' + title + "\n")
    
    article_text  = wikidb.getRawArticle(title, followRedirects=False)
    if article_text == None:
        sys.stderr.write('ERROR - SKIPPING: ' + title + "\n")
        continue

    # we don't expand nor follow redirects
    m = re.match(r'^\s*\#?redirect\s*\:?\s*\[\[(.*)\]\]',
                 article_text, re.IGNORECASE|re.MULTILINE)
    if not m:
        article_text = wikidb.getExpandedArticle(title)

    sys.stdout.write(START_HEADING + '\n')
    sys.stdout.write(title + '\n')
    # in Python 2.x, len() over a unicode string
    # gives us the bytecount. Not compat w Python 3.
    sys.stdout.write("%s\n" % len(article_text))
    sys.stdout.write(START_TEXT + '\n')
    sys.stdout.write(article_text + '\n')
    sys.stdout.write(END_TEXT + '\n')

    # break
