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
The ukai_proxy.py module provides proxy functions and classes to
krespond read and write operations requested by a primary UKAI node
that runs a virtual machine related to the specific UKAI disk image.
'''

import os
import zlib
import json
import xmlrpclib
from SimpleXMLRPCServer import SimpleXMLRPCServer

from ukai_config import UKAIConfig
from ukai_metadata import UKAIMetadata
from ukai_data import UKAIData

def UKAIProxyWorker(metadata_set, data_set, node_error_state_set):
    server = SimpleXMLRPCServer(('', UKAIConfig['proxy_port']),
                                logRequests=False)
    server.register_instance(UKAIProxy(metadata_set,
                                       data_set,
                                       node_error_state_set))
    server.serve_forever()

class UKAIProxy(object):
    '''
    The UKAIProxy class provides proxy read and write operations.
    '''

    def __init__(self, metadata_set, data_set, node_error_state_set):
        self._metadata_set = metadata_set
        self._data_set = data_set
        self._node_error_state_set = node_error_state_set

    def read(self, name, blk_size, blk_idx, offset, size):
        '''
        Reads data from a local store and returns the data in a XML
        RPC Binary encoded format.

        name: the disk image name.
        blk_size: the block size of the disk image
        blk_idx: the index of the blocks arrray in the disk image.
        offset: the position relateve to the beginning of the specified
            block.
        size: the length to be read from the specified block.
        '''
        path = '%s/%s/' % (UKAIConfig['data_root'],
                           name)
        path = path + UKAIConfig['blockname_format'] % blk_idx
        fh = open(path, 'r')
        fh.seek(offset)
        data = fh.read(size)
        fh.close()
        assert data is not None
        return (xmlrpclib.Binary(zlib.compress(data)))

    def write(self, name, blk_size, blk_idx, offset, bin_data):
        '''
        Writes data to a local store and returns the number of written
        data.

        name: the disk image name.
        blk_size: the block size of the disk image
        blk_idx: the index of the blocks arrray in the disk image.
        offset: the position relateve to the beginning of the specified
            block.
        bin_data: the XML RPC Binary encoded data to be written.
        '''
        data = zlib.decompress(bin_data.data)
        path = '%s/%s/' % (UKAIConfig['data_root'],
                           name)
        path = path + UKAIConfig['blockname_format'] % blk_idx
        if not os.path.exists(path):
            # XXX should not happen.
            # raise an exception
            return (0)
        fh = open(path, 'r+')
        fh.seek(offset)
        fh.write(data)
        fh.close()
        return (len(data))

    def allocate_dataspace(self, name, blk_size, blk_idx):
        '''
        Allocates an empty data block in a local store specified by
        the blk_idx argument.
        '''
        path = '%s/%s/' % (UKAIConfig['data_root'],
                           name)
        if not os.path.exists(path):
            os.makedirs(path)
        path = path + UKAIConfig['blockname_format'] % blk_idx
        fh = open(path, 'w')
        fh.seek(blk_size - 1)
        fh.write('\0')
        fh.close()
        return (0)

    def update_metadata(self, name, bin_metadata):
        json_metadata = zlib.decompress(bin_metadata.data)
        metadata_path = '%s/%s' % (UKAIConfig['metadata_root'],
                                    name)

        fh = open(metadata_path, 'w')
        json.dump(json.loads(json_metadata), fh)
        fh.close()

        if name in self._metadata_set:
            self._metadata_set[name].load_json_metadata(json_metadata)
        else:
            metadata = UKAIMetadata(metadata_path)
            self._metadata_set[name] = metadata
            self._data_set[name] = UKAIData(metadata,
                                            self._node_error_state_set)

        return (0)


if __name__ == '__main__':
    import sys
    if len(sys.argv) == 2 and sys.argv[1] == 'test':
        UKAIConfig['data_root'] = './test/remote/data'
        UKAIConfig['metadata_root'] = './test/remote/metadata'
        print UKAIConfig

    server = SimpleXMLRPCServer(('', UKAIConfig['proxy_port']),
                                logRequests=False)
    server.register_instance(UKAIProxy())
    server.serve_forever()
