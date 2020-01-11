from mediawiki_parser import preprocessor, html, raw
from pijnu.library.pattern import Pattern
import cProfile, pstats

foo = ""

def testit(content):
    global foo
    templates = {}
    allowed_tags = ["PRE"]
    allowed_self_closing_tags = []
    allowed_attributes = []
    interwiki = {}
    namespaces = {}

    preprocess = preprocessor.make_parser(templates)

    parser = html.make_parser(allowed_tags, allowed_self_closing_tags, allowed_attributes, interwiki, namespaces)
    #parser._setTopPattern('wikitext')

    #parser = raw.make_parser()

    preprocessed_text = preprocess.parseTest(content)
    #import pdb; pdb.set_trace()
    #Pattern.TRACE=True
    foo = parser.parseTest(preprocessed_text).leaves()
    #return preprocessed_text.treeView()

if __name__ == "__main__":
    content = open("bigfile.wiki", "r").read()
    cProfile.run('testit(content)', 'results')
    results = pstats.Stats('results')
    results.strip_dirs()
    results.sort_stats('time')
    results.print_stats()
    results.print_callers('pattern.py', .2)

    f = open("bigfile.html", "w+")
    f.truncate()
    f.write( foo )

