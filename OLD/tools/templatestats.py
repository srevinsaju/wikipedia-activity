#!/usr/bin/python 
#
# Trivial script -- check usage frequency of templates
# (Shows templates have a 'long-tail')
# Usage:
#
#  bzcat -d -c es_PE/es_PE.xml.bz2.processed  | ./templatestats.py > templatestats.txt 
#
# Author: Martin Langhoff <martin@laptop.org>
#
import sys, re

rx = re.compile('\{\{.+?\}\}')
seen = {}

while 1:
    line = sys.stdin.readline()
    if not line:
        break
    m = rx.findall(line)
    for p in m:
        # strip away curly braces
        p = p[2:-2]
        p = re.sub('\{+', '', p)
        if p in seen:
            seen[p] = seen[p]+1
        else:
            seen[p] = 1

order = []
for p in seen.keys():
    order.append(tuple([seen[p], p]))

order.sort(cmp=lambda x,y: cmp(y[0], x[0]))

for p in order:
    print "%i : %s" % p 

