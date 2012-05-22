#!/usr/bin/env python
# -*- coding: utf-8 -*-
# create index
# use https://bitbucket.org/james_taylor/seek-bzip2

import codecs
import os
import sys
from subprocess import call, Popen, PIPE, STDOUT
import shutil
import re
import logging
import config

input_xml_file_name = config.input_xml_file_name


def normalize_title(title):
    return title.strip().replace(' ', '_').capitalize()


def create_index(pages_blacklist):
    output_file = open("%s.processed.idx" % input_xml_file_name, mode='w')
    num_block = 1
    index_file = open("%s.processed.bz2t" % input_xml_file_name, mode='r')
    index_line = index_file.readline()
    while index_line:
        parts = index_line.split()
        block_start = int(parts[0])
        print "Block %d starts at %d" % (num_block, block_start)
        position = 0
        # extract the block
        bzip_file = open("%s.processed.bz2" % input_xml_file_name, mode='r')
        cmd = ['../bin/%s/seek-bunzip' % config.system_id, str(block_start)]
        p = Popen(cmd, stdin=bzip_file, stdout=PIPE, stderr=STDOUT,
                close_fds=True)
        data_line = p.stdout.readline()
        while data_line:
            position += len(data_line)
            #print data_line
            if len(data_line) == 2:
                if ord(data_line[0]) == 1:
                    title = p.stdout.readline()
                    position += len(title)
                    # read article size
                    # size
                    size_line = p.stdout.readline()
                    position += len(size_line)
                    # \02
                    data_line = p.stdout.readline()
                    position += len(data_line)
                    title = title[0:-1].strip().capitalize()
                    if title not in pages_blacklist:
                        output_file.write("%s %d %d\n" % \
                            (title, num_block, position))
                        print "Article %s block %d position %d" % \
                            (title, num_block, position)
                    else:
                        print "* Blacklisted %s " % title

            data_line = p.stdout.readline()

        num_block += 1
        index_line = index_file.readline()

    output_file.close()


class FileListReader():

    def __init__(self, file_name):
        _file = codecs.open(file_name,
                                encoding='utf-8', mode='r')
        self.list = []
        line = _file.readline()
        while line:
            self.list.append(normalize_title(line))
            line = _file.readline()


class RedirectParser:

    def __init__(self, file_name):
        self.link_re = re.compile('\[\[.*?\]\]')
        # Load redirects
        input_redirects = codecs.open('%s.redirects_used' % file_name,
                encoding='utf-8', mode='r')

        self.redirects = {}
        for line in input_redirects.readlines():
            links = self.link_re.findall(unicode(line))
            if len(links) == 2:
                origin = links[0][2:-2]
                destination = links[1][2:-2]
                self.redirects[origin] = destination
            #print "Processing %s" % normalize_title(origin)
        logging.error("Loaded %d redirects" % len(self.redirects))
        input_redirects.close()


def create_search_index(input_xml_file_name, pages_blacklist):
    sys.path.append('..')
    from whoosh.index import create_in
    from whoosh.fields import TEXT, NUMERIC, Schema

    schema = Schema(title=TEXT(stored=True, phrase=False),
                block=NUMERIC(stored=True), position=NUMERIC(stored=True),
                redirect_to=TEXT(stored=True, phrase=False))
    if not os.path.exists("index_dir"):
        os.mkdir("index_dir")
    ix = create_in("index_dir", schema)
    writer = ix.writer()
    text_index_file = codecs.open("%s.processed.idx" % input_xml_file_name,
            encoding='utf-8', mode='r')
    line = text_index_file.readline()
    while line:
        parts = line.split()
        if len(parts) > 0:
            title_article = parts[0]
            block_article = parts[1]
            position_article = parts[2]
            title_article = normalize_title(title_article)
            if title_article not in pages_blacklist:
                writer.add_document(title=unicode(title_article),
                    block=int(block_article), position=int(position_article),
                    redirect_to=unicode(''))
            else:
                print "* Blacklisted %s " % title_article
        line = text_index_file.readline()

    # add redirects
    redirects_parser = RedirectParser(input_xml_file_name)
    for origin in redirects_parser.redirects.keys():
        origin = normalize_title(origin)
        try:
            destination = normalize_title(redirects_parser.redirects[origin])
            if origin not in pages_blacklist and \
                    destination not in pages_blacklist:
                writer.add_document(title=unicode(origin), block=0, position=0,
                                    redirect_to=unicode(destination))
            else:
                print "* Blacklisted %s " % origin
        except:
            print "ERROR: origin %s destination %s" % (origin, destination)
    writer.commit()
    text_index_file.close()


def create_bzip_table():
    """
    ../seek-bzip2/seek-bzip2/bzip-table <
    eswiki-20110810-pages-articles.xml.processed.bz2 >
    eswiki-20110810-pages-articles.xml.processed.bz2t
    """
    cmd = ['../bin/%s/bzip-table' % config.system_id]
    bzip_file = open('%s.processed.bz2' % input_xml_file_name, mode='r')
    table_file = open('%s.processed.bz2t' % input_xml_file_name, mode='w')
    call(cmd, stdin=bzip_file, stdout=table_file, close_fds=True)

if len(sys.argv) > 1:
    if sys.argv[1] == '--delete_old':
        if os.path.exists('%s.processed.bz2' % input_xml_file_name):
            os.remove('%s.processed.bz2' % input_xml_file_name)
        if os.path.exists('%s.processed.bz2t' % input_xml_file_name):
            os.remove('%s.processed.bz2t' % input_xml_file_name)
        if os.path.exists('%s.processed.idx' % input_xml_file_name):
            os.remove('%s.processed.idx' % input_xml_file_name)
        if os.path.exists('index_dir'):
            shutil.rmtree('index_dir')

if os.path.exists(config.blacklist_file_name):
    pages_blacklisted_reader = FileListReader(config.blacklist_file_name)
    pages_blacklist = pages_blacklisted_reader.list
    print "Loaded %d blacklisted pages" % len(pages_blacklist)
else:
    pages_blacklist = []

print 'Compressing .processed file'
if not os.path.exists('%s.processed.bz2' % input_xml_file_name):
    cmd = ['bzip2', '-zk', '%s.processed' % input_xml_file_name]
    p = call(cmd)
    if os.path.exists('%s.processed.bz2t' % input_xml_file_name):
        os.remove('%s.processed.bz2t' % input_xml_file_name)
else:
    print '.bz2 already exists. Skipping'

if not os.path.exists('%s.processed.bz2t' % input_xml_file_name):
    print 'Creating bzip2 table file'
    create_bzip_table()
else:
    print '.bz2t already exists. Skipping'

if not os.path.exists('%s.processed.idx' % input_xml_file_name):
    print 'Creating index file'
    create_index(pages_blacklist)
else:
    print '.idx already exists. Skipping'

if not os.path.exists('%s.index_dir'):
    print 'Creating locate database'
    create_search_index(input_xml_file_name, pages_blacklist)
else:
    print '.locate.db already exists. Skipping'
