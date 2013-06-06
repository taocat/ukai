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
import xmlrpclib

from ukai_config import UKAIConfig

UKAI_PORT=22222

class UKAIMeta:
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
        block = self.meta_db['blocks'][block_num]
        return (block)

class UKAIBlock:
    def __init__(self, metadata):
        self.meta = metadata

    def gather_pieces(self, offset, size):
        assert size > 0
        assert offset >= 0
        assert (size + offset) <= self.meta.size

        # pieces format: (block #, start position, length)
        start_block = offset / self.meta.block_size
        end_block = (offset + size - 1) / self.meta.block_size
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
        assert (offset + size) <= self.meta.size

        data = ''
        pieces = self.gather_pieces(offset, size)
        for piece in pieces:
            blk_num = piece[0]
            off_in_blk = piece[1]
            size_in_blk = piece[2]
            block_members = self.meta.get_block_members_of(blk_num)
            candidate = None
            for node in block_members.keys():
                if block_members[node]['synced'] is not True:
                    continue
                if node == '127.0.0.1':
                    candidate = node
                    break
                candidate = node
            data = data + self.get_data(node,
                                        blk_num,
                                        off_in_blk,
                                        size_in_blk)
        return (data)


    def is_local_node(self, node):
        if (node == 'localhost'
            or node == '127.0.0.1'
            or node == '::1'):
            return (True)
        else:
            return (False)

    def get_data(self, node, num, offset, size):
        if self.is_local_node(node):
            return (self.get_data_local(node, num, offset, size))
        else:
            return (self.get_data_remote(node, num, offset, size))
        

    def get_data_local(self, node, num, offset, size):
        assert size > 0
        assert offset >= 0
        assert (offset + size) <= self.meta.block_size

        path = '%s/%s/' % (UKAIConfig['image_root'],
                           self.meta.name)
        path = path + UKAIConfig['blockname_format'] % num
        fh = open(path, 'r')
        fh.seek(offset)
        data = fh.read(size)
        fh.close()
        assert data is not None
        return (data)

    def get_data_remote(self, node, num, offset, size):
        # XXX
        print 'not implemented yet'

    def write(self, data, offset):
        assert data is not None
        assert offset >= 0
        assert (offset + len(data)) <= self.meta.size

        pieces = self.gather_pieces(offset, len(data))
        data_offset = 0
        for piece in pieces:
            blk_num = piece[0]
            off_in_blk = piece[1]
            size_in_blk = piece[2]
            block_members = self.meta.get_block_members_of(blk_num)
            for node in block_members.keys():
                if block_members[node]['synced'] is not True:
                    # XXX call a synchronize routine
                    pass
                else:
                    self.put_data(node,
                                  blk_num,
                                  off_in_blk,
                                  data[data_offset:data_offset + size_in_blk])
            data_offset = data_offset + size_in_blk

        # XXX what value should we return?
        return (len(data))

    def put_data(self, node, num, offset, data):
        if self.is_local_node(node):
            return (self.put_data_local(node, num, offset, data))
        else:
            return (self.put_data_remote(node, num, offset, data))

    def put_data_local(self, node, num, offset, data):
        path = '%s/%s/' % (UKAIConfig['image_root'],
                           self.meta.name)
        path = path + UKAIConfig['blockname_format'] % num
        fh = open(path, 'r+')
        fh.seek(offset)
        fh.write(data)
        fh.close()
        return (len(data))

    def put_data_remote(self, node, num, offset, data):
        # XXX
        print 'not implemented yet'
        remote = xmlrpclib.ServerProxy('http://%s:%d/' %
                                       (node,
                                        UKAI_PORT))
        remote.write(self.meta.name, self.meta.block_size, num, offset, data)

if __name__ == "__main__":
    import random

    if len(sys.argv) != 2:
        print 'usage %s metadata_file' % sys.argv[0]
        sys.exit(1)

    print 'UKAIMeta'
    meta = UKAIMeta(sys.argv[1])
    print meta.meta_db
    print meta.name
    print meta.size
    print meta.block_size
    print meta.get_block_members_of(0)
    print meta.get_block_members_of(1)

    print 'UKAIBlock'
    fh = UKAIBlock(meta)
    data = 'Hello World!'
    offset = 0
    print 'offset %d' % offset
    fh.write(data, offset)
    ver = fh.read(len(data), offset)
    if ver != data:
        print 'error at offset %d' % offset

    offset = meta.block_size - (len(data) / 2)
    print 'offset %d' % offset
    fh.write(data, offset)
    ver = fh.read(len(data), offset)
    if ver != data:
        print ver
        print 'error at offset %d' % offset
    
    block_count = meta.size / meta.block_size
    if meta.size % meta.block_size:
        block_count = block_count + 1
    offset = (meta.block_size * block_count) - len(data)
    print 'offset %d' % offset
    fh.write(data, offset)
    ver = fh.read(len(data), offset)
    if ver != data:
        print 'error at offset %d' % offset
    
