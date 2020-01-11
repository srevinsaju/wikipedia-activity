# -*- coding: utf8 -*-

from . import PostprocessorTestCase


class TextBackendTests(PostprocessorTestCase):
    def test_simple_title(self):
        source = '= A title =\n'
        result = ' A title \n'
        self.parsed_equal_string(source, result, 'wikitext', {}, 'text')

    def test_simple_title2(self):
        source = '== A title ==\n'
        result = ' A title \n'
        self.parsed_equal_string(source, result, 'wikitext', {}, 'text')

    def test_simple_title3(self):
        source = '=== A title ===\n'
        result = ' A title \n'
        self.parsed_equal_string(source, result, 'wikitext', {}, 'text')

    def test_simple_title4(self):
        source = '==== A title ====\n'
        result = ' A title \n'
        self.parsed_equal_string(source, result, 'wikitext', {}, 'text')

    def test_simple_title5(self):
        source = '==== A title ====\n'
        result = ' A title \n'
        self.parsed_equal_string(source, result, 'wikitext', {}, 'text')

    def test_simple_title6(self):
        source = '====== Test! ======\n'
        result = ' Test! \n'
        self.parsed_equal_string(source, result, 'wikitext', {}, 'text')

    def test_simple_title_without_method(self):
        source = '= A title =\n'
        result = ' A title \n'
        self.parsed_equal_string(source, result, None, {}, 'text')

    def test_simple_title2_without_method(self):
        source = '== A title ==\n'
        result = ' A title \n'
        self.parsed_equal_string(source, result, None, {}, 'text')

    def test_simple_title3_without_method(self):
        source = '=== A title ===\n'
        result = ' A title \n'
        self.parsed_equal_string(source, result, None, {}, 'text')

    def test_simple_title4_without_method(self):
        source = '==== A title ====\n'
        result = ' A title \n'
        self.parsed_equal_string(source, result, None, {}, 'text')

    def test_simple_title5_without_method(self):
        source = '==== A title ====\n'
        result = ' A title \n'
        self.parsed_equal_string(source, result, None, {}, 'text')

    def test_simple_title6_without_method(self):
        source = '====== Test! ======\n'
        result = ' Test! \n'
        self.parsed_equal_string(source, result, None, {}, 'text')

    def test_simple_allowed_open_tag(self):
        source = 'a<p>test'
        result = 'a\ntest'
        self.parsed_equal_string(source, result, 'inline', {}, 'text')

    def test_complex_allowed_open_tag(self):
        """ The attributes are ignored. """
        source = 'a<p class="wikitext" style="color:red" onclick="javascript:alert()">test'
        result = 'a\ntest'
        self.parsed_equal_string(source, result, 'inline', {}, 'text')

    def test_simple_disallowed_open_tag(self):
        source = '<a>'
        result = '<a>'
        self.parsed_equal_string(source, result, 'inline', {}, 'text')

    def test_complex_disallowed_open_tag(self):
        source = '<a href="test" class="test" style="color:red" anything="anything">'
        result = '<a href="test" class="test" style="color:red" anything="anything">'
        self.parsed_equal_string(source, result, 'inline', {}, 'text')

    def test_simple_allowed_autoclose_tag(self):
        source = 'a<br />test'
        result = 'a\ntest'
        self.parsed_equal_string(source, result, 'inline', {}, 'text')

    def test_complex_allowed_autoclose_tag(self):
        source = 'one more <br name="test" /> test'
        result = 'one more \n test'
        self.parsed_equal_string(source, result, 'inline', {}, 'text')

    def test_simple_disallowed_autoclose_tag(self):
        source = '<test />'
        result = '<test />'
        self.parsed_equal_string(source, result, 'inline', {}, 'text')

    def test_simple_disallowed_standalone_attribute(self):
        source = 'a <test test> test'
        result = 'a <test test> test'
        self.parsed_equal_string(source, result, 'inline', {}, 'text')

    def test_complex_disallowed_autoclose_tag(self):
        source = '<img src="file.png" />'
        result = '<img src="file.png" />'
        self.parsed_equal_string(source, result, 'inline', {}, 'text')

    def test_italic(self):
        source = "Here, we have ''italic'' text.\n"
        result = "Here, we have _italic_ text.\n"
        self.parsed_equal_string(source, result, None, {}, 'text')

    def test_bold(self):
        source = "Here, we have '''bold''' text.\n"
        result = "Here, we have *bold* text.\n"
        self.parsed_equal_string(source, result, None, {}, 'text')

    def test_bold_and_italic_case1(self):
        source = "Here, we have '''''bold and italic''''' text.\n"
        result = "Here, we have _*bold and italic*_ text.\n"
        self.parsed_equal_string(source, result, None, {}, 'text')

    def test_bold_italic_case2(self):
        source = "Here, we have ''italic only and '''bold and italic''''' text.\n"
        result = "Here, we have _italic only and *bold and italic*_ text.\n"
        self.parsed_equal_string(source, result, None, {}, 'text')

    def test_bold_italic_case3(self):
        source = "Here, we have '''bold only and ''bold and italic''''' text.\n"
        result = "Here, we have *bold only and _bold and italic_* text.\n"
        self.parsed_equal_string(source, result, None, {}, 'text')

    def test_bold_italic_case4(self):
        source = "Here, we have '''''bold and italic''' and italic only''.\n"
        result = "Here, we have _*bold and italic* and italic only_.\n"
        self.parsed_equal_string(source, result, None, {}, 'text')

    def test_bold_italic_case5(self):
        source = "Here, we have '''''bold and italic'' and bold only'''.\n"
        result = "Here, we have *_bold and italic_ and bold only*.\n"
        self.parsed_equal_string(source, result, None, {}, 'text')

    def test_bold_italic_case6(self):
        source = "Here, we have ''italic, '''bold and italic''' and italic only''.\n"
        result = "Here, we have _italic, *bold and italic* and italic only_.\n"
        self.parsed_equal_string(source, result, None, {}, 'text')

    def test_bold_italic_case7(self):
        source = "Here, we have '''bold, ''bold and italic'' and bold only'''.\n"
        result = "Here, we have *bold, _bold and italic_ and bold only*.\n"
        self.parsed_equal_string(source, result, None, {}, 'text')

    def test_bold_italic_case8(self):
        source = """'''Le gras :'''

et l'''italique''...
"""
        result = "*Le gras :*\net l'_italique_...\n"
        self.parsed_equal_string(source, result, None, {}, 'text')

    def test_italic_template(self):
        source = "Here, we have ''italic {{template}}!''.\n"
        result = "Here, we have _italic text!_.\n"
        templates = {'template': 'text'}
        self.parsed_equal_string(source, result, None, templates, 'text')

    def test_styles_in_template(self):
        source = "Here, we have {{template}}.\n"
        result = "Here, we have *text* and _more text_ and _*still more text*_.\n"
        templates = {'template': "'''text''' and ''more text'' and '''''still more text'''''"}
        self.parsed_equal_string(source, result, None, templates, 'text')

    def test_simple_bullet_list(self):
        source = """* item 1
** item 2
*** item 3
** item 2
"""
        result = """
\t*  item 1
\t\t*  item 2
\t\t\t*  item 3

\t\t*  item 2

"""
        self.parsed_equal_string(source, result, 'wikitext', {}, 'text')

    def test_simple_numbered_list(self):
        source = """## item 2
### item 3
## item 2
### item 3
"""
        result = """
\t1. 
\t\t1.  item 2

\t2. 
\t\t1. 
\t\t\t1.  item 3


\t3. 
\t\t1.  item 2

\t4. 
\t\t1. 
\t\t\t1.  item 3


"""
        self.parsed_equal_string(source, result, 'wikitext', {}, 'text')

    def test_simple_semicolon_list(self):
        source = """; item 1
;; item 2
;; item 2
; item 1
; item 1
;;; item 3
"""
        result = """
\t*  item 1
\t\t*  item 2
\t\t*  item 2

\t*  item 1
\t*  item 1
\t\t* 
\t\t\t*  item 3


"""
        self.parsed_equal_string(source, result, 'wikitext', {}, 'text')

    def test_simple_colon_list(self):
        source = """: item 1
::: item 3
:: item 2
: item 1
:: item 2
:: item 2
"""
        result = """
\t*  item 1
\t\t* 
\t\t\t*  item 3

\t\t*  item 2

\t*  item 1
\t\t*  item 2
\t\t*  item 2

"""
        self.parsed_equal_string(source, result, 'wikitext', {}, 'text')

    def test_formatted_mixed_list(self):
        source = """: item 1
; this is ''italic''
* and '''bold''' here
# a [[link]]
: a {{template}}
"""
        result = """
\t*  item 1

\t*  this is _italic_

\t*  and *bold* here

\t1.  a link (link: link)

\t*  a template!
"""
        templates = {'template': 'template!'}
        self.parsed_equal_string(source, result, 'wikitext', templates, 'text')

    def test_complex_mixed_list(self):
        source = """*level 1
*level 1
**level 2
**#level 3
**level 2
:: level 2
; level 1
##level 2
##;level 3
####level 4
#**#level 4
:*;#*: weird syntax
* end
"""
        result = """
\t* level 1
\t* level 1
\t\t* level 2
\t\t\t1. level 3

\t\t* level 2

\t* 
\t\t*  level 2


\t*  level 1
\t* 
\t\t1. level 2

\t* 
\t\t1. 
\t\t\t* level 3


\t* 
\t\t1. 
\t\t\t1. 
\t\t\t\t1. level 4



\t* 
\t\t* 
\t\t\t* 
\t\t\t\t1. level 4



\t* 
\t\t* 
\t\t\t* 
\t\t\t\t1. 
\t\t\t\t\t* 
\t\t\t\t\t\t*  weird syntax






\t*  end
"""
        self.parsed_equal_string(source, result, 'wikitext', {}, 'text')
