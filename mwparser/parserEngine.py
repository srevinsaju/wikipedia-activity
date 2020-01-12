# -*- coding: utf8 -*-

from __future__ import print_function
import time
import codecs
import os
import sys
from sugar3.activity import activity

try:
    from pijnu import makeParser
except ModuleNotFoundError:
    print("Module pijnu not found. Installing it")
    path_to_pijnu ="{}/bin/any/pijnu-20160727.tar.gz".format(activity.get_bundle_path())
    os.system('pip3 install {} --user'.format(path_to_pijnu))
    try:
        from pijnu import makeParser
    except ModuleNotFoundError:
        print("""Wikipedia Activity couldn't automatically install pijnu.
            Install it manually by 
            pip3 install pijnu --user"
            """)
        sys.exit(1)
from .mediawiki_parser.preprocessor import make_parser as make_parser1
from .mediawiki_parser.text import make_parser as make_parser2
from .mediawiki_parser.html import make_parser as make_parser3

print("*** Parsing to HTML ***")

start_time = time.time()

# get the parser

class ParserCore:
    def __init__(self, i_file):
        self.o_file = ""
        preprocessorGrammar = open(os.path.join(activity.get_bundle_path(), "mwparser", "preprocessor.pijnu")).read()
        makeParser(preprocessorGrammar)

        mediawikiGrammar = open(os.path.join(activity.get_bundle_path(), "mwparser", "mediawiki.pijnu")).read()
        makeParser(mediawikiGrammar)

        allowed_tags = ['p', 'span', 'b', 'i', 'small', 'center', 'ref', 'div', 'references']
        allowed_autoclose_tags = ['br']
        allowed_parameters = ['class', 'style', 'name', 'id', 'scope']
        interwiki = {'ar': 'http://ar.wikipedia.org/wiki/',
                    'az': 'http://az.wikipedia.org/wiki/',
                    'br': 'http://br.wikipedia.org/wiki/',
                    'ca': 'http://ca.wikipedia.org/wiki/',
                    'cs': 'http://cs.wikipedia.org/wiki/',
                    'da': 'http://da.wikipedia.org/wiki/',
                    'de': 'http://de.wikipedia.org/wiki/',
                    'en': 'http://en.wikipedia.org/wiki/',
                    'eo': 'http://eo.wikipedia.org/wiki/',
                    'es': 'http://es.wikipedia.org/wiki/',
                    'fr': 'http://fr.wikipedia.org/wiki/'}

        namespaces = {'Template':   10,
                    u'Catégorie': 14,
                    'Category':   14,
                    'File':        6,
                    'Fichier':     6,
                    'Image':       6}
        templates = {'listen': u"""{| style="text-align:center; background: #f9f9f9; color: #000;font-size:90%; line-height:1.1em; float:right;clear:right; margin:1em 1.5em 1em 1em; width:300px; border: 1px solid #aaa; padding: 0.1em;" cellspacing="7"
        ! class="media audio" style="background-color:#ccf; line-height:3.1em" | Fichier audio
        |-
        |<span style="height:20px; width:100%; padding:4pt; padding-left:0.3em; line-height:2em;" cellspacing="0">'''[[Media:{{{filename|{{{nomfichier|{{{2|}}}}}}}}}|{{{title|{{{titre|{{{1|}}}}}}}}}]]''' ''([[:Fichier:{{{filename|{{{nomfichier|{{{2|}}}}}}}}}|info]])''<br /><small>{{{suitetexte|{{{description|}}}}}}</small>
        <center>[[Fichier:{{{filename|{{{nomfichier|{{{2|}}}}}}}}}|noicon]]</center></span><br /><span style="height:20px; width:100%; padding-left:0.3em;" cellspacing="0"><span title="Des difficultés pour écouter le fichier ?">[[Image:Circle question mark.png|14px|link=Aide:Écouter des sons ogg|Des difficultés  pour  écouter le fichier ?]] ''[[Aide:Écouter des sons ogg|Des problèmes pour écouter le fichier ?]]''</span>
        |}
        """,
            '3e': '3<sup>e</sup>',
            'prettyTable': 'font-size:90%',
            'title': 'test: {{{1}}}',
            'template': '{{{1}}} and {{{parameters}}}...'}

        preprocessor = make_parser1(templates)
        
        parser = make_parser3(allowed_tags, allowed_autoclose_tags, allowed_parameters, interwiki, namespaces)

        # import the source in a utf-8 string
        source = i_file

        # The last line of the file will not be parsed correctly if
        # there is no newline at the end of file, so, we add one.
        if source[-1] != '\n':
            source += '\n'

        preprocessed_text = preprocessor.parse(source)
        tree = parser.parse(preprocessed_text.leaves())

        output = """<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.1//EN" "http://www.w3.org/TR/xhtml11/DTD/xhtml11.dtd">
        <html xmlns="http://www.w3.org/1999/xhtml" xml:lang="fr">
        <head>
            <meta http-equiv="Content-Type" content="text/html; charset=utf-8" />
            <meta name="type" content="text/html; charset=utf-8" />
            <title>Test!</title></head>""" + tree.leaves() + "</html>"

        self.o_file = output

        end_time = time.time()
        print("Parsed and rendered in", end_time - start_time, "s.")
    
    def get(self):
        return self.o_file
