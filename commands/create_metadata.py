#!/usr/bin/env python

import sys
import getopt

from ukai_metadata import UKAIMetadataCreate

if len(sys.argv) == 1:
    print 'Usage: %s -s size -b block_size -n location image_name' % sys.argv[0]
    exit (-1)

(optlist, args) = getopt.getopt(sys.argv[1:], 's:b:n:')
for opt_pair in optlist:
    if opt_pair[0] == '-s':
        size = int(opt_pair[1])
    if opt_pair[0] == '-b':
        block_size = int(opt_pair[1])
    if opt_pair[0] == '-n':
        node = opt_pair[1]
assert size > 0
assert block_size > 0
assert size > block_size
block_count = size / block_size
if size % block_size:
    block_count = block_count + 1
name = args[0]

UKAIMetadataCreate(name, name, size, block_size, node)
