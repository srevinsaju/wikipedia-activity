#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys

import server
from utils import read_conf_from_info

conf = read_conf_from_info('./')

conf['comandline'] = True
conf['ip'] = '0.0.0.0'

if len(sys.argv) > 1:
    conf['path'] = sys.argv[1]
if len(sys.argv) > 2:
    conf['port'] = int(sys.argv[2])
if len(sys.argv) > 3:
    conf['editdir'] = sys.argv[3]
if len(sys.argv) > 4:
    conf['giturl'] = sys.argv[4]

server.run_server(conf)