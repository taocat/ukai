#!/usr/bin/env python

import sys
import xmlrpclib
import json

from ukai_config import UKAIConfig

if len(sys.argv) != 2:
    print 'Usage: %s image_name' % sys.argv[0]
    exit (-1)

image_name = sys.argv[1]

c = xmlrpclib.ServerProxy('http://127.0.0.1:%d' % UKAIConfig['control_port'])
metadata = json.loads(c.get_metadata(image_name))

name = metadata['name']
size = metadata['size']
block_size = metadata['block_size']
blocks = metadata['blocks']

print '''#
#  Disk Metadata
#
name=%s
size=%d
block_size=%d''' % (name, size, block_size)

location2index = {}
index2location = []
location_index = 0
for idx in range(0, size / block_size):
    block = blocks[idx]
    for loc in block.keys():
        if loc in location2index:
            continue
        location2index[loc] = location_index
        index2location.append(loc)
        location_index = location_index + 1
print '''#
# Location Index
#'''
for loc_idx in range(0, len(location2index)):
    print '%d=%s' % (loc_idx, index2location[loc_idx])

print '''#
# Block Information
#
# block_index: location_index:sync_status
#   sync_status: 'Y' = In-sync, 'N' = Out-of-sync
#'''
for idx in range(0, size / block_size):
    block = blocks[idx]
    print '%016d:' % idx,
    for loc_idx in range(0, len(index2location)):
        loc = index2location[loc_idx]
        if loc in block.keys():
            print '%d:%s' % (loc_idx,
                             'Y' if block[loc]['sync_status'] == 0 else 'N'),
        else:
            print '   ',
    print ''
        
