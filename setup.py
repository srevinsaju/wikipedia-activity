#!/usr/bin/env python
#
# Copyright (C) 2011, One Laptop Per Child
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
#
import sys
import os
import shutil
import zipfile
import tarfile
from fnmatch import fnmatch
from sugar3.activity import bundlebuilder

import utils

INCLUDE_DIRS = ['activity', 'binarylibs', 'icons', 'locale', 'bin',
                'mwlib', 'po', 'seek-bzip2', 'static', 'tools2', 'mwparser']
IGNORE_FILES = ['.gitignore', 'MANIFEST', '*.pyc', '*~', '*.bak', 'pseudo.po']


def list_files(base_dir, filter_directories=False, data_file=None):
    if filter_directories:
        include_dirs = INCLUDE_DIRS
    else:
        include_dirs = None

    ignore_files = IGNORE_FILES
    result = []

    base_dir = os.path.abspath(base_dir)

    for root, dirs, files in os.walk(base_dir):

        if ignore_files:
            for pattern in ignore_files:
                files = [f for f in files if not fnmatch(f, pattern)]

        rel_path = root[len(base_dir) + 1:]
        for f in files:
            result.append(os.path.join(rel_path, f))

        if root == base_dir:
            n = 0
            while n < len(dirs):
                directory = dirs[n]
                if include_dirs is not None and directory not in include_dirs:
                    dirs.remove(directory)
                else:
                    n = n + 1

    if data_file is not None:
        # Add the data files
        needed_sufix = ['.processed.bz2', '.processed.bz2t']
        for sufix in needed_sufix:
            file_name = data_file + sufix
            result.append(file_name)

        data_dir = os.path.dirname(data_file)

        # add index
        result.append(os.path.join(data_dir, 'search.db'))

        # add images
        images_path = os.path.join(base_dir, data_dir, 'images')
        if os.path.exists(images_path):
            for file_name in list_files(images_path):
                result.append(os.path.join(data_dir, 'images', file_name))

    return result


class WikiXOPackager(bundlebuilder.XOPackager):

    def __init__(self, builder):
        bundlebuilder.Packager.__init__(self, builder.config)
        self.builder = builder
        self.builder.build_locale()
        self.package_path = os.path.join(self.config.dist_dir,
                                         self.config.xo_name)

    def package(self):
        bundle_zip = zipfile.ZipFile(self.package_path, 'w',
                                     zipfile.ZIP_DEFLATED)

        for f in list_files(self.config.source_dir, True, data_file):
            if os.path.exists(os.path.join(self.config.source_dir, f)):
                bundle_zip.write(os.path.join(self.config.source_dir, f),
                                 os.path.join(self.config.bundle_root_dir, f))
        bundle_zip.close()


class WikiSourcePackager(bundlebuilder.Packager):

    def __init__(self, config):
        bundlebuilder.Packager.__init__(self, config)
        self.package_path = os.path.join(self.config.dist_dir,
                                         self.config.tar_name)

    def package(self):
        tar = tarfile.open(self.package_path, 'w:bz2')
        for f in list_files('./', True, data_file):
            tar.add(os.path.join(self.config.source_dir, f),
                    os.path.join(self.config.tar_root_dir, f))
        tar.close()


valid_data_param = False
if len(sys.argv) >= 3 and not sys.argv[2].startswith('--'):
    valid_data_param = True
    data_file = sys.argv[2]
    if not data_file.endswith(".xml"):
        print("Data file should be a .xml file")
        exit()

    lang = data_file[:data_file.find('/')]

    if not os.path.exists(lang):
        print("Lang directory '%s' does not exist" % lang)
        exit()

    sys.argv.pop()

    # copy activty/activity.info.lang as activty/activity.info
    f = 'activity/activity.info.' + lang
    if os.path.exists(f):
        shutil.copyfile(f, 'activity/activity.info')

if not valid_data_param:
    config = utils.read_conf_from_info('./')
    data_file = config['path']
    lang = data_file[:data_file.find('/')]
    print("data_file parameter not set, taking config from activity.info file")
    print("using %s" % data_file)

print()
print("Lang:", lang)
print()

if lang == 'base':
    print('Without a data file will create a .xo/tar.bz2 file with ' \
        'sources only')
    print()

print('To create a wikipedia activity for a specific language')
print('add a parameter with the xml data file, like:')
print()
print('./setup.py dist_xo fr/frwiki-20111231-pages-articles.xml')
print()

bundlebuilder.XOPackager = WikiXOPackager
bundlebuilder.SourcePackager = WikiSourcePackager

bundlebuilder.start()
