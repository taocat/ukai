#!/usr/bin/env python

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

from collections import defaultdict

import sys
import stat
import errno
import os

from fuse import FUSE, FuseOSError, Operations, LoggingMixIn

from ukai_config import UKAIConfig
from ukai_metadata import UKAIMetadata
from ukai_data import UKAIData

class UKAI(LoggingMixIn, Operations):
    """Example memory filesystem. Supports only one level of files."""

    def __init__(self):
        self.files = {}
        self.data = defaultdict(str)
        self.fd = 0

        self.meta_db = {}
        for meta_file in os.listdir(UKAIConfig['meta_root']):
            meta_path = '%s/%s' % (UKAIConfig['meta_root'], meta_file)
            self.meta_db[meta_file] = UKAIMetadata(meta_path)
        self.data_db = {}
        for meta_file in self.meta_db.keys():
            self.data_db[meta_file] = UKAIData(self.meta_db[meta_file])

    def chmod(self, path, mode):
        print 'XXX chmod not supported'
        return (0)

    def chown(self, path, uid, gid):
        print 'XXX chwon not supported'
        return (0)

    def create(self, path, mode):
        return (errno.EPERM)

    def getattr(self, path, fh=None):
        if path == '/':
            st = dict(st_mode=(stat.S_IFDIR | 0755), st_ctime=0,
                      st_mtime=0, st_atime=0, st_nlink=2)
        else:
            filename = path[1:]
            if filename in self.meta_db:
                st = dict(st_mode=(stat.S_IFREG | 0644), st_ctime=0,
                          st_mtime=0, st_atime=0, st_nlink=1,
                          st_size=self.meta_db[filename].size)
            else:
                raise FuseOSError(errno.ENOENT)
        return st

    def getxattr(self, path, name, position=0):
        return ('')

    def listxattr(self, path):
        return ([])

    def mkdir(self, path, mode):
        return (errno.EPERM)

    def open(self, path, flags):
        filename = path[1:]
        if filename not in self.data_db.keys():
            raise FuseOSError(errno.ENOENT)
        self.fd += 1
        return self.fd

    def read(self, path, size, offset, fh):
        filename = path[1:]
        if filename not in self.data_db.keys():
            raise FuseOSError(errno.ENOENT)
        block = self.data_db[filename]
        return (block.read(size, offset))

    def readdir(self, path, fh):
        return (['.', '..'] + self.meta_db.keys())

    def readlink(self, path):
        return (errno.EPERM)

    def removexattr(self, path, name):
        return (errno.EPERM)

    def rename(self, old, new):
        return (errno.EPERM)

    def rmdir(self, path):
        return (errno.EPERM)

    def setxattr(self, path, name, value, options, position=0):
        return (errno.EPERM)

    def statfs(self, path):
        return dict(f_bsize=512, f_blocks=4096, f_bavail=2048)

    def symlink(self, target, source):
        return (errno.EPERM)

    def truncate(self, path, length, fh=None):
        return (errno.EPERM)

    def unlink(self, path):
        return (errno.EPERM)

    def utimens(self, path, times=None):
        pass

    def write(self, path, data, offset, fh):
        filename = path[1:]
        if filename not in self.data_db.keys():
            raise FuseOSError(errno.ENOENT)
        block = self.data_db[filename]
        return (block.write(data, offset))

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print 'usage: %s <mountpoint>' % sys.argv[0]
        sys.exit(1)

    # for linux users: you may have /etc/fuse.conf in some linux
    # distributions.  in that case you need to add the 'user_allow_other'
    # parameter in the conf file to enable the 'allow_other' fuse option.
    fuse = FUSE(UKAI(), sys.argv[1], foreground=True, allow_other=True)
