#!/usr/bin/env python
# -*- coding: utf-8 -*-
# create index

import codecs
import os
from subprocess import Popen, PIPE, STDOUT
import re
import sqlite3

def normalize_title(title):
    return title.strip().replace(' ', '_').capitalize()


class DataRetriever():

    def __init__(self, data_files_base):
        self._bzip_file_name = '%s.processed.bz2' % data_files_base
        self._bzip_table_file_name = '%s.processed.bz2t' % data_files_base
        self._index_file_name = '%s.processed.idx' % data_files_base
        self.template_re = re.compile('({{.*?}})')
        self.conn = sqlite3.connect('%s.all_redirects.db' % data_files_base)
        self.conn.text_factory = lambda x: unicode(x, "utf-8", "ignore")

    def _get_article_position(self, article_title):
        article_title = normalize_title(article_title)
        #index_file = codecs.open(self._index_file_name, encoding='utf-8',
        #        mode='r')
        index_file = open(self._index_file_name, mode='r')

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

        if num_block == -1:
            # look at redirects
            print "looking for '%s' at redirects table" % article_title
            cur = self.conn.cursor()
            cur.execute('select * from redirects where page = ?',
                    (article_title,))
            row = cur.fetchone()
            if row is not None:
                print row
                if row[0] == row[1]:
                    # to avoid infinite recursion
                    return -1, -1
                return self._get_article_position(row[1])

        return num_block, position

    def _get_block_start(self, num_block):
        bzip_table_file = open(self._bzip_table_file_name, mode='r')
        n = num_block
        table_line = ''
        while n > 0:
            table_line = bzip_table_file.readline()
            n -= 1
        if table_line == '':
            return -1
        parts = table_line.split()
        block_start = int(parts[0])
        bzip_table_file.close()
        return block_start

    def get_expanded_article(self, article_title):
        """
        This method does not do real template expansion
        is only used to test all the needed templates and redirects are
        available.
        """
        text_article = self.get_text_article(article_title)
        templates_cache = {}
        expanded_article = ''
        parts = self.template_re.split(text_article)
        for part in parts:
            if part.startswith('{{'):
                part = part[2:-2]
                #print "TEMPLATE: %s" % part
                if part.find('|') > -1:
                    template_name = part[:part.find('|')]
                else:
                    template_name = part
                # TODO: Plantilla should be a parameter
                template_name = normalize_title('Plantilla:%s' % template_name)
                if template_name in templates_cache:
                    expanded_article += templates_cache[template_name]
                else:
                    templates_content = self.get_text_article(template_name)
                    expanded_article += templates_content
                    templates_cache[template_name] = templates_content
            else:
                expanded_article += part
        return expanded_article

    def get_text_article(self, article_title):
        output = ''
        #print "Looking for article %s" % article_title
        num_block, position = self._get_article_position(article_title)
        #print "Found at block %d position %d" % (num_block, position)

        block_start = self._get_block_start(num_block)
        #print "Block %d starts at %d" % (num_block, block_start)
        if block_start == -1:
            return ""

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

if __name__ == '__main__':
    data_retriever = DataRetriever('./eswiki-20111112-pages-articles.xml')
    data_retriever.get_expanded_article('Argentina')
    #print data_retriever.get_text_article('Argentina')
