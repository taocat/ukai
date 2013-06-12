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

import xmlrpclib
from SimpleXMLRPCServer import SimpleXMLRPCServer
import json

from ukai_config import UKAIConfig
from ukai_metadata import UKAIMetadata
from ukai_data import UKAIData

def UKAIControlWorker(metadata_set, data_set):
    server = SimpleXMLRPCServer(('localhost',
                                 UKAIConfig['control_port']),
                                logRequests=False)
    server.register_instance(UKAIControl(metadata_set, data_set))
    server.serve_forever()

class UKAIControl(object):
    def __init__(self, metadata_set, data_set):
        self._metadata_set = metadata_set
        self._data_set = data_set

    def add_image(self, image_name):
        if image_name in self._metadata_set:
            return (-1)
        metadata_path = '%s/%s' % (UKAIConfig['metadata_root'], image_name)
        metadata = UKAIMetadata(metadata_path)
        self._metadata_set[image_name] = metadata
        self._data_set[image_name] = UKAIData(metadata)
        return (0)

    def remove_image(self, image_name):
        if image_name not in self._metadata_set:
            return (-1)
        del self._metadata_set[image_name]
        del self._data_set[image_name]
        return (0)

    def get_metadata(self, image_name):
        if image_name not in self._metadata_set:
            return ('')
        metadata = self._metadata_set[image_name]
        return(json.dumps(metadata.metadata))
