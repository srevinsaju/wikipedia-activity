# -*- coding: utf8 -*-

from . import ParserTestCase


class RulesTests(ParserTestCase):
    def test_simple_rule(self):
        source = '----\n'
        result = "[horizontal_rule:'']"
        self.parsed_equal_string(source, result, None)

    def test_rule_too_short(self):
        # In this case, it is a paragraph!
        source = '---\n'
        result = "[paragraphs:[paragraph:[raw_text:'---']]]"
        self.parsed_equal_string(source, result, None)

    def test_rule_too_long(self):
        # In this case, it is a paragraph!
        source = '----\n'
        result = "[horizontal_rule:'']"
        self.parsed_equal_string(source, result, None)

    def test_inline_after_rule(self):
        # In this case, it is a paragraph!
        source = '------ {{template|arg=[[link]]}}\n'
        result = u"[horizontal_rule:[@inline@:[raw_text:' test: '  internal_link:[page_name:'link']]]]"
        templates = {'template': 'test: {{{arg}}}'}
        self.parsed_equal_string(source, result, None, templates)

    def test_html_rule(self):
        # In this case, it is a paragraph!
        source = 'test <hr> test\n'
        result = u"[paragraphs:[paragraph:[raw_text:'test ']]  HR:[<?>:'<hr>']  paragraphs:[paragraph:[raw_text:'test']]]"
        templates = {'template': 'test: {{{arg}}}'}
        self.parsed_equal_string(source, result, None, templates)
