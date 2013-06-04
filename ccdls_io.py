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

from ccdls_config import CCDLSConfig

class CCDLSMeta:
    def __init__(self, meta_file):
        self.meta_file = meta_file
        self.reload()

    def reload(self):
        fh = open(self.meta_file, 'r')
        self.meta_db = json.load(fh)

    def get_name(self):
        return (self.meta_db['name'])
    name = property(get_name)

    def get_size(self):
        return (int(self.meta_db['size']))
    size = property(get_size)

    def get_block_size(self):
        return (int(self.meta_db['block_size']))
    block_size = property(get_block_size)

    def get_block_members_of(self, block_num):
        assert self.meta_db is not None
        blocks = self.meta_db['blocks'][block_num]
        block_members = blocks
        for node in block_members.keys():
            path = '%s/%s/%016d' % (CCDLSConfig['image_root'],
                                    self.name,
                                    block_num)
            block_members[node]['path'] = path
        return (block_members)

class CCDLSBlock:
    def __init__(self, metadata):
        self.meta = metadata

    def gather_pieces(self, offset, size):
        assert size > 0
        assert offset >= 0
        assert size + offset < self.meta.size

        # pieces format: (block #, start position, length)
        start_block = offset / self.meta.block_size
        end_block = (offset + size) / self.meta.block_size
        start_block_pos = offset - (start_block * self.meta.block_size)
        end_block_pos = (offset + size) - (end_block * self.meta.block_size)
        pieces = []
        if start_block == end_block:
            pieces.append((start_block,
                           start_block_pos,
                           size))
        else:
            for block in range(start_block, end_block + 1):
                if block == start_block:
                    pieces.append((block,
                                   start_block_pos,
                                   self.meta.block_size - start_block_pos))
                elif block == end_block:
                    pieces.append((block,
                                   0,
                                   end_block_pos))
                else:
                    pieces.append((block,
                                   0,
                                   self.meta.block_size))
        return (pieces)

    def read(self, size, offset):
        assert size > 0
        assert offset >= 0
        assert (offset + size) < self.meta.size

        data = ''
        pieces = self.gather_pieces(offset, size)
        for piece in pieces:
            block_members = self.meta.get_block_members_of(piece[0])
            candidate = None
            for node in block_members.keys():
                if block_members[node]['synced'] is not True:
                    continue
                if node == '127.0.0.1':
                    candidate = node
                    break
                candidate = node
            data = data + self.get_data(node,
                                        block_members[node]['path'],
                                        piece[1],
                                        piece[2])
        return (data)

    def get_data(self, node, path, offset, size):
        # XXX
        assert node == '127.0.0.1'
        if node == '127.0.0.1':
            fh = open(path, 'r')
            fh.seek(offset)
            data = fh.read(size)
            fh.close()
            assert data is not None
        return (data)

    def write(self, data, offset):
        assert data is not None
        assert offset >= 0
        assert (offset + len(data)) < self.meta.size

        pieces = self.gather_pieces(offset, len(data))
        print pieces
        for piece in pieces:
            block_members = self.meta.get_block_members_of(piece[0])
            data_offset = 0
            for node in block_members.keys():
                if block_members[node]['synced'] is not True:
                    # XXX call a synchronize routine
                    pass
                else:
                    self.put_data(node,
                                  block_members[node]['path'],
                                  piece[1],
                                  data[data_offset:data_offset + piece[2]])
        # XXX ?
        return (len(data))

    def put_data(self, node, path, offset, data):
        if node == '127.0.0.1':
            fh = open(path, 'r+')
            fh.seek(offset)
            fh.write(data)
            fh.close()
        else:
            # XXX remote put handling
            pass

if __name__ == "__main__":
    import random

    if len(sys.argv) != 2:
        print 'usage %s metadata_file' % sys.argv[0]
        sys.exit(1)

    print 'CCDLSMeta'
    meta = CCDLSMeta(sys.argv[1])
    print meta.meta_db
    print meta.name
    print meta.size
    print meta.block_size
    print meta.get_block_members_of(0)
    print meta.get_block_members_of(1)

    print 'CCDLSBlock'
    fh = CCDLSBlock(meta)
    data = 'Hello World!'
    for i in range(0, 100):
        pos = random.randint(0, meta.size - 100)
        fh.write(data, pos)
        print fh.read(len(data), pos)
