#!/usr/bin/env python
# -*- coding: utf-8 -*-

# take a list of pages
# select a level default = 1
# prepare a list of links in the pages from the original list
# create a file with the titles of all the selected pages
# create a file with the content of all the selected pages

import codecs
import re
from xml.sax import make_parser, handler
import os
from operator import itemgetter
#import sqlite3

input_xml_file_name = './eswiki-20111112-pages-articles.xml'
favorites_file_name = 'favorites.txt'
blacklist_file_name = './blacklist.txt'

REDIRECT_TAGS = [u'#REDIRECT', u'#REDIRECCIÓN']

BLACKLISTED_NAMESPACES = ['Wikipedia:', 'MediaWiki:']

TEMPLATE_NAMESPACES = ['Plantilla:']

LINKS_NAMESPACES = [u'Categoría']


def normalize_title(title):
    return title.strip().replace(' ', '_').capitalize()


class FileListReader():

    def __init__(self, file_name):
        _file = codecs.open(file_name,
                                encoding='utf-8', mode='r')
        self.list = []
        line = _file.readline()
        while line:
            self.list.append(normalize_title(line))
            line = _file.readline()


class RedirectChecker:

    def __init__(self, file_name):
        self.conn = sqlite3.connect('%s.all_redirects.db' % file_name)
        self.conn.text_factory = lambda x: unicode(x, "utf-8", "ignore")
        self.cur = self.conn.cursor()

    def get_redirected(self, article_title):
        article_title = article_title.capitalize()
        self.cur.execute('select * from redirects where page = ?',
                (article_title,))
        row = self.cur.fetchone()
        if row is not None:
            #print row[0], row[1]
            return row[1]
        else:
            return None

    def clean(self):
        self.conn.close()


class RedirectParser:

    def __init__(self, file_name):
        self.link_re = re.compile('\[\[.*?\]\]')
        # Load redirects
        input_redirects = codecs.open('%s.redirects' % file_name,
                encoding='utf-8', mode='r')

        line = input_redirects.readline()
        self.redirects = {}
        count = 0
        while line:
            links = links = self.link_re.findall(unicode(line))
            if len(links) == 2:
                self.redirects[normalize_title(links[0])] = \
                        normalize_title(links[1])
            line = input_redirects.readline()
            count += 1
            print "Processing %d\r" % count,
        input_redirects.close()

    def get_redirected(self, article_title):
        try:
            article_title = article_title.capitalize()
            redirected = self.redirects[article_title]
        except:
            redirect = None
        return redirect


class LinksFilter():

    def __init__(self, file_name, redirects_checker, favorites):
        self.links = []
        input_links = codecs.open('%s.links' % file_name,
                encoding='utf-8', mode='r')
        line = input_links.readline()
        while line:
            words = line.split()
            if len(words) > 0:
                page = words[0]
                #print "Processing page %s \r" % page,
                if page in favorites:
                    print "Adding page %s" % page
                    for n in range(1, len(words) - 1):
                        link = words[n]
                        link = normalize_title(link)
                        # check if is a redirect
                        redirected = redirects_checker.get_redirected(link)
                        if redirected is not None:
                            link = redirected

                        if not link in self.links and \
                            not link in favorites:
                            self.links.append(link)
            line = input_links.readline()
        input_links.close()


class PagesProcessor(handler.ContentHandler):

    def __init__(self, file_name, selected_pages_list, pages_blacklist):
        handler.ContentHandler.__init__(self)
        self._page_counter = 0
        self._page = None
        self._output = codecs.open('%s.processed' % file_name,
                encoding='utf-8', mode='w')
        self._selected_pages_list = selected_pages_list
        self._pages_blacklist = pages_blacklist

    def startElement(self, name, attrs):
        if name == "page":
            self._page = {}
            self._page_counter += 1
        self._text = ""

    def characters(self, content):
        self._text = self._text + content

    def _register_page(self, register, title, content):
        register.write('\01\n')
        register.write('%s\n' % normalize_title(title))
        register.write('%d\n' % len(content))
        register.write('\02\n')
        register.write('%s\n' % content)
        register.write('\03\n')

    def endElement(self, name):
        if name == "title":
            self._title = self._text
        elif name == "text":
            self._page = self._text
        elif name == "page":

            for namespace in BLACKLISTED_NAMESPACES:
                if unicode(self._title).startswith(namespace):
                    return

            for namespace in TEMPLATE_NAMESPACES:
                if unicode(self._title).startswith(namespace):
                    return

            for tag in REDIRECT_TAGS:
                if unicode(self._page).startswith(tag):
                    return

            title = normalize_title(self._title)

            if title not in self._pages_blacklist and \
                title in self._selected_pages_list:
                print "%d Page '%s', length %d                   \r" % \
                        (self._page_counter, title, len(self._page)),
                # processed
                self._register_page(self._output, title, self._page)

        elif name == "mediawiki":
            self._output.close()
            print "Processed %d pages." % self._page_counter


class TemplatesCounter:

    def __init__(self, file_name, pages_selected, redirect_checker):
        self.templates_to_counter = {}
        input_links = codecs.open('%s.page_templates' % file_name,
                encoding='utf-8', mode='r')
        line = input_links.readline()
        while line:
            words = line.split()
            page = words[0]
            if page in pages_selected:
                print "Processing page %s \r" % page,
                for n in range(1, len(words) - 1):
                    template = words[n]
                    # check if is a redirect
                    redirected = redirect_checker.get_redirected(template)
                    if redirected is not None:
                        template = redirected

                    try:
                        self.templates_to_counter[template] = \
                                self.templates_to_counter[template] + 1
                    except:
                        self.templates_to_counter[template] = 1
            line = input_links.readline()
        input_links.close()


class CountedTemplatesReader():

    def __init__(self, file_name):
        _file = codecs.open('%s.templates_counted' % file_name,
                                encoding='utf-8', mode='r')
        self.templates = {}
        line = _file.readline()
        while line:
            words = line.split()
            template_name = words[0]
            cant_used = int(words[1])
            self.templates[normalize_title(template_name)] = \
                    {'cant': cant_used}
            line = _file.readline()


class TemplatesLoader():

    def __init__(self, file_name, templates_used):
        _file = codecs.open('%s.templates' % file_name,
                                encoding='utf-8', mode='r')
        self._output = codecs.open('%s.processed' % file_name,
                encoding='utf-8', mode='a')
        line = _file.readline()
        while line:
            if len(line) == 2:
                if ord(line[0]) == 1:
                    title = _file.readline()
                    size = _file.readline()
                    separator = _file.readline()
                    finish = False
                    template_content = ''
                    while not finish:
                        line = _file.readline()
                        #print line
                        if len(line) == 2:
                            if ord(line[0]) == 3:
                                finish = True
                                break
                        template_content += line
                    template_namespace = title[:title.find(':')]
                    template_name = title[title.find(':') + 1:]
                    template_name = normalize_title(template_name)
                    #print "checking", template_name,

                    if template_name in templates_used.keys():
                        #print "Adding", template_name,
                        title = template_namespace + ":" + template_name
                        self._register_page(title, template_content.strip())

            line = _file.readline()

    def _register_page(self, title, content):
        self._output.write('\01\n')
        self._output.write('%s\n' % normalize_title(title))
        self._output.write('%d\n' % len(content))
        self._output.write('\02\n')
        self._output.write('%s\n' % content)
        self._output.write('\03\n')


class RedirectsUsedWriter():

    def __init__(self, file_name, selected_pages_list, templates_used,
            redirect_checker):
        _output_redirects = codecs.open('%s.redirects_used' % file_name,
                encoding='utf-8', mode='w')

        pages_redirects = {}
        # check pages in redirects
        for title in selected_pages_list:
            title = normalize_title(title)
            redirected = redirect_checker.get_redirected(title)
            if redirected is not None:
                pages_redirects[title] = redirected
                _output_redirects.write('[[%s]]\t[[%s]]\n' %
                        (title, redirected))
        print "Found %d redirected pages" % len(pages_redirects)

        templates_redirects = {}
        # check pages in redirects
        for title in templates_used_reader.templates.keys():
            title = normalize_title(title)
            redirected = redirect_checker.get_redirected(title)
            if redirected is not None:
                templates_redirects[title] = redirected
                _output_redirects.write('[[%s]]\t[[%s]]\n' %
                        (title, redirected))

        print "Found %d redirected templates" % len(templates_redirects)

        _output_redirects.close()


if __name__ == '__main__':
    MAX_LEVELS = 1

    fav_reader = FileListReader(favorites_file_name)
    print "Loaded %d favorite pages" % len(fav_reader.list)

    if not os.path.exists(blacklist_file_name):
        pages_blacklisted_reader = FileListReader(blacklist_file_name)
        pages_blacklist = pages_blacklisted_reader
        print "Loaded %d blacklisted pages" % len(pages_blacklist)
    else:
        pages_blacklist = []

    print "Init redirects checker"
    #redirect_checker = RedirectChecker(input_xml_file_name)
    redirect_checker = RedirectParser(input_xml_file_name)

    level = 1

    selected_pages_file_name = '%s.pages_selected-level-%d' % \
                    (input_xml_file_name, MAX_LEVELS)
    if not os.path.exists(selected_pages_file_name):
        while level <= MAX_LEVELS:
            print "Processing links level %d" % level
            links_filter = LinksFilter(input_xml_file_name,
                    redirect_checker, fav_reader.list)
            fav_reader.list.extend(links_filter.links)
            level += 1

        print "Writing pages_selected-level-%d file" % MAX_LEVELS
        output_file = codecs.open(selected_pages_file_name,
                        encoding='utf-8', mode='w')
        for page  in fav_reader.list:
            output_file.write('%s\n' % page)
        output_file.close()
        selected_pages_list = fav_reader.list
    else:
        print "Loading selected pages"
        pages_selected_reader = FileListReader(selected_pages_file_name)
        selected_pages_list = pages_selected_reader.list

    if not os.path.exists('%s.processed' % input_xml_file_name):
        print "Writing .processed file"
        parser = make_parser()
        parser.setContentHandler(PagesProcessor(input_xml_file_name,
                selected_pages_list, pages_blacklist))
        parser.parse(input_xml_file_name)

        # if there are a .templates_counted file should be removed
        # because we need recalculate it
        if os.path.exists('%s.templates_counted' % input_xml_file_name):
            os.remove('%s.templates_counted' % input_xml_file_name)

    if not os.path.exists('%s.templates_counted' % input_xml_file_name):
        print "Processing templates"
        templates_counter = TemplatesCounter(input_xml_file_name,
                selected_pages_list, redirect_checker)

        print "Sorting counted templates"
        items = templates_counter.templates_to_counter.items()
        items.sort(key=itemgetter(1), reverse=True)

        print "Writing templates_counted file"
        output_file = codecs.open('%s.templates_counted' % input_xml_file_name,
                        encoding='utf-8', mode='w')
        for n  in range(len(items)):
            output_file.write('%s %d\n' % (items[n][0], items[n][1]))
        output_file.close()

        print "Loading templates used"
        templates_used_reader = CountedTemplatesReader(input_xml_file_name)
        print "Readed %d templates used" % len(templates_used_reader.templates)

        print "Adding used templates to .processed file"
        templates_loader = TemplatesLoader(input_xml_file_name,
                templates_used_reader.templates)

        if not os.path.exists('%s.redirects_used' % input_xml_file_name):
            redirects_used_writer = RedirectsUsedWriter(input_xml_file_name,
                    selected_pages_list, templates_used_reader.templates,
                    redirect_checker)
