#!/bin/env python

import os
from setuptools import setup
from distutils.cmd import Command
from distutils.command.build import build as _build

# Utility function to read the README file.
# Used for the long_description.  It's nice, because now 1) we have a top level
# README file and 2) it's easier to type in the README file than to put a raw
# string in below ...
def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

def inputNewer(inputFile, outputFile):
    if not os.path.exists(outputFile):
        return True
    elif os.stat(inputFile).st_mtime - os.stat(outputFile).st_mtime > 1:
        return True
    else:
        return False

def makeparsers(force=False):
    from pijnu import makeParser
    import os
    inputFile = "preprocessor.pijnu"
    outputFile = os.path.join("mediawiki_parser", "preprocessorParser.py")
    if force or inputNewer(inputFile, outputFile):
        preprocessorGrammar = open(inputFile).read()
        makeParser(preprocessorGrammar, outputPath="mediawiki_parser")

    inputFile = "mediawiki.pijnu"
    outputFile = os.path.join("mediawiki_parser", "wikitextParser.py")
    if force or inputNewer(inputFile, outputFile):
        mediawikiGrammar = open(inputFile).read()
        makeParser(mediawikiGrammar, outputPath="mediawiki_parser")

class build_parsers(Command):
    description = "Build the pijnu parsers for mediawiki_parser"
    user_options = [('force', 'f', "Force parser generation")]
    def initialize_options(self):
        self.force = None
    def finalize_options(self):
        pass

    def run(self):
        # honor the --dry-run flag
        if not self.dry_run:
            makeparsers(self.force)

class build(_build):
    sub_commands = [ ('build_parsers', None) ] + _build.sub_commands


if __name__ == '__main__':
    setup(
        name="mediawiki-parser",
        author="Erik Rose, Peter Potrowl",
        author_email="grinch@grinchcentral.com, peter.potrowl@gmail.com",
        url="https://github.com/peter17/mediawiki-parser",
        version="0.4.1",
        license="GPL v3",
        description="A parser for the MediaWiki syntax, based on Pijnu.",
        long_description=read('README.rst'),
        keywords="MediaWiki, parser, syntax",
        packages=["mediawiki_parser"],
        scripts=[],
        data_files=[],
        install_requires=['pijnu>=20160727'],
        cmdclass={'build_parsers': build_parsers, 'build': build},
        classifiers=[
          'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
          'Development Status :: 4 - Beta',
          'Topic :: Software Development',
          'Topic :: Text Processing',
          'Topic :: Software Development :: Libraries :: Python Modules',
          'Intended Audience :: Developers',
          'Programming Language :: Python',
          ]
    )
