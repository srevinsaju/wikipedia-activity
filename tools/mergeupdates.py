#!/usr/bin/python
#
# Usage:
#   bzcat es_PE.xml.bz2.processed \ 
#     | mergeupdates.py /path/to/wikiedits [ /path/to/blacklist ] \
#     | bzip -c -9 - > new/es_PE.xml.bz2.processed

import sys, re, os, codecs
reload(sys)
sys.setdefaultencoding('utf-8')

START_HEADING = chr(1)
START_TEXT = chr(2)
END_TEXT = chr(3)

def process_article(title, text):
    if title.lower() in blacklist:
        sys.stderr.write('Skipping %s\n' % title)
        return
    if re.match('Wikipedia:', title):
        sys.stderr.write('Skipping %s\n' % title)
        return

    fpath = os.path.join(wikidir, title)
    if os.path.exists(fpath):
        sys.stderr.write('Merging %s\n' % fpath)
        fc = open(fpath).read()
        fc = re.sub('^\n+', '', fc)
        fc = re.sub('\n+$', '', fc)
        text = fc
    sys.stdout.write(START_HEADING + '\n')
    sys.stdout.write(title + '\n')
    sys.stdout.write("%s\n" % len(text))
    sys.stdout.write(START_TEXT + '\n')
    sys.stdout.write(text + '\n')
    sys.stdout.write(END_TEXT + '\n')
    
buf = ''
mode = 'title'
wikidir = os.path.join(sys.argv[1], 'wiki')
if not os.path.exists(wikidir):
    print "Does not exist: " + wikidir
    sys.exit(1)

blacklist = []
if sys.argv > 2:
    blacklist = codecs.open(sys.argv[2], mode='r', encoding='utf8').readlines()
    blacklist = [ i.strip().lower() for i in blacklist]

while True:
    b = sys.stdin.read(1)
    if not b:
        break
    if b == START_HEADING:
        #sys.stderr.write('d start heading\n')
        pass
    elif b == START_TEXT:
        buf = re.sub('^\n+', '', buf)
        title = buf.split('\n')[0]
        bytes = buf.split('\n')[1]
        buf = ''
        #sys.stderr.write('d start text\n')
    elif b == END_TEXT:
        buf = re.sub('^\n+', '', buf)
        buf = re.sub('\n+$', '', buf)
        process_article(title, buf)
        buf = ''
        title = ''
    else:
        buf += b

