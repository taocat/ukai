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
The ukai_metadata.py module defines classes and functions to handle
metadata information of the UKAI system.
'''

import sys
import json

from ukai_config import UKAIConfig

def UKAIMetadataCreate(metadata_file, name, size, block_size, node):
    '''
    Create a metadata file.

    metadata_file: a filename to be generated.
    name: the name of the disk image.
    size: the total size of the disk image.  The size must be multiple
        of the block_size value.
    block_size: the block size of the disk image.
    node: the node address (currently IPv4 numeric address only) of
        initial data store.
    '''

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

class UKAIMetadata(object):
    '''
    The UKAIMetadata class contains metadata information of a disk image
    of the UKAI system.
    '''

    def __init__(self, metadata_file):
        '''
        Initializes the class with the specified file contents.  The
        metadata_file is a JSON format file, which is generated by the
        UKAIMetadataCreate() function or the flush() method of this
        class.

        metadata_file: The path to the file containing metadata
            information.
        '''
        self._metadata_file = metadata_file
        self.reload()

    def reload(self):
        '''
        Reloads the metadata dump file.
        '''
        fh = open(self._metadata_file, 'r')
        self._metadata = json.load(fh)
        fh.close()

    def flush(self):
        '''
        Writes out the latest metadata information stored in memory
        to the metadata file.
        '''
        fh = open(self._metadata_file, 'w')
        json.dump(self._metadata, fh)
        fh.close()

    @property
    def metadata(self):
        '''
        A metadata dictionary object.
        '''
        return(self._metadata)

    @property
    def name(self):
        '''
        The name of the disk image.
        '''
        return (self._metadata['name'])

    @property
    def size(self):
        '''
        The total size of the disk image.
        '''
        return (int(self._metadata['size']))

    @property
    def block_size(self):
        '''
        The block size of the disk image.
        '''
        return (int(self._metadata['block_size']))

    @property
    def blocks(self):
        '''
        An array of all blocks.
        '''
        return(self._metadata['blocks'])

    def add_remote(self, node, start_block=0, end_block=-1, sync_status=False):
        '''
        Adds a node entry to the current blocks.

        node: the node (currently IPv4 numeric only) to be added.
        start_block: the first index of the blocks array to add the node.
        end_block: the end index of the blocks array to add the node.
            When specified -1, the end_block is replaced to the final index
            of the block array.
        sync_status: the initial synchronized status.
        '''
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

    def remove_remote(self, node, start_block=0, end_block=-1):
        '''
        Removes a node entry from the current blocks.

        node: the node (currently IPv4 numeric only) to be removed.
        start_block: the first index of the blocks array to add the node.
        end_block: the end index of the blocks array to add the node.
            When specified -1, the end_block is replaced to the final index
            of the block array.
        '''
        if end_block == -1:
            end_block = self.size / self.block_size
        assert start_block <= end_block

        can_be_removed = True
        for block_num in range(start_block, end_block):
            block = self.blocks[block_num]
            has_synced_node = False
            for member_node in block.keys():
                if member_node == node:
                    continue
                if block[member_node]['synced'] is True:
                    has_synced_node = True
                    break
            if has_synced_node is False:
                print 'block %d does not have synced block' % block_num
                can_be_removed = False
                break
            del block[node]

if __name__ == '__main__':
    UKAIConfig['data_root'] = './test/local/images'
    UKAIConfig['metadata_root'] = './test/local/meta'
    meta = UKAIMetadata('./test/local/meta/test')
    print 'metadata:', meta._metadata
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
    print meta.blocks
