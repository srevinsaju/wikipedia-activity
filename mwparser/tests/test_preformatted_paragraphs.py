# -*- coding: utf8 -*-

from . import ParserTestCase


class PreformattedParagraphsTests(ParserTestCase):
    def test_single_line_paragraph(self):
        source = " This is a preformatted paragraph.\n"
        result = """body:
   preformatted_lines:
      preformatted_line:
         preformatted_inline:
            raw_text:This is a preformatted paragraph.
         EOL_KEEP:
"""
        self.parsed_equal_tree(source, result, None)

    def test_preformatted_and_normal_paragraphs(self):
        source = """ This is a preformatted paragraph.
Followed by a "normal" one.
"""
        result = """body:
   preformatted_lines:
      preformatted_line:
         preformatted_inline:
            raw_text:This is a preformatted paragraph.
         EOL_KEEP:

   paragraphs:
      paragraph:
         raw_text:Followed by a "normal" one."""
        self.parsed_equal_tree(source, result, None)

    def test_normal_and_preformatted_paragraphs(self):
        source = """This is a normal paragraph
 Followed by
 a few preformatted
 lines
"""
        result = """body:
   paragraphs:
      paragraph:
         raw_text:This is a normal paragraph
   preformatted_lines:
      preformatted_line:
         preformatted_inline:
            raw_text:Followed by
         EOL_KEEP:

      preformatted_line:
         preformatted_inline:
            raw_text:a few preformatted
         EOL_KEEP:

      preformatted_line:
         preformatted_inline:
            raw_text:lines
         EOL_KEEP:
"""
        self.parsed_equal_tree(source, result, None)

    def test_multiline_paragraph(self):
        source = """ This is a multiline
 preformatted paragraph.
"""
        result = """body:
   preformatted_lines:
      preformatted_line:
         preformatted_inline:
            raw_text:This is a multiline
         EOL_KEEP:

      preformatted_line:
         preformatted_inline:
            raw_text:preformatted paragraph.
         EOL_KEEP:
"""
        self.parsed_equal_tree(source, result, None)

    def test_style_in_preformatted_paragraph(self):
        source = """ Styled text such as ''italic'', '''bold''', {{templates}} also work.
"""
        result = """body:
   preformatted_lines:
      preformatted_line:
         preformatted_inline:
            raw_text:Styled text such as ''italic'', '''bold''', 
            internal_link:
               page_name:Template:templates
            raw_text: also work.
         EOL_KEEP:
"""
        self.parsed_equal_tree(source, result, None)

    def test_tabs_in_preformatted_paragraph(self):
        source = """ Preformatted\tparagraph
 \twith
 \t\tmultiple tabs.
"""
        result = """body:
   preformatted_lines:
      preformatted_line:
         preformatted_inline:
            raw_text:Preformatted
            tab_to_8_spaces: 
            raw_text:paragraph
         EOL_KEEP:

      preformatted_line:
         preformatted_inline:
            tab_to_8_spaces: 
            raw_text:with
         EOL_KEEP:

      preformatted_line:
         preformatted_inline:
            tab_to_8_spaces: 
            tab_to_8_spaces: 
            raw_text:multiple tabs.
         EOL_KEEP:
"""
        self.parsed_equal_tree(source, result, None)

    def test_html_pre_paragraph(self):
        source = """<pre>
Preformatted paragraph.
</pre>
"""
        result = """body:
   preformatted:
Preformatted paragraph.
"""
        self.parsed_equal_tree(source, result, None)

    def test_html_multiline_source_paragraph(self):
        source = """<source>

This is a multiline...


...code paragraph.

</source>
"""
        result = """body:
   preformatted:

This is a multiline...


...code paragraph.

"""

    def test_html_multiline_pre_paragraph(self):
        source = """<pre>

This is a multiline...


...preformatted paragraph.

</pre>
"""
        result = """body:
   preformatted:

This is a multiline...


...preformatted paragraph.

"""
        self.parsed_equal_tree(source, result, None)

    def test_formatted_html_code_paragraph(self):
        # <code> should act similar to <nowiki>
        source = "<source>some [[text]] that should {{not}} be changed</source>\n"
        result = "[source:'some [[text]] that should {{not}} be changed']"
        self.parsed_equal_string(source, result, None)

    def test_formatted_html_pre_paragraph(self):
        # <pre> should act like <nowiki>
        source = "<pre>some [[text]] that should {{not}} be changed</pre>\n"
        result = "[preformatted:'some [[text]] that should {{not}} be changed']"
        self.parsed_equal_string(source, result, None)

    def test_html_pre_in_paragraph(self):
        source = "Normal paragraph <pre>Preformatted one</pre> Normal one.\n"
        result = """body:
   paragraphs:
      paragraph:
         raw_text:Normal paragraph 
   preformatted:Preformatted one
   paragraphs:
      paragraph:
         raw_text:Normal one."""
        self.parsed_equal_tree(source, result, None)

    def test_pre_paragraph_in_table(self):
        source = """{|
|-
! <pre>Text</pre>
|}
"""
        result = """body:
   table:
      table_line_break:
      table_line_header:
         table_cell:
            table_cell_content:
               table_inline:
                  raw_text: 
               table_multiline_content:
                  preformatted:Text"""
        self.parsed_equal_tree(source, result, None)
