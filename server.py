#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2007, One Laptop Per Child
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
# Web server script for Wikiserver project.
#
# Usage: server.py <dbfile> <port>
#
## Standard libs
from __future__ import with_statement
import sys
import os
import platform
import subprocess
import select
import codecs
from StringIO import StringIO
import BaseHTTPServer
from SimpleHTTPServer import SimpleHTTPRequestHandler
import cgi
import errno
import urllib
import tempfile
import re
import xml.dom.minidom
try:
    from hashlib import md5
except ImportError:
    from md5 import md5

##
## Libs we ship -- add lib path for
## shared objects
##
_root_path = os.path.dirname(__file__)
# linux32_27" for Linux 32bits Python 2.7
system_id = "%s%s" % (platform.system().lower(),
                          platform.architecture()[0][0:2])
if platform.processor().startswith('arm'):
    system_id = platform.processor()

platform_dir = "%s_%s%s" % (system_id,
                          sys.version_info[0], # major
                          sys.version_info[1]) # minor

sys.path.append(os.path.join(_root_path, 'binarylibs', platform_dir))

import wp
from pylru import lrudecorator
import mwlib.htmlwriter
from mwlib import parser, scanner, expander

# Uncomment to print out a large dump from the template expander.
#os.environ['DEBUG_EXPANDER'] = '1'



class MyHTTPServer(BaseHTTPServer.HTTPServer):
    def serve_forever(self, poll_interval=0.5):
        """Overridden version of BaseServer.serve_forever that does not fail
        to work when EINTR is received.
        """
        self._BaseServer__serving = True
        self._BaseServer__is_shut_down.clear()
        while self._BaseServer__serving:
            # XXX: Consider using another file descriptor or
            # connecting to the socket to wake this up instead of
            # polling. Polling reduces our responsiveness to a
            # shutdown request and wastes cpu at all other times.
            try:
                r, w, e = select.select([self], [], [], poll_interval)
            except select.error, e:
                if e[0] == errno.EINTR:
                    print "got eintr"
                    continue
                raise
            if r:
                self._handle_request_noblock()
        self._BaseServer__is_shut_down.set()

class LinkStats:
    allhits = 1
    alltotal = 1
    pagehits = 1
    pagetotal = 1

class ArticleIndex:
    # Prepare an in-memory index, using the already generated 
    # index file.  

    def __init__(self, path):
        self.article_index = set()
        with codecs.open(path, mode='r', encoding='utf-8') as f:
            for line in f.readlines():
                m = re.search(r'(.*?)\s*\d+$', line)
                if m is None:
                    raise AssertionError("Match didn't work")
                self.article_index.add(m.group(1))

    def __contains__(self, x):
        return x in self.article_index

class WPWikiDB:
    """Retrieves article contents for mwlib."""

    def __init__(self, lang, templateprefix, templateblacklist):
        self.lang = lang
        self.templateprefix = templateprefix
        self.templateblacklist = templateblacklist
    
    def getRawArticle(self, title, followRedirects=True):
        # Retrieve article text, recursively following #redirects.
        if title == '':
            return ''

        oldtitle = ""
        while True:
            # Replace underscores with spaces in title.
            title = title.replace("_", " ")
            # Capitalize the first letter of the article -- Trac #6991.
            title = title[0].capitalize() + title[1:]

            if title == oldtitle:
                article_text = ""
                break

            article_text = wp_load_article(title.encode('utf8'))
            if article_text == None:
                # something's wrong
                return None
            article_text = unicode(article_text, 'utf8')
            
            # To see unmodified article_text, uncomment here.
            # print article_text
            if not followRedirects:
                break

            m = re.match(r'^\s*\#?redirect\s*\:?\s*\[\[(.*)\]\]', article_text, re.IGNORECASE|re.MULTILINE)
            if not m: break

            oldtitle = title
            title = m.group(1)

        # Stripping leading & trailing whitespace fixes template expansion.
        article_text = article_text.lstrip()
        article_text = article_text.rstrip()

        return article_text

    def getTemplate(self, title, followRedirects=False):
        return self.getRawArticle(title)

    def expandArticle(self, article_text, title):
        template_expander = expander.Expander(article_text, pagename=title,
                                              wikidb=self, lang=self.lang,
                                              templateprefix = self.templateprefix,
                                              templateblacklist = self.templateblacklist)
        return template_expander.expandTemplates()
        
    def getExpandedArticle(self, title):
        return self.expandArticle(self.getRawArticle(title), title)

class WPImageDB:
    """Retrieves images for mwlib."""
    def __init__(self, basepath):
        self.basepath = basepath

    def hashpath(self, name):
        name = name.replace(' ', '_')
        name = name[:1].upper()+name[1:]
        d = md5(name.encode('utf-8')).hexdigest()
        return "/".join([d[0], d[:2], name])
    
    def getPath(self, name, size=None):
        hashed_name = self.hashpath(name).encode('utf8')
        path = self.basepath + '/%s' % hashed_name
        #print "getPath: %s -> %s" % (name.encode('utf8'), path.encode('utf8'))
        return path

    def getURL(self, name, size=None):
        hashed_name = self.hashpath(name).encode('utf8')
        if os.path.exists(self.basepath + hashed_name):
            url = '/' + self.basepath + hashed_name
        else:
            url = 'http://upload.wikimedia.org/wikipedia/commons/' + hashed_name
        #print "getUrl: %s -> %s" % (name.encode('utf8'), url.encode('utf8'))
        return url

class HTMLOutputBuffer:
    """Buffers output and converts to utf8 as needed."""

    def __init__(self):
        self.buffer = ''

    def write(self, obj):
        if isinstance(obj, unicode):
            self.buffer += obj.encode('utf8')
        else:
            self.buffer += obj
    
    def getvalue(self):
        return self.buffer

class WPMathRenderer:
    def render(self, latex):
        if platform.processor().startswith('arm'):
            process = subprocess.Popen(('bin/arm/blahtex', '--mathml',
                '--texvc-compatible-commands'), stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                env={"LD_LIBRARY_PATH":"bin/arm/"})
        else:
            process = subprocess.Popen(('bin/blahtex', '--mathml',
                '--texvc-compatible-commands'), stdin=subprocess.PIPE,
                stdout=subprocess.PIPE)

        (mathml, err) = process.communicate(latex.encode('utf8'))
        if process.returncode is not 0:
            return ""

        # Ugly!  There is certainly a better way to do this, but my DOM skills are weak, and this works.
        try:
            dom = xml.dom.minidom.parseString(mathml)
            dom = dom.getElementsByTagName('blahtex')[0]
            dom = dom.getElementsByTagName('mathml')[0]
            dom = dom.getElementsByTagName('markup')[0]
            mathml = dom.toxml()
            mathml = mathml.replace('markup', 'math xmlns="http://www.w3.org/1998/Math/MathML" display="inline"')
            dom.unlink()
        except:
            print "BLAHTEX XML PARSING FAILED:\nINPUT: '%s'\nOUTPUT: '%s'" % (latex, mathml)
            return ""

        # Straight embedding.  Requires parent document to be XHTML.
        return mathml
            
class WPHTMLWriter(mwlib.htmlwriter.HTMLWriter):
    """Customizes HTML output from mwlib."""
    
    def __init__(self, index, wfile, images=None, lang='en'):
        self.index = index
        self.gallerylevel = 0
        self.lang = lang

        math_renderer = WPMathRenderer()
        mwlib.htmlwriter.HTMLWriter.__init__(self, wfile, images, math_renderer=math_renderer)

    def writeLink(self, obj):
        if obj.target is None:
            return

        article = obj.target
        
        # Parser appending '/' characters to link targets for some reason.
        article = article.rstrip('/')
        
        title = article
        title = title[0].capitalize() + title[1:]
        title = title.replace("_", " ")

        article_exists = title.encode('utf8') in self.index
        
        if article_exists:
            # Exact match.  Internal link.
            LinkStats.allhits += 1
            LinkStats.alltotal += 1
            LinkStats.pagehits += 1
            LinkStats.pagetotal += 1
            link_attr = ''
            link_baseurl = '/wiki/'
        else:
            # No match.  External link.  Use {lang}.wikipedia.org.
            # FIXME:  Decide between {lang}.w.o and schoolserver.
            LinkStats.alltotal += 1
            LinkStats.pagetotal += 1
            link_attr = "class='offsite' "
            link_baseurl = 'http://' + self.lang + '.wikipedia.org/wiki/'

        parts = article.encode('utf-8').split('#')
        parts[0] = parts[0].replace(" ", "_")
        url = ("#".join([x for x in parts]))

        self.out.write("<a %s href='%s%s'>" % (link_attr, link_baseurl, url))

        if obj.children:
            for x in obj.children:
                self.write(x)
        else:
            self._write(obj.target)
        
        self.out.write("</a>")

    def writeImageLink(self, obj):
        if self.images is None:
            return

        width = obj.width
        height = obj.height

        if width and height:
            path = self.images.getPath(obj.target, size=max(width, height))
            url = self.images.getURL(obj.target, size=max(width, height))
        else:
            path = self.images.getPath(obj.target)
            url = self.images.getURL(obj.target)
            
        if url is None:
            return

        # The following HTML generation code is copied closely from InstaView, which seems to 
        # approximate the nest of <div> tags needed to render images close to right.
        # It's also been extended to support Gallery tags.
        if self.imglevel==0:
            self.imglevel += 1

            align = obj.align
            thumb = obj.thumb
            frame = obj.frame
            caption = obj.caption
            
            # SVG images must be included using <object data=''> rather than <img src=''>.
            if re.match(r'.*\.svg$', url, re.IGNORECASE):
                tag = 'object'
                ref = 'data'
            else:
                tag = 'img'
                ref = 'src'
            
            # Hack to get galleries to look okay, in the absence of image dimensions.
            if self.gallerylevel > 0:
                width = 120
            
            if thumb and not width:
                width = 180 #FIXME: This should not be hardcoded
    
            attr = ''
            if width:
                attr += 'width="%d" ' % width
            
            img = '<%(tag)s %(ref)s="%(url)s" longdesc="%(caption)s" %(attr)s></%(tag)s>' % \
               {'tag':tag, 'ref':ref, 'url':url, 'caption':caption, 'attr':attr}
            
            center = False
            if align == 'center':
                center = True
                align = None

            if center:
                self.out.write('<div class="center">');

            if self.gallerylevel > 0:
                self.out.write('<div class="gallerybox" style="width: 155px;">')
                
                self.out.write('<div class="thumb" style="padding: 13px 0; width: 150px;">')
                self.out.write('<div style="margin-left: auto; margin-right: auto; width: 120px;">')
                self.out.write('<a href="%s" class="image" title="%s">' % (url, caption))
                self.out.write(img)
                self.out.write('</a>')
                self.out.write('</div>')
                self.out.write('</div>')

                self.out.write('<div class="gallerytext">')
                self.out.write('<p>')
                for x in obj.children:
                    self.write(x)
                self.out.write('</p>')
                self.out.write('</div>')

                self.out.write('</div>')
            elif frame or thumb:
                if not align:
                    align = "right"
                self.out.write('<div class="thumb t%s">' % align)

                if not width:
                    width = 180 # default thumb width
                self.out.write('<div style="width:%dpx;">' % (int(width)+2))

                if thumb:
                    self.out.write(img)
                    self.out.write('<div class="thumbcaption">')
                    self.out.write('<div class="magnify" style="float:right">')
                    self.out.write('<a href="%s" class="internal" title="Enlarge">' % url)
                    self.out.write('<img src="/static/magnify-clip.png"></img>')
                    self.out.write('</a>')
                    self.out.write('</div>')
                    for x in obj.children:
                        self.write(x)
                    self.out.write('</div>')
                else:
                    self.out.write(img)
                    self.out.write('<div class="thumbcaption">')
                    for x in obj.children:
                        self.write(x)
                    self.out.write('</div>')

                self.out.write('</div>')
                self.out.write('</div>')
            elif align:
                self.out.write('<div class="float%s">' % align)
                self.out.write(img)
                self.out.write('</div>')
            else:
                self.out.write(img)

            if center:
                self.out.write('</div>');

            self.imglevel -= 1
        else:
            self.out.write('<a href="%s">' % url.encode('utf8'))
            
            for x in obj.children:
                self.write(x)
                
            self.out.write('</a>')

    def writeTagNode(self, t):
        if t.caption == 'gallery':
            self.out.write('<table class="gallery"  cellspacing="0" cellpadding="0">')
            
            self.gallerylevel += 1

            # TODO: More than one row.
            self.out.write('<tr>')
            
            for x in t.children:
                self.out.write('<td>')
                self.write(x)
                self.out.write('</td>')
                
            self.out.write('</tr>')

            self.gallerylevel -= 1
            
            self.out.write('</table>')
        else:
            # All others handled by base class.
            mwlib.htmlwriter.HTMLWriter.writeTagNode(self, t)

class WikiRequestHandler(SimpleHTTPRequestHandler):
    def __init__(self, index, conf, request, client_address, server):
        # pullcord is currently offline
        # self.reporturl = 'pullcord.laptop.org:8000'
        self.reporturl = False
        self.index = index
        self.port  = conf['port']
        self.lang  = conf['lang']
        self.flang = conf['flang']
        self.templateprefix = conf['templateprefix']
        self.templateblacklist = set()
        self.imgbasepath = self.flang + '/images/'
        self.wpheader = conf['wpheader']
        self.wpfooter = conf['wpfooter']
        self.resultstitle = conf['resultstitle']

        if conf.has_key('editdir'):
            self.editdir = conf['editdir']
        else:
            self.editdir = False
        if conf.has_key('giturl'):
            self.giturl = conf['giturl']
        else:
            self.giturl = False

        self.wikidb = WPWikiDB(self.lang, self.templateprefix, self.templateblacklist)
            
        self.client_address = client_address
        SimpleHTTPRequestHandler.__init__(
            self, request, client_address, server)

    def get_wikitext(self, title):
        article_text = self.wikidb.getRawArticle(title)
        if self.editdir:
            edited = self.get_editedarticle(title)
            if edited:
                article_text = edited
            
        # Pass ?override=1 in the url to replace wikitext for testing the renderer.
        if self.params.get('override', 0):
            override = codecs.open('override.txt', 'r', 'utf-8')
            article_text = override.read()
            override.close()

        # Pass ?noexpand=1 in the url to disable template expansion.
        if not self.params.get('noexpand', 0) \
               and not self.params.get('edit', 0):
            article_text = self.wikidb.expandArticle(article_text, title)

        return article_text
    
    def write_wiki_html(self, htmlout, title, article_text):
        tokens = scanner.tokenize(article_text, title)

        wiki_parsed = parser.Parser(tokens, title).parse()
        wiki_parsed.caption = title
      
        imagedb = WPImageDB(self.flang + '/images/')
        writer = WPHTMLWriter(self.index, htmlout, images=imagedb, lang=self.lang)
        writer.write(wiki_parsed)

    def send_article(self, title):
        article_text = self.get_wikitext(title)

        # Capitalize the first letter of the article -- Trac #6991.
        title = title[0].capitalize() + title[1:]

        # Replace underscores with spaces in title.
        title = title.replace("_", " ")

        # Redirect to Wikipedia if the article text is empty (e.g. an image link)
        if article_text == "":
            self.send_response(301)
            self.send_header("Location", 
                             'http://' + self.lang + '.wikipedia.org/wiki/' + title.encode('utf8'))
            self.end_headers()
            return

        # Pass ?raw=1 in the URL to see the raw wikitext (post expansion, unless noexpand=1 is also set).
        if self.params.get('raw', 0):
            self.send_response(200)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.end_headers()
        
            self.wfile.write(article_text.encode('utf8'))
        elif self.params.get('edit', 0):
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()

            self.wfile.write('<html><body><form method="POST">')
            # self.wfile.write('User: <input type="text" size="30" name="user"><br />')
            # self.wfile.write('Comment: <input type="text" size="100" name="comment"><br />')
            self.wfile.write('<input type="submit" value="OK"><br />')
            self.wfile.write('<textarea name="wmcontent" rows="40" cols="80" >')
            htmlout = HTMLOutputBuffer()
            htmlout.write(article_text.encode('utf8'))
            self.wfile.write(htmlout.getvalue())
            self.wfile.write("</textarea></form></body></html>")
        else:
            htmlout = HTMLOutputBuffer()
            
            self.send_response(200)
            self.send_header("Content-Type", "text/xml; charset=utf-8")
            self.end_headers()

            htmlout.write(
                '<?xml version="1.0"?>'\
                '<!DOCTYPE html PUBLIC '\
                '"-//W3C//DTD XHTML 1.1 plus MathML 2.0//EN" '\
                '"http://www.w3.org/TR/MathML2/dtd/xhtml-math11-f.dtd" '\
                '[ <!ENTITY mathml "http://www.w3.org/1998/Math/MathML"> ]> ')
            
            htmlout.write('<html xmlns="http://www.w3.org/1999/xhtml"> ')

            htmlout.write("<head>")
            htmlout.write("<title>%s</title>" % title.encode('utf8'))
        
            htmlout.write("<style type='text/css' media='screen, projection'>"
                             "@import '/static/common.css';"\
                             "@import '/static/monobook.css';"\
                             "@import '/static/styles.css';"\
                             "@import '/static/shared.css';"\
                             "</style>")
            
            htmlout.write("</head>")
            
            htmlout.write("<body>")

            htmlout.write("<h1>")
            htmlout.write(title)
            htmlout.write(' <font size="1">&middot; <a class="offsite" ')
            htmlout.write('href="http://'+self.lang+'.wikipedia.org/wiki/')
            htmlout.write(title)
            htmlout.write('">'+ self.wpheader + '</a> ')

            if self.reporturl:
                # Report rendering problem.
                htmlout.write('&middot; <a class="offsite" ')
                htmlout.write('href="http://%s/render?q=' % self.reporturl)
                htmlout.write(title)
                htmlout.write('">Haz clic aquí si esta página contiene errores de presentación</a> ')

                # Report inappropriate content.
                htmlout.write(' &middot; <a class="offsite" ')
                htmlout.write('href="http://%s/report?q=' % self.reporturl)
                htmlout.write(title)
                htmlout.write('">Esta página contiene material inapropiado</a>')

            if self.editdir:
                htmlout.write(' &middot; <a ')
                htmlout.write('href="http://localhost:%s/wiki/' % self.port)
                htmlout.write(title)
                htmlout.write('?edit=true">[ Editar ]</a>')
                htmlout.write(' &middot; <a ')
                htmlout.write('href="http://localhost:%s/wiki/' % self.port)
                htmlout.write(title)
                htmlout.write('?edit=true">[ Vista OK ]</a>')
            if self.giturl:
                htmlout.write(' &middot; <a ')
                htmlout.write('href="%s' % self.giturl)
                htmlout.write(title)
                htmlout.write('">[ Historial ]</a>')
                
            htmlout.write("</font>")
            htmlout.write('</h1>')
 
            self.write_wiki_html(htmlout, title, article_text)

            htmlout.write('<center>' + self.wpfooter + '</center>')
            htmlout.write("</body>")
            htmlout.write("</html>")

            html = htmlout.getvalue()

            # Fix any non-XHTML tags using tidy.
            if platform.processor().startswith('arm'):
                process = subprocess.Popen(('bin/arm/tidy', '-q', '-config',
                    'bin/tidy.conf', '-numeric', '-utf8', '-asxhtml'),
                    stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                    env={"LD_LIBRARY_PATH":"bin/arm/"})
            else:
                process = subprocess.Popen(('bin/tidy', '-q', '-config',
                    'bin/tidy.conf', '-numeric', '-utf8', '-asxhtml'),
                    stdin=subprocess.PIPE, stdout=subprocess.PIPE)
            (xhtml, err) = process.communicate(html)
            if len(xhtml):
                html = xhtml
            else:
                print "FAILED to tidy '%s'" % title
    
            self.wfile.write(html)

    def do_POST(self):

        real_path = urllib.unquote(self.path)
        real_path = unicode(real_path, 'utf8')

        (real_path, sep, param_text) = real_path.partition('?')

        # Wiki requests return article contents or redirect to Wikipedia.
        m = re.match(r'^/wiki/(.+)$', real_path)
        if self.editdir and m:
            title = m.group(1)

            self._save_page(title)
            
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()

            htmlout = HTMLOutputBuffer()
            htmlout.write(title.encode('utf8'))

            self.wfile.write('<html><body>Editado: ')
            self.wfile.write('<a href="')
            
            self.wfile.write(htmlout.getvalue())
            self.wfile.write('">')
            self.wfile.write(htmlout.getvalue())
            self.wfile.write('</body></html>')
            
            return

        # Any other request redirects to the index page.        
        self.send_response(301)
        self.send_header("Location", "/static/")
        self.end_headers()

    def _save_page(self, title):
        formdata = cgi.FieldStorage(fp=self.rfile,
            headers=self.headers, environ = {'REQUEST_METHOD':'POST'},
            keep_blank_values = 1)

        user      = formdata.getfirst('user')
        comment   = formdata.getfirst('comment')
        wmcontent = formdata.getfirst('wmcontent')

        # fix newlines
        wmcontent = re.sub('\r', '', wmcontent)

        fpath = self.getfpath('wiki', title)
        # UGLY: racy.
        if not os.path.exists(fpath):
            self._saveorig(title)
        (fh, tmpfpath) = tempfile.mkstemp(dir=os.path.dirname(fpath))
        os.write(fh, wmcontent)
        os.close(fh)
        os.rename(tmpfpath, fpath)

        return True

    def getfpath(self, dir, title):
        # may want to hash it
        fpath = os.path.join(self.editdir, dir, title)
        return fpath

    def _saveorig(self, title):
        article_text = self.wikidb.getRawArticle(title)
        fpath = self.getfpath('wiki.orig', title)
        fh = codecs.open(fpath, 'w', encoding='utf-8')
        fh.write(article_text)
        fh.close()

    def get_editedarticle(self, title):
        buf = None
        fpath = self.getfpath('wiki', title)
        if os.path.exists(fpath):
            buf = codecs.open(fpath, 'r', encoding='utf-8').read()
        return buf
    
    def send_searchresult(self, title):
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()

        self.wfile.write("<html><head><title>" 
                         + ( self.resultstitle % title.encode('utf8') )
                         + "</title></head>")

        self.wfile.write("<style type='text/css' media='screen, projection'>"\
                         "@import '/static/monobook.css';</style>")

        self.wfile.write("</head>")

        self.wfile.write("<body>")
        
        self.wfile.write("<h1>" 
                         + ( self.resultstitle % title.encode('utf8') ) 
                         + "</h1>")
        self.wfile.write("<ul>")

        num_results = wp.wp_search(title.encode('utf8'))
        for i in xrange(0, num_results):
            result = unicode(wp.wp_result(i), 'utf8')
            if not result.startswith(self.templateprefix):
                self.wfile.write('<li><a href="/wiki/%s">%s</a></li>' %
                                (result.encode('utf8'), result.encode('utf8')))

        self.wfile.write("</ul>")
            
        self.wfile.write("</body></html>")

    def send_image(self, path):
        if os.path.exists(self.imgbasepath + path.encode('utf8')):
            # If image exists locally, serve it as normal.
            SimpleHTTPRequestHandler.do_GET(self)
        else:
            # If not, redirect to wikimedia.
            redirect_url = "http://upload.wikimedia.org/wikipedia/commons/%s" \
                         % path.encode('utf8')
            self.send_response(301)
            self.send_header("Location", redirect_url.encode('utf8'))
            self.end_headers()

    def handle_feedback(self, feedtype, article):
        with codecs.open("feedback.log", "a", "utf-8") as f:
           f.write(feedtype +"\t"+ article +"\t" + self.client_address[0] +"\n")
           f.close()
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()

        if feedtype == "render":
            strtype = "un error de presentación"
        elif feedtype == "report":
            strtype = "material inapropriado"

        self.wfile.write("<html><title>Comentario recibido</title>Gracias por reportar %s en la pagina <b>%s</b>.</html>" % (strtype, article.encode('utf8')))

    def do_GET(self):
        real_path = urllib.unquote(self.path)
        real_path = unicode(real_path, 'utf8')

        (real_path, sep, param_text) = real_path.partition('?')
        self.params = {}
        for p in param_text.split('&'):
            (key, sep, value) = p.partition('=')
            self.params[key] = value

        # Wiki requests return article contents or redirect to Wikipedia.
        m = re.match(r'^/wiki/(.+)$', real_path)
        if m:
            self.send_article(m.group(1))
            return

        # Search requests return search results.
        m = re.match(r'^/search$', real_path)
        if m:
            self.send_searchresult(self.params.get('q', ''))
            return

        # Image requests are handled locally or are referenced from Wikipedia.
        # matches /es_PE/images/, /en_US/images/ etc
        m = re.match(r'^/\w\w_\w\w/images/(.+)$', real_path)
        if m:
            self.send_image(m.group(1))
            return

        # Static requests handed off to SimpleHTTPServer.
        m = re.match(r'^/(static|generated)/(.*)$', real_path)
        if m:
            SimpleHTTPRequestHandler.do_GET(self)
            return

        # Feedback links.
        m = re.match(r'^/(report|render)$', real_path)
        if m:
            self.handle_feedback(m.group(1), self.params.get('q', ''))
            return

        # Any other request redirects to the index page.        
        self.send_response(301)
        self.send_header("Location", "/static/")
        self.end_headers()

def load_db(dbname):
    if os.environ.has_key('SUGAR_BUNDLE_PATH'):
        dbname = os.path.join(os.environ['SUGAR_BUNDLE_PATH'], dbname)
    wp.wp_load_dump(
        dbname + '.processed',
        dbname + '.locate.db',
        dbname + '.locate.prefixdb',
        dbname + '.blocks.db')

# Cache articles and specially templates
@lrudecorator(100)
def wp_load_article(title):
    
    return wp.wp_load_article(title)

def run_server(confvars):
    index = ArticleIndex('%s.index.txt' % confvars['path'])

    if confvars.has_key('editdir'):
        try:
            for dir in ['wiki', 'wiki.orig']:
                fdirpath = os.path.join(confvars['editdir'], dir)
                if not os.path.exists(fdirpath):
                    os.mkdir(fdirpath)
        except:
            print "Error setting up directories:"
            print "%s must be a writable directory" % confvars['editdir']

    blacklistpath = os.path.join(os.path.dirname(confvars['path']),
                               'template_blacklist')
    blacklist = set()
    if os.path.exists(blacklistpath):
        with open(blacklistpath, 'r') as f:
            for line in f.readlines():
                blacklist.add(line.rstrip().decode('utf8'))
    confvars['templateblacklist'] = blacklist
    confvars['lang'] = os.path.basename(confvars['path'])[0:2]
    confvars['flang'] = os.path.basename(confvars['path'])[0:5]
    ## FIXME GETTEXT
    templateprefixes = { 'en': 'Template:',
                         'es': 'Plantilla:' }
    wpheader = {'en': 'From Wikipedia, The Free Encyclopedia',
                'es': 'De Wikipedia, la enciclopedia libre'}
    wpfooter = {'en': 'Content available under the <a href="/static/es-gfdl.html">GNU Free Documentation License</a>. <br/> Wikipedia is a registered trademark of the non-profit Wikimedia Foundation, Inc.<br/><a href="/static/about_en.html">About Wikipedia</a>',
                'es': 'Contenido disponible bajo los términos de la <a href="/static/es-gfdl.html">Licencia de documentación libre de GNU</a>. <br/> Wikipedia es una marca registrada de la organización sin ánimo de lucro Wikimedia Foundation, Inc.<br/><a href="/static/about_es.html">Acerca de Wikipedia</a>'}
    resultstitle = { 'en': "Search results for '%s'.",
                     'es': "Resultados de la búsqueda sobre '%s'."
        }

    confvars['templateprefix'] = templateprefixes[ confvars['lang'] ]
    confvars['wpheader'] = wpheader[ confvars['lang'] ]
    confvars['wpfooter'] = wpfooter[ confvars['lang'] ]
    confvars['resultstitle'] = resultstitle[confvars['lang']]
    httpd = MyHTTPServer(('', confvars['port']),
        lambda *args: WikiRequestHandler(index, confvars, *args))

    if __name__ == '__main__':
        httpd.serve_forever()
    else:
        from threading import Thread
        server = Thread(target=httpd.serve_forever)
        server.setDaemon(True)
        server.start()
    
    # Tell the world that we're ready to accept request.
    print 'ready'


if __name__ == '__main__':

    conf  = {'path': sys.argv[1],
             'port': int(sys.argv[2])} 
    if len(sys.argv) > 3:
        conf['editdir'] = sys.argv[3]
    if len(sys.argv) > 4:
        conf['giturl'] = sys.argv[4]

    load_db(conf['path'])
    run_server(conf)
