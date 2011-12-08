#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Test to use sax to parse wikimedia xml files

from xml.sax import make_parser, handler
import codecs
import re
import sqlite3

input_xml_file_name = './eswiki-20111112-pages-articles.xml'

REDIRECT_TAGS = [u'#REDIRECT', u'#REDIRECCIÓN']

BLACKLISTED_NAMESPACES = ['Wikipedia:', 'MediaWiki:']

TEMPLATE_NAMESPACES = ['Plantilla:']

LINKS_NAMESPACES = [u'Categoría']


class WikimediaXmlPagesProcessor(handler.ContentHandler):

    def __init__(self, file_name):
        handler.ContentHandler.__init__(self)
        self._page_counter = 0
        self._page = None
        self._output = codecs.open('%s.all_pages' % file_name,
                encoding='utf-8', mode='w')
        self._output_titles = codecs.open('%s.titles' % file_name,
                encoding='utf-8', mode='w')
        self._output_redirects = codecs.open('%s.redirects' % file_name,
                encoding='utf-8', mode='w')
        self._output_templates = codecs.open('%s.templates' % file_name,
                encoding='utf-8', mode='w')
        self._output_blacklisted = codecs.open('%s.blacklisted' % file_name,
                encoding='utf-8', mode='w')
        self._output_links = codecs.open('%s.links' % file_name,
                encoding='utf-8', mode='w')
        self._output_page_templates = codecs.open('%s.page_templates' % 
                file_name, encoding='utf-8', mode='w')
        self.conn = sqlite3.connect('%s.all_redirects.db' % file_name)
        self.conn.execute('create table redirects(page, redirect_to)')
        self.cur = self.con.cursor()
        self.link_re = re.compile('\[\[.*?\]\]')
        self.template_re = re.compile('{{.*?}}')

    def startElement(self, name, attrs):
        if name == "page":
            self._page = {}
            self._page_counter += 1
        self._text = ""

    def characters(self, content):
        self._text = self._text + content

    def _register_page(self, register):
        register.write('\01\n')
        register.write('%s\n' % self._title)
        register.write('%d\n' % len(self._page))
        register.write('\02\n')
        register.write('%s\n' % self._page)
        register.write('\03\n')

    def endElement(self, name):
        if name == "title":
            self._title = self._text
        elif name == "text":
            self._page = self._text
        elif name == "page":

            print "Page %d '%s', length %d                   \r" % \
                    (self._page_counter, self._title, len(self._page)),

            for namespace in BLACKLISTED_NAMESPACES:
                if unicode(self._title).startswith(namespace):
                    self._register_page(self._output_blacklisted)
                    return


            is_redirect = False
            for tag in REDIRECT_TAGS:
                if unicode(self._page).startswith(tag):
                    is_redirect = True
                    break

            if is_redirect:
                # redirected pages

                page_destination = "ERROR"
                search = self.link_re.search(self._page)
                if search is not None:
                    # keep out the [[]]
                    page_destination = search.group()[2:-2]
                    page_destination = page_destination.strip().capitalize()
                origin = self._title.strip().replace(' ', '_').capitalize()

                self._output_redirects.write('[[%s]]\t[[%s]]\n' %
                        (origin, page_destination))

                self.cur.execute('insert into redirects (page, redirect_to) ' +
                            'values (?,?)', (origin, page_destination))
            else:

                for namespace in TEMPLATE_NAMESPACES:
                    if unicode(self._title).startswith(namespace):
                        # templates
                        self._register_page(self._output_templates)
                        return


                # titles
                self._output_titles.write('%s\n' % self._title)

                # processed
                self._register_page(self._output)

                title = self._title.replace(' ', '_')
                # links
                links = self.link_re.findall(unicode(self._page))
                self._output_links.write('%s ' % title)
                for link in links:
                    # remove '[[' and ']]'
                    link = link[2:-2]
                    # Check if have a valid namespace
                    colon_position = link.find(':')
                    valid = True
                    if colon_position > -1:
                        namespace = link[:colon_position]
                        valid = namespace in LINKS_NAMESPACES
                    if valid:
                        # if there are a pipe remove the right side
                        pipe_position = link.find('|')
                        if pipe_position > -1:
                            link = link[:pipe_position]
                        link = link.replace(' ', '_')
                        link = link.capitalize()
                        self._output_links.write('%s ' % link)
                self._output_links.write('\n')

                # find templates used in the pages
                templates = self.template_re.findall(unicode(self._page))
                templates_list = []
                for template in templates:
                    # remove '{{' and '}}'
                    template = template[2:-2]
                    # if there are a pipe remove the right side
                    pipe_position = template.find('|') 
                    if pipe_position > -1:
                        template = template[:pipe_position]
                    # if there are a : remove the right side
                    colon_position = template.find(':') 
                    if colon_position > -1:
                        template = template[:colon_position]
                    if len(template) == 0:
                        break
                    # ignore templates starting with # or {
                    if template[0] == '#' or template[0] == '{':
                        break
                    template = template.strip().replace(' ', '_')
                    template = template.capitalize()
                    # only add one time by page
                    if not template in templates_list: 
                        templates_list.append(template)

                if len(templates_list) > 0:
                    self._output_page_templates.write('%s ' % title)
                    for template in templates_list:
                        self._output_page_templates.write('%s ' % template)
                    self._output_page_templates.write('\n')


        elif name == "mediawiki":
            self._output.close()
            self._output_titles.close()
            self._output_redirects.close()
            self._output_templates.close()
            self._output_blacklisted.close()
            self._output_links.close()
            self._output_page_templates.close()
            self.conn.commit()
            self.conn.close()
            print "Processed %d pages." % self._page_counter


parser = make_parser()
parser.setContentHandler(WikimediaXmlPagesProcessor(input_xml_file_name))
parser.parse(input_xml_file_name)
