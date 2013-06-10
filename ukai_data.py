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

'''
The ukai_data.py module defines classes and functions to handle image
data of the UKAI system.
'''

import sys
import xmlrpclib
import netifaces

from ukai_metadata import UKAIMetadata
from ukai_config import UKAIConfig

class UKAIData:
    '''
    The UKAIData class provides manipulation functions to modify the
    disk image contents.
    '''

    def __init__(self, metadata):
        '''
        Initializes the instance with the specified metadata object
        created with the UKAIMetadata class.
        '''
        self.metadata = metadata

    def gather_pieces(self, offset, size):
        '''
        Returns a list of tupples specifying which block and index in
        the blocks are related to the offset and size of the disk
        image.  The tupple format is shown below.
          (block_index, start_position, length)

        offset: offset from the beginning of the disk image.
        size: the length of the data to be handled.
        '''
        assert size > 0
        assert offset >= 0
        assert (size + offset) <= self.metadata.size

        # pieces format: (block #, start position, length)
        start_block = offset / self.metadata.block_size
        end_block = (offset + size - 1) / self.metadata.block_size
        start_block_pos = offset - (start_block * self.metadata.block_size)
        end_block_pos = (offset + size) - (end_block * self.metadata.block_size)
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
                                   self.metadata.block_size - start_block_pos))
                elif block == end_block:
                    pieces.append((block,
                                   0,
                                   end_block_pos))
                else:
                    pieces.append((block,
                                   0,
                                   self.metadata.block_size))
        return (pieces)

    def is_local_node(self, node):
        '''
        Checks if node is this machine or not.  This function compares
        the node variable and all the local network interface
        addresses.

        The node variable must be specified as IPv4 numeric address at
        this moment.
        '''
        for interface in netifaces.interfaces():
            ifaddresses = netifaces.ifaddresses(interface)
            for family in ifaddresses.keys():
                for addr in ifaddresses[family]:
                    if node == addr['addr']:
                        return (True)
        return (False)

    def read(self, size, offset):
        '''
        Reads size bytes from the specified location in the disk image
        specified as the offset argument.  The read data is returned
        as a return value.
        '''
        assert size > 0
        assert offset >= 0
        assert (offset + size) <= self.metadata.size

        data = ''
        pieces = self.gather_pieces(offset, size)
        for piece in pieces:
            blk_num = piece[0]
            off_in_blk = piece[1]
            size_in_blk = piece[2]
            block = self.metadata.blocks[blk_num]
            candidate = None
            for node in block.keys():
                if block[node]['synced'] is False:
                    continue
                if self.is_local_node(node):
                    candidate = node
                    break
                candidate = node
            data = data + self.get_data(candidate,
                                        blk_num,
                                        off_in_blk,
                                        size_in_blk)
        return (data)

    def get_data(self, node, num, offset, size):
        '''
        Returns a data read from a local store or a remote store
        depending on the node location.

        node: the target node from which we read the data.
        num: the block index of the disk image.
        offset: the offset relative to the beginning of the specified
            block.
        size: the length of the data to be read.
        '''
        if self.is_local_node(node):
            return (self.get_data_local(node, num, offset, size))
        else:
            return (self.get_data_remote(node, num, offset, size))

    def get_data_local(self, node, num, offset, size):
        '''
        Returns a data read from a local store.

        node: the target node from which we read the data.
        num: the block index of the disk image.
        offset: the offset relative to the beginning of the specified
            block.
        size: the length of the data to be read.
        '''
        assert size > 0
        assert offset >= 0
        assert (offset + size) <= self.metadata.block_size

        path = '%s/%s/' % (UKAIConfig['image_root'],
                           self.metadata.name)
        path = path + UKAIConfig['blockname_format'] % num
        fh = open(path, 'r')
        fh.seek(offset)
        data = fh.read(size)
        fh.close()
        assert data is not None
        return (data)

    def get_data_remote(self, node, num, offset, size):
        '''
        Returns a data read from a remote store.  The remote read
        command is sent to a remote proxy program using the XML RPC
        mechanism.

        node: the target node from which we read the data.
        num: the block index of the disk image.
        offset: the offset relative to the beginning of the specified
            block.
        size: the length of the data to be read.
        '''
        remote = xmlrpclib.ServerProxy('http://%s:%d/' %
                                       (node,
                                        UKAIConfig['proxy_port']))
        return (remote.read(self.metadata.name,
                            self.metadata.block_size,
                            num,
                            offset,
                            size).data)

    def write(self, data, offset):
        '''
        Writes the data from the specified location in the disk image
        specified as the offset argument.  The method returns the
        number of written data.
        '''
        assert data is not None
        assert offset >= 0
        assert (offset + len(data)) <= self.metadata.size

        pieces = self.gather_pieces(offset, len(data))
        data_offset = 0
        for piece in pieces:
            blk_num = piece[0]
            off_in_blk = piece[1]
            size_in_blk = piece[2]
            block = self.metadata.blocks[blk_num]
            for node in block.keys():
                if block[node]['synced'] is False:
                    self.synchronize_block(blk_num)
                self.put_data(node,
                              blk_num,
                              off_in_blk,
                              data[data_offset:data_offset + size_in_blk])
            data_offset = data_offset + size_in_blk

        return (len(data))

    def put_data(self, node, num, offset, data):
        '''
        Writes the data to a local store or a remote store depending
        on the node location.

        node: the target node from which we read the data.
        num: the block index of the disk image.
        offset: the offset relative to the beginning of the specified
            block.
        data: the data to be written.
        '''
        if self.is_local_node(node):
            return (self.put_data_local(node, num, offset, data))
        else:
            return (self.put_data_remote(node, num, offset, data))

    def put_data_local(self, node, num, offset, data):
        '''
        Writes the data to a local store.

        node: the target node from which we read the data.
        num: the block index of the disk image.
        offset: the offset relative to the beginning of the specified
            block.
        data: the data to be written.
        '''
        path = '%s/%s/' % (UKAIConfig['image_root'],
                           self.metadata.name)
        path = path + UKAIConfig['blockname_format'] % num
        fh = open(path, 'r+')
        fh.seek(offset)
        fh.write(data)
        fh.close()
        return (len(data))

    def put_data_remote(self, node, num, offset, data):
        '''
        Writes the data to a remote store.  The remote write command
        is sent to a remote proxy program using the XML RPC mechanism.

        node: the target node from which we read the data.
        num: the block index of the disk image.
        offset: the offset relative to the beginning of the specified
            block.
        data: the data to be written.
        '''
        remote = xmlrpclib.ServerProxy('http://%s:%d/' %
                                       (node,
                                        UKAIConfig['proxy_port']))
        return (remote.write(self.metadata.name, self.metadata.block_size,
                             num, offset, xmlrpclib.Binary(data)))

    def synchronize_block(self, block_num):
        '''
        Synchronizes the specified block by the block_num argument.
        This function first search the already synchronized node block
        and copy the data to all the other not-synchronized nodes.
        '''
        block = self.metadata.blocks[block_num]
        source_candidate = None
        for node in block.keys():
            if block[node]['synced'] is False:
                continue
            if self.is_local_node(node):
                source_candidate = node
                break
            source_candidate = node
        if source_candidate == None:
            # XXX fatal
            # should raise an exception
            print 'Disk broken'
        for node in block.keys():
            if block[node]['synced'] == True:
                continue
            if node == source_candidate:
                continue
            self.allocate_dataspace(node, block_num)
            self.put_data(node,
                          block_num,
                          0,
                          self.get_data(source_candidate,
                                        block_num,
                                        0,
                                        self.metadata.block_size))
            block[node]['synced'] = True
        self.metadata.flush()

    def allocate_dataspace(self, node, block_num):
        '''
        Allocates an empty data block in a local store specified by
        the block_num argument.
        '''
        if self.is_local_node(node):
            path = '%s/%s/' % (UKAIConfig['image_root'],
                           self.metadata.name)
            path = path + UKAIConfig['blockname_format'] % block_num
            fh = open(path, 'w')
            fh.seek(self.metadata.block_size - 1)
            fh.write('\0')
            fh.close()
        else:
            remote = xmlrpclib.ServerProxy('http://%s:%d/' %
                                           (node,
                                            UKAIConfig['proxy_port']))
            remote.allocate_dataspace(self.metadata.name,
                                      self.metadata.block_size,
                                      block_num)

if __name__ == '__main__':
    UKAIConfig['image_root'] = './test/local/images'
    UKAIConfig['meta_root'] = './test/local/meta'

    meta = UKAIMetadata('./test/local/meta/test')
    fh = UKAIData(meta)
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
    
    for block_num in range(0, meta.size / meta.block_size):
        print 'sync block_num %d' % block_num
        remote = xmlrpclib.ServerProxy('http://127.0.0.1:%d/' %
                                       UKAIConfig['proxy_port'])
        remote.allocate_dataspace(meta.name,
                                  meta.block_size,
                                  block_num)
        remote.write(meta.name, meta.block_size,
                     block_num, 0,
                     xmlrpclib.Binary(fh.get_data_local('dummy',
                                                        block_num,
                                                        0,
                                                        meta.block_size)))
