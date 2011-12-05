#!/usr/bin/env python
# -*- coding: utf-8 -*-
# create index

import codecs
import os
from subprocess import Popen, PIPE, STDOUT

input_xml_file_name = './eswiki-20110810-pages-articles.xml'


class FileListReader():

    def __init__(self, file_name):
        _file = codecs.open(file_name,
                                encoding='utf-8', mode='r')
        self.list = []
        line = _file.readline()
        while line:
            self.list.append(line.strip())
            line = _file.readline()


class DataRetriever():

    def __init__(self, data_files_base):
        self._bzip_file_name = '%s.processed.bz2' % data_files_base
        self._bzip_table_file_name = '%s.processed.bz2t' % data_files_base
        self._index_file_name = '%s.processed.idx' % data_files_base

    def _get_article_position(self, article_title):
        index_file = codecs.open(self._index_file_name, encoding='utf-8',
                mode='r')
        index_line = index_file.readline()
        num_block = -1
        position = -1
        while index_line:
            words = index_line.split()
            article = words[0]
            if article == article_title:
                num_block = int(words[1])
                position = int(words[2])
                break
            index_line = index_file.readline()
        index_file.close()
        return num_block, position

    def _get_block_start(self, num_block):
        bzip_table_file = open(self._bzip_table_file_name, mode='r')
        n = num_block
        while n > 0:
            table_line = bzip_table_file.readline()
            n -= 1

        parts = table_line.split()
        block_start = int(parts[0])
        bzip_table_file.close()
        return block_start

    def get_text_article(self, article_title):
        output = ''
        num_block, position = self._get_article_position(article_title)
        print "Looking for article %s at block %d position %d" % \
                (article_title, num_block, position)

        block_start = self._get_block_start(num_block)
        print "Block %d starts at %d" % (num_block, block_start)

        # extract the block
        bzip_file = open(self._bzip_file_name, mode='r')
        cmd = ['./seek-bzip2/seek-bunzip', str(block_start)]
        p = Popen(cmd, stdin=bzip_file, stdout=PIPE, stderr=STDOUT,
                close_fds=True)

        while position > 0:
            line = p.stdout.readline()
            position -= len(line)

        finish = False
        while not finish:
            line = p.stdout.readline()
            if len(line) == 2:
                if ord(line[0]) == 3:
                    finish = True
                    break
            output += line
        return output

#data_retriever = DataRetriever(input_xml_file_name)
#data_retriever.get_text_article('Circo')
