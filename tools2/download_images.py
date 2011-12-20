#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Create a list of pages with a nuber of how many links are directed to them.

import codecs
import re
import md5
import urllib
import os
import sys


class FileListReader():

    def __init__(self, file_name):
        _file = open(file_name, mode='r')
        self.list = []
        line = _file.readline()
        while line:
            self.list.append(line.strip())
            line = _file.readline()


class ImagesDownloader:

    def __init__(self, file_name, pages_selected, base_dir):
        self.base_dir = base_dir
        self.templates_to_counter = {}
        input_links = open('%s.page_images' % file_name, mode='r')
        line = input_links.readline()
        while line:
            words = line.split()
            page = words[0]
            if pages_selected is None or (page in pages_selected):
                print "Processing page %s \r" % page,
                for n in range(1, len(words) - 1):
                    image_url = words[n]
                    self.download_image(image_url)

            line = input_links.readline()
        input_links.close()

    def download_image(self, url):
        sliced_url = url.split('thumb/')
        image_part = sliced_url[1]
        dirs = image_part.split('/')
        destdir = "%s/%s/%s" % (self.base_dir, dirs[0], dirs[1])
        image_name = dirs[len(dirs) - 1]
        try:
            os.makedirs(destdir)
        except:
            pass  # This just means that destdir already exists
        dest = "%s/%s" % (destdir, image_name)
        if not os.path.exists(dest):
            print "Downloading %s" % url
            urllib.urlretrieve(url, dest)

downlad_all = False
print sys.argv
if len(sys.argv) > 1:
    downlad_all = (sys.argv[1] == '--all')
    print "Downloading all images"

input_xml_file_name = './eswiki-20111112-pages-articles.xml'

selected_pages = None
if not downlad_all:
    print "Loading selected pages"
    favorites_reader = FileListReader("favorites.txt")
    selected_pages = favorites_reader.list

print "Downloading images"
templates_counter = ImagesDownloader(input_xml_file_name,
        selected_pages, "./images")
