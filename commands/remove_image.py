#!/usr/bin/env python

import sys
import xmlrpclib

from ukai_config import UKAIConfig

if len(sys.argv) != 2:
    print 'Usage: %s IMAGE_NAME' % sys.argv[0]
    exit (-1)

image_name = sys.argv[1]

c = xmlrpclib.ServerProxy('http://127.0.0.1:%d' % UKAIConfig['control_port'])
c.remove_image(image_name)

