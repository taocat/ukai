# Copyright 2013
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

import os
import shutil

def ukai_local_read(image_name, block_size, block_index, offset, size, config):
    image_path = '%s/%s/' % (config.get('data_root'), image_name)
    block_path = image_path + config.get('blockname_format') % block_index
    if not os.path.exists(block_path):
        # the data block file is not allcated yet.
        return '\0' * size
    if os.path.getsize(block_path) != block_size:
        # a block file exists but the size doesn't match.  maybe
        # garbage.
        ukai_local_deallocate_dataspace(image_name, block_index, config)
        return '\0' * size

    fh = open(block_path, 'r')
    fh.seek(offset)
    data = fh.read(size)
    fh.close()
    assert data is not None

    return data

def ukai_local_write(image_name, block_size, block_index,
                     offset, data, config):
    image_path = '%s/%s/' % (config.get('data_root'), image_name)
    block_path = image_path + config.get('blockname_format') % block_index
    if ((not os.path.exists(block_path))
        or (os.path.getsize(block_path) != block_size)):
        # the data block file is not allcated yet.
        ukai_local_allocate_dataspace(image_name, block_size, block_index,
                                      config)
    fh = open(block_path, 'r+')
    fh.seek(offset)
    fh.write(data)
    fh.close()

    return len(data)

def ukai_local_allocate_dataspace(image_name, block_size, block_index, config):
    image_path = '%s/%s/' % (config.get('data_root'), image_name)
    if not os.path.exists(image_path):
        os.makedirs(image_path)
    block_path = image_path + config.get('blockname_format') % block_index
    fh = open(block_path, 'w')
    fh.seek(block_size - 1)
    fh.write('\0')
    fh.close()

    return 0

def ukai_local_deallocate_dataspace(image_name, block_index, config):
    image_path = '%s/%s/' % (config.get('data_root'), image_name)
    block_path = image_path + config.get('blockname_format') % block_index
    if not os.path.exists(block_path):
        return 0
    os.unlink(block_path)

    return 0

def ukai_local_destroy_image(image_name, config):
    image_path = '%s/%s/' % (config.get('data_root'), image_name)
    if not os.path.exists(image_path):
        return 0
    shutil.rmtree(image_path)

    return 0
    
