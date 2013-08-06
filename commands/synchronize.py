#!/usr/bin/env python

import getopt
import json
import sys
import xmlrpclib

from ukai_config import UKAIConfig

if len(sys.argv) == 1:
    print 'Usage: %s [-s START_BLOCK -e END_BLOCK -v] IMAGE_NAME' % sys.argv[0]
    exit (-1)

start = 0
end = -1
verbose = False
(optlist, args) = getopt.getopt(sys.argv[1:], 's:e:v')
for opt_pair in optlist:
    if opt_pair[0] == '-s':
        start = int(opt_pair[1])
    if opt_pair[0] == '-e':
        end = int(opt_pair[1])
    if opt_pair[0] == '-v':
        verbose = True
image_name = args[0]

c = xmlrpclib.ServerProxy('http://127.0.0.1:%d' % UKAIConfig['control_port'])
metadata = json.loads(c.get_metadata(image_name))
nblocks = metadata['size'] / metadata['block_size']

if (start < 0) or (end > nblocks - 1):
    print 'Block index out of range (must be 0 to %d)' % (nblocks - 1)
    exit (-1)
if (end != -1) and (end < start):
    print 'END_BLOCK must be greater or equal to START_BLOCK'
    exit (-1)

c.synchronize(image_name, start, end, verbose)
