#!/usr/bin/env python
# -*- coding: utf-8 -*-
# create index
# use https://bitbucket.org/james_taylor/seek-bzip2

import codecs
import os
from subprocess import call, Popen, PIPE, STDOUT

import config

input_xml_file_name = config.input_xml_file_name


def normalize_title(title):
    return title.strip().replace(' ', '_').capitalize()


def create_index():
    output_file  = open("%s.processed.idx" % input_xml_file_name, mode='w')
    num_block = 1
    index_file  = open("%s.processed.bz2t" % input_xml_file_name, mode='r')
    index_line = index_file.readline()
    while index_line:
        parts = index_line.split()
        block_start = int(parts[0])
        print "Block %d starts at %d" % (num_block, block_start) 
        position = 0
        # extract the block
        bzip_file = open("%s.processed.bz2" % input_xml_file_name, mode='r')
        cmd = ['../seek-bzip2/seek-bunzip', str(block_start)]
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
                    output_file.write("%s %d %d\n" % \
                        (title, num_block, position))
                    print "Article %s block %d position %d" % \
                        (title, num_block, position)

            data_line = p.stdout.readline()

        num_block += 1
        index_line = index_file.readline()

    output_file.close()

def create_bzip_table():
    """
    ../seek-bzip2/seek-bzip2/bzip-table <
    eswiki-20110810-pages-articles.xml.processed.bz2 >
    eswiki-20110810-pages-articles.xml.processed.bz2t 
    """
    cmd = ['../seek-bzip2/bzip-table']
    bzip_file = open('%s.processed.bz2' % input_xml_file_name, mode='r')
    table_file = open('%s.processed.bz2t' % input_xml_file_name, mode='w')
    call(cmd, stdin=bzip_file, stdout=table_file, close_fds=True)


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

print 'Creating index file'
create_index()
