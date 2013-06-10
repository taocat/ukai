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

class UKAIMetadata:
    def __init__(self, metadata_file):
        self.metadata_file = metadata_file
        self.reload()

    def reload(self):
        fh = open(self.metadata_file, 'r')
        self.metadata = json.load(fh)
        fh.close()

    def flush(self):
        fh = open(self.metadata_file, 'w')
        json.dump(self.metadata, fh)
        fh.close()

    def get_name(self):
        return (self.metadata['name'])
    name = property(get_name)

    def get_size(self):
        return (int(self.metadata['size']))
    size = property(get_size)

    def get_block_size(self):
        return (int(self.metadata['block_size']))
    block_size = property(get_block_size)

    def get_blocks(self):
        return(self.metadata['blocks'])
    blocks = property(get_blocks)

if __name__ == '__main__':
    UKAIConfig['image_root'] = './test/local/images'
    UKAIConfig['meta_root'] = './test/local/meta'
    meta = UKAIMetadata('./test/local/meta/test')
    print 'metadata:', meta.metadata
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
