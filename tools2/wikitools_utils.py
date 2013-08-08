#!/usr/bin/env python
# -*- coding: utf-8 -*-

def normalize_title(title):
    if len(title) == 0:
        return ''
    s = title.strip().replace(' ', '_')
    if len(s) > 1:
        return s[0].capitalize() + s[1:]
    else:
        return s.capitalize()

