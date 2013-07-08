#!/usr/bin/env python

import sys
import getopt

from ukai_metadata import UKAIMetadataCreate

if len(sys.argv) == 1:
    print 'Usage: %s -s SIZE -b BLOCK_SIZE -h HYPERVISOR -l LOCATION IMAGE_NAME' % sys.argv[0]
    exit (-1)

(optlist, args) = getopt.getopt(sys.argv[1:], 's:b:n:h:')
for opt_pair in optlist:
    if opt_pair[0] == '-s':
        size = int(opt_pair[1])
    if opt_pair[0] == '-b':
        block_size = int(opt_pair[1])
    if opt_pair[0] == '-h':
        hypervisor = opt_pair[1]
    if opt_pair[0] == '-l':
        location = opt_pair[1]
assert size > 0
assert block_size > 0
assert size > block_size
block_count = size / block_size
if size % block_size:
    block_count = block_count + 1
name = args[0]

UKAIMetadataCreate(name, name, size, block_size, hypervisor, location)
