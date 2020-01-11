#!/usr/bin/env python
# -*- coding: utf-8 -*-
# create index

from subprocess import Popen, PIPE, STDOUT
import re
import os
import logging
import codecs
import sqlite3


def normalize_title(title):
    s = title.strip().replace(' ', '_')
    return s[0].capitalize() + s[1:]

class RedirectParser:

    def __init__(self, file_name):
        self.link_re = re.compile('\[\[.*?\]\]')
        # Load redirects
        input_redirects = codecs.open('%s.redirects_used' % file_name,
                encoding='utf-8', mode='r')

        line = input_redirects.readline()
        self.redirects = {}
        count = 0
        while line:
            links = self.link_re.findall(str(line))
            if len(links) == 2:
                origin = normalize_title(links[0][2:-2])
                destination = normalize_title(links[1][2:-2])
                self.redirects[origin] = destination
            line = input_redirects.readline()
            count += 1
            print("Processing %d\r" % count, end=' ')
        input_redirects.close()

    def get_redirected(self, article_title):
        try:
            redirect = self.redirects[normalize_title(article_title)]
        except:
            redirect = None
        return redirect

class DataRetriever():

    def __init__(self, system_id, data_files_base):
        self.system_id = system_id
        self._seek_bunzip_cmnd = self._check_seek_bunzip_cmnd()
        self._bzip_file_name = '%s.processed.bz2' % data_files_base
        self._bzip_table_file_name = '%s.processed.bz2t' % data_files_base
        self.template_re = re.compile('({{.*?}})')
        base_path = os.path.dirname(data_files_base)
        self._db_path = os.path.join(base_path, "search.db")
        self._idx_path = "%s.processed.idx" % data_files_base
        # TODO: I need control cache size
        self.templates_cache = {}
        self.redirects_checker = RedirectParser(data_files_base)

    def _check_seek_bunzip_cmnd(self):
        # check if seek-bunzip is installed in the system
        installed_path = '/usr/bin/seek-bunzip'
        if os.path.exists(installed_path) and \
                os.access(installed_path, os.X_OK):
            return installed_path

        # if not installed use the binary for the platform
        # included with the activity
        return './bin/%s/seek-bunzip' % self.system_id

    def check_existence(self, article_title):
        article_title = normalize_title(article_title)
        num_block, posi = self._get_article_position(article_title)
        return num_block > -1 and posi > -1

    def _get_article_position(self, article_title):
        article_title = normalize_title(article_title)
        #index_file = codecs.open(self._index_file_name, encoding='utf-8',
        #        mode='r')
        index_file = open(self._idx_path, mode='r')

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
            redirect = self.redirects_checker.get_redirected(article_title)
            print("Searching redirect from %s to %s" % (article_title,
                    redirect))
            if redirect is not None:
                return self._get_article_position(redirect)

        print("Numblock %d, position %d" % (num_block, position))
        return num_block, position
        
        """
        article_title = normalize_title(article_title)
        # look at the title in the index database
        conn = sqlite3.connect(self._db_path)
        if article_title.find('"'):
            article_title = article_title.replace('"', '')

        sql = 'SELECT * from articles where title=?'
        results = conn.execute(sql, (article_title,))
        try:
            row = next(results)
            num_block = row[1]
            position = row[2]
            redirect_to = row[3]
            logging.error('Search article %s returns %s',
                    article_title, row)
        except:
            num_block = -1
            position = -1
        conn.close()
        

        if num_block == 0 and position == 0:
            # if block and position = 0 serach with the redirect_to value
            num_block2, position2 = \
                    self._get_article_position(redirect_to)
            if num_block2 == 0 and position2 == 0:
                logging.error('Prevent recursion')
                return -1, -1
            else:
                return num_block2, position2
        return num_block, position
        """
        

    def check_existence_list(self, article_title_list):
        if not article_title_list:
            return []

        conn = sqlite3.connect(self._db_path)
        search_list = '('
        for article_title in article_title_list:
            search_list = search_list + \
                    '"' + normalize_title(article_title) + '",'
        search_list = search_list[:-1] + ')'
        #logging.error(search_list)
        sql = 'SELECT * from articles where title in %s' % search_list
        #logging.error(sql)
        results = conn.execute(sql)
        row = next(results)
        articles = []
        try:
            while row:
                articles.append(row[0])
                row = next(results)
        except:
            pass
        conn.close()
        return articles

    def search(self, article_title):
        conn = sqlite3.connect(self._db_path)
        search_word = '%' + article_title + '%'
        sql = "SELECT * from articles where title like ?"
        results = conn.execute(sql, (search_word,))
        row = next(results)
        articles = []
        try:
            while row:
                articles.append(row[0])
                row = next(results)
        except:
            pass
        conn.close()
        return articles

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
                if template_name in self.templates_cache:
                    expanded_article += self.templates_cache[template_name]
                else:
                    templates_content = self.get_text_article(template_name)
                    expanded_article += templates_content
                    self.templates_cache[template_name] = templates_content
            else:
                expanded_article += part
        return expanded_article

    def get_text_article(self, article_title):
        #print "Looking for article %s" % article_title
        num_block, position = self._get_article_position(article_title)
        #print "Found at block %d position %d" % (num_block, position)
        return self._get_block_text(num_block, position)

    def _get_block_text(self, num_block, position):
        output = ''
        block_start = self._get_block_start(num_block)
        #print "Block %d starts at %d" % (num_block, block_start)
        if block_start == -1:
            return ""

        # extract the block
        bzip_file = open(self._bzip_file_name, mode='r')
        cmd = [self._seek_bunzip_cmnd, str(block_start)]
        p = Popen(cmd, stdin=bzip_file, stdout=PIPE, stderr=STDOUT,
                close_fds=True)

        while position > 0:
            line = p.stdout.readline()
            position -= len(line)

        finish = False
        while not finish:
            line = p.stdout.readline().decode()
            if line == '':
                # end of block?
                output += self._get_block_text(num_block + 1, 0)
                break
            if len(line) == 2:
                if ord(line[0]) == 3:
                    finish = True
                    break
            output += line
        p.stdout.close()
        #logging.error(output)
        return output
