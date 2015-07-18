#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
from ConfigParser import ConfigParser


def read_conf_from_info(path):
    activity_info_path = os.path.join(path, 'activity/activity.info')
    if not os.path.exists(activity_info_path):
        print "FATAL ERROR: no activity.info file available on path '%s'" % \
            activity_info_path
        raise
    activity_info = ConfigParser()
    activity_info.readfp(open(activity_info_path))
    wiki_section = 'Wikipedia'
    confvars = {}
    if activity_info.has_section(wiki_section):
        confvars['comandline'] = False
        confvars['path'] = activity_info.get(wiki_section, 'path')
        confvars['port'] = int(activity_info.get(wiki_section, 'port'))
        confvars['home_page'] = activity_info.get(wiki_section, 'home_page')
        confvars['templateprefix'] = activity_info.get(wiki_section,
                                                       'templateprefix')
        confvars['wpheader'] = activity_info.get(wiki_section, 'wpheader')
        confvars['wpfooter'] = activity_info.get(wiki_section, 'wpfooter')
        confvars['resultstitle'] = activity_info.get(wiki_section,
                                                     'resultstitle')
    else:
        print "FATAL ERROR: activity.info don't have [%s] section" % \
            wiki_section
        raise

    return confvars
