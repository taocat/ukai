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

import os
import xmlrpclib
from SimpleXMLRPCServer import SimpleXMLRPCServer

from ukai_config import UKAIConfig

class UKAIProxy:
    def read(self, name, blk_size, blk_num, offset, size):
        path = '%s/%s/' % (UKAIConfig['image_root'],
                           name)
        path = path + UKAIConfig['blockname_format'] % blk_num
        fh = open(path, 'r')
        fh.seek(offset)
        data = fh.read(size)
        fh.close()
        assert data is not None
        return (xmlrpclib.Binary(data))

    def write(self, name, blk_size, blk_num, offset, bin_data):
        data = bin_data.data
        path = '%s/%s/' % (UKAIConfig['image_root'],
                           name)
        if not os.path.exists(path):
            os.makedirs(path)
        path = path + UKAIConfig['blockname_format'] % blk_num
        fh = 0
        if not os.path.exists(path):
            fh = open(path, 'w')
            fh.seek(blk_size - 1)
            fh.write('0')
        else:
            fh = open(path, 'r+')
        fh.seek(offset)
        fh.write(data)
        fh.close()
        return (len(data))

if __name__ == '__main__':
    import sys
    if sys.argv[1] == 'test':
        UKAIConfig['image_root'] = './test/images'
        UKAIConfig['meta_root'] = './test/meta'
        print UKAIConfig

    server = SimpleXMLRPCServer(('', UKAIConfig['proxy_port']),
                                logRequests=False)
    server.register_introspection_functions()
    server.register_instance(UKAIProxy())
    server.serve_forever()
