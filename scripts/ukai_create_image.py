#!/usr/bin/env python

import sys
import getopt

from ukai.ukai_config import UKAIConfig
from ukai.ukai_metadata import UKAIMetadataCreate
from ukai.ukai_data import UKAIDataCreate

if len(sys.argv) == 1:
    print 'Usage: %s -s SIZE -b BLOCK_SIZE -h HYPERVISOR -l LOCATION IMAGE_NAME' % sys.argv[0]
    exit (-1)

(optlist, args) = getopt.getopt(sys.argv[1:], 's:b:h:l:')
for opt_pair in optlist:
    if opt_pair[0] == '-s':
        size = int(opt_pair[1])
    if opt_pair[0] == '-b':
        block_size = int(opt_pair[1])
    if opt_pair[0] == '-h':
        hypervisor = opt_pair[1]
    if opt_pair[0] == '-l':
        location = opt_pair[1]
if size <= 0:
    print 'SIZE must be greater than 0.'
    exit (-1)
if block_size <= 0:
    print 'BLOCK_SIZE must be greater than 0.'
    exit (-1)
if size < block_size:
    print 'BLOCK_SIZE must be less or equal to SIZE.'
    exit (-1)
if size % block_size != 0:
    print 'SIZE must be multiple of BLOCK_SIZE.'
    exit (-1)
block_count = size / block_size
name = args[0]

UKAIMetadataCreate(UKAIConfig['metadata_root'], name, size, block_size,
                   hypervisor, location)
UKAIDataCreate(UKAIConfig['data_root'], name, size, block_size, block_count,
               UKAIConfig['blockname_format'])
