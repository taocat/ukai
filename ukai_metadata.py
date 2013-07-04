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

import threading
import sys
import json

from ukai_config import UKAIConfig

UKAI_IN_SYNC = 0
UKAI_SYNCING = 1
UKAI_OUT_OF_SYNC = 2

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
    for block_num in range(0, block_count):
        node_entry = {node: {'sync_status': UKAI_IN_SYNC}}
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
        self._lock = []
        for idx in range(0, len(self.blocks)):
            self._lock.append(threading.Lock())

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
        try:
            self.acquire_lock()

            fh = open(self._metadata_file, 'w')
            json.dump(self._metadata, fh)

        finally:
            fh.close()
            self.release_lock()

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
        An array of all blocks.  Need to acquire lock when modifying
        the contents.
        '''
        return(self._metadata['blocks'])

    def acquire_lock(self, start_idx=0, end_idx=-1):
        if end_idx == -1:
            end_idx = (self.size / self.block_size) - 1
        assert start_idx >= 0
        assert end_idx >= start_idx
        assert end_idx < (self.size / self.block_size)

        for blk_idx in range(0, end_idx + 1):
            self._lock[blk_idx].acquire()

    def release_lock(self, start_idx=0, end_idx=-1):
        if end_idx == -1:
            end_idx = (self.size / self.block_size) - 1
        assert start_idx >= 0
        assert end_idx >= start_idx
        assert end_idx < (self.size / self.block_size)

        for blk_idx in range(0, end_idx + 1):
            self._lock[blk_idx].release()

    def set_sync_status(self, blk_idx, node, sync_status):
        assert (sync_status == UKAI_IN_SYNC
                or sync_status == UKAI_SYNCING
                or sync_status == UKAI_OUT_OF_SYNC)

        self.blocks[blk_idx][node]['sync_status'] = sync_status

    def get_sync_status(self, blk_idx, node):
        return (self.blocks[blk_idx][node]['sync_status'])

    def add_location(self, node, start_idx=0, end_idx=-1,
                     sync_status=UKAI_OUT_OF_SYNC):
        '''
        Adds location information (a node address) to specified range
        of blocks.

        node: the node (currently IPv4 numeric only) to be added.
        start_idx: the first index of the blocks array to add the node.
        end_idx: the end index of the blocks array to add the node.
            When specified -1, the end_block is replaced to the final index
            of the block array.
        sync_status: the initial synchronized status.
        '''
        if end_idx == -1:
            end_idx = (self.size / self.block_size) - 1
        assert start_idx >= 0
        assert end_idx >= start_idx
        assert end_idx < (self.size / self.block_size)

        try:
            self.acquire_lock(start_idx, end_idx)

            for blk_idx in range(start_idx, end_idx + 1):
                if node not in self.blocks[blk_idx]:
                    # if there is no node entry, create it.
                    self.blocks[blk_idx][node] = {}
                    self.set_sync_status(blk_idx, node, sync_status)

        finally:
            self.release_lock(start_idx, end_idx)

        self.flush()

    def remove_location(self, node, start_idx=0, end_idx=-1):
        '''
        Removes location information (a node address) from specified
        range of blocks.

        node: the node (currently IPv4 numeric only) to be removed.
        start_idx: the first index of the blocks array to add the node.
        end_idx: the end index of the blocks array to add the node.
            When specified -1, the end_block is replaced to the final index
            of the block array.
        '''
        if end_idx == -1:
            end_idx = (self.size / self.block_size) - 1
        assert start_idx >= 0
        assert end_idx >= start_idx
        assert end_idx < (self.size / self.block_size)

        try:
            self.acquire_lock(start_idx, end_idx)

            for blk_idx in range(start_idx, end_idx + 1):
                block = self.blocks[blk_idx]
                has_synced_node = False
                for member_node in block.keys():
                    if member_node == node:
                        continue
                    if (self.get_sync_status(blk_idx, member_node)
                        == UKAI_IN_SYNC):
                        has_synced_node = True
                        break
                if has_synced_node is False:
                    print 'block %d does not have synced block' % blk_idx
                    continue
                if node in block.keys():
                    del block[node]

        finally:
            self.release_lock(start_idx, end_idx)

        self.flush()

if __name__ == '__main__':
    UKAIConfig['data_root'] = './test/local/data'
    UKAIConfig['metadata_root'] = './test/local/metadata'
    meta = UKAIMetadata('./test/local/metadata/test')
    print 'metadata:', meta._metadata
    print 'name:', meta.name
    print 'size:', meta.size
    print 'block_size:', meta.block_size
    print 'block[0]:', meta.blocks[0]
    print 'block[3]:', meta.blocks[3]

    for blk_idx in range(0, meta.size / meta.block_size):
        for node in meta.blocks[blk_idx].keys():
            if node == '192.168.100.100':
                meta.set_sync_status(blk_idx, node, UKAI_OUT_OF_SYNC)
    meta.flush()
    for blk_idx in range(0, meta.size / meta.block_size):
        for node in meta.blocks[blk_idx].keys():
            if node == '192.168.100.100':
                meta.set_sync_status(blk_idx, node, UKAI_IN_SYNC)
    meta.flush()

    meta.add_remote('192.168.100.101')
    print meta.blocks

    meta.remove_remote('192.168.100.101')
    print meta.blocks
