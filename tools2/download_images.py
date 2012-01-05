#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Create a list of pages with a nuber of how many links are directed to them.

import codecs
import re
import md5
from urllib import FancyURLopener
import os
import sys
import shutil
import magic

import config


class FileListReader():

    def __init__(self, file_name):
        _file = open(file_name, mode='r')
        self.list = []
        line = _file.readline()
        while line:
            self.list.append(line.strip())
            line = _file.readline()


class CustomUrlOpener(FancyURLopener):

    version = 'Mozilla/5.0 (X11; Linux x86_64; rv:9.0) Gecko/20100101 ' + \
            'Firefox/9.0'


class ImagesDownloader:

    def __init__(self, file_name, pages_selected, base_dir, cache_dir):
        self.base_dir = base_dir
        self.cache_dir = cache_dir
        self.mime_checker = magic.open(magic.MAGIC_MIME)
        self.mime_checker.load()
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

    def download_image(self, url, dest=None):
        # avoid downloading .ogg files
        if url.lower().endswith('.ogg'):
            return
        overwrite = True
        if dest is None:
            overwrite = False
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
        if not os.path.exists(dest) or overwrite:
            if self.cache_dir is not None and not overwrite:
                # Verify if the file is in the cahce_dir
                cache_file = "%s/%s/%s/%s" % (self.cache_dir, dirs[0], dirs[1],
                        image_name)
                if os.path.exists(cache_file):
                    shutil.copyfile(cache_file, dest)
                    return
            print "Downloading %s" % url
            opener = CustomUrlOpener()
            opener.retrieve(url, dest)
        # Verify the mime type
        # wikipedia return a html file with a error, if the size requested
        # is small than the real image
        # then if the file is a html we need request the unescaled image
        if url.find('/thumb/')> -1:
            mime_type = str(self.mime_checker.file(dest))
            if mime_type.find('text/html') > -1:
                url = url[0:url.rfind('/')]
                url = url.replace('thumb/', '')
                print 'Wrong mime type, redownloading %s to %s' % (url, dest)
                self.download_image(url, dest)


downlad_all = False
cache_dir = None
print sys.argv
if len(sys.argv) > 1:
    for argn in range(1, len(sys.argv)):
        arg = sys.argv[argn]
        if arg == '--all':
            downlad_all = True
            print "Downloading all images"
        if arg.startswith('--cache_dir='):
            cache_dir = arg[arg.find('=') + 1:]
            print "Using cache directory", cache_dir

input_xml_file_name = config.input_xml_file_name

selected_pages = None
if not downlad_all:
    print "Loading selected pages"
    favorites_reader = FileListReader(config.favorites_file_name)
    selected_pages = favorites_reader.list

print "Downloading images"
templates_counter = ImagesDownloader(input_xml_file_name,
        selected_pages, "./images", cache_dir)
