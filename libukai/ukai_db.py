# Copyright 2014
# IIJ Innovation Institute Inc. All rights reserved.
# 
# Redistribution and use in source and binary forms, with or
# without modification, are permitted provided that the following
# conditions are met:
# 
# * Redistributions of source code must retain the above copyright
#   notice, this list of conditions and the following disclaimer.
# * Redistributions in binary form must reproduce the above
#   copyright notice, this list of conditions and the following
#   disclaimer in the documentation and/or other materials
#   provided with the distribution.
# 
# THIS SOFTWARE IS PROVIDED BY IIJ INNOVATION INSTITUTE INC. ``AS
# IS'' AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND
# FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT
# SHALL IIJ INNOVATION INSTITUTE INC. OR CONTRIBUTORS BE LIABLE
# FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
# PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA,
# OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
# THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR
# TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT
# OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY
# OF SUCH DAMAGE.

import riak

class UKAIDB(object):
    def put_metadata(self, image_name, metadata):
        assert False

    def get_metadata(self, image_name):
        assert False

    def delete_metadata(self, image_name):
        assert False

    def get_image_names(self):
        assert False

UKAI_RIAK_DB_METADATA_BUCKET_NAME = 'metadata'
class UKAIRiakDB(UKAIDB):
    def __init__(self, config):
        self._servers = config.get('metadata_servers')
        self._bucket_name = UKAI_RIAK_DB_METADATA_BUCKET_NAME
        self._config = config

    def put_metadata(self, image_name, metadata):
        client = riak.RiakClient(nodes=self._servers)
        bucket = client.bucket(self._bucket_name)
        riak_data = bucket.new(image_name, data=metadata)
        riak_data.store()
        return 0

    def get_metadata(self, image_name):
        client = riak.RiakClient(nodes=self._servers)
        bucket = client.bucket(self._bucket_name)
        return bucket.get(image_name).data

    def delete_metadata(self, image_name):
        client = riak.RiakClient(nodes=self._servers)
        bucket = client.bucket(self._bucket_name)
        bucket.delete(image_name)
        return 0

    def get_image_names(self):
        client = riak.RiakClient(nodes=self._servers)
        bucket = client.bucket(self._bucket_name)
        return bucket.get_keys()

if __name__ == '__main__':
    from ukai_config import UKAIConfig
    config = UKAIConfig()
    db = UKAIRiakDB(config)
    db.put_metadata('test', 'hoge')
    print db.get_metadata('test')
    print db.get_image_names()
    db.delete_metadata('test')
