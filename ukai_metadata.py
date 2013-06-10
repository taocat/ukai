# Copyright 2013 IIJ Innovation Institute Inc. All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#     * Redistributions of source code must retain the above copyright
#       notice, this list of conditions and the following disclaimer.
#     * Redistributions in binary form must reproduce the above copyright
#       notice, this list of conditions and the following disclaimer in the
#       documentation and/or other materials provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY IIJ INNOVATION INSTITUTE INC. ``AS IS'' AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL IIJ INNOVATION INSTITUTE INC. OR
# CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
# EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
# PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS;
# OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY,
# WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR
# OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF
# ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

import sys
import json

from ukai_config import UKAIConfig

def UKAIMetadataCreate(metadata_file, name, size, block_size, node):
    if size % block_size:
        print 'size must be multiple of block_size'
        exit(-1)
    block_count = size / block_size
    metadata_raw = {}
    metadata_raw['name'] = name
    metadata_raw['size'] = size
    metadata_raw['block_size'] = block_size
    metadata_raw['blocks'] = []
    blocks = metadata_raw['blocks']
    print block_count
    for block_num in range(0, block_count):
        node_entry = {node: {'synced': True}}
        blocks.append(node_entry)

    fh = open(metadata_file, 'w')
    json.dump(metadata_raw, fh)
    fh.close()

class UKAIMetadata:
    def __init__(self, metadata_file):
        self.metadata_file = metadata_file
        self.reload()

    def reload(self):
        fh = open(self.metadata_file, 'r')
        self.metadata_raw = json.load(fh)
        fh.close()

    def flush(self):
        fh = open(self.metadata_file, 'w')
        json.dump(self.metadata_raw, fh)
        fh.close()

    def get_name(self):
        return (self.metadata_raw['name'])
    name = property(get_name)

    def get_size(self):
        return (int(self.metadata_raw['size']))
    size = property(get_size)

    def get_block_size(self):
        return (int(self.metadata_raw['block_size']))
    block_size = property(get_block_size)

    def get_blocks(self):
        return(self.metadata_raw['blocks'])
    blocks = property(get_blocks)

    def add_remote(self, node, start_block=0, end_block=-1, sync_status=False):
        if end_block == -1:
            end_block = self.size / self.block_size
        assert start_block <= end_block

        for block_num in range(start_block, end_block):
            block = self.blocks[block_num]
            if node in block:
                # the specified node is already listed in this block.
                continue
            block[node] = {}
            block[node]['synced'] = sync_status

if __name__ == '__main__':
    UKAIConfig['image_root'] = './test/local/images'
    UKAIConfig['meta_root'] = './test/local/meta'
    meta = UKAIMetadata('./test/local/meta/test')
    print 'metadata:', meta.metadata_raw
    print 'name:', meta.name
    print 'size:', meta.size
    print 'block_size:', meta.block_size
    print 'block[0]:', meta.blocks[0]
    print 'block[3]:', meta.blocks[3]

    for block in meta.blocks:
        for node in block.keys():
            if node == '192.168.100.100':
                block[node]['synced'] = False
    meta.flush()
    for block in meta.blocks:
        for node in block.keys():
            if node == '192.168.100.100':
                block[node]['synced'] = True
    meta.flush()

    meta.add_remote('192.168.100.101')
    print meta.blocks

    meta.remove_remote('192.168.100.101')
