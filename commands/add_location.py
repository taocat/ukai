#!/usr/bin/env python

import sys
import xmlrpclib

from ukai_config import UKAIConfig

if len(sys.argv) != 3:
    print 'Usage: %s image_name location' % sys.argv[0]
    exit (-1)

image_name = sys.argv[1]
location = sys.argv[2]

c = xmlrpclib.ServerProxy('http://127.0.0.1:%d' % UKAIConfig['control_port'])
c.add_location(image_name, location)
