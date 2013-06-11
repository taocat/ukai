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

'''
The ukai.py module is a top level module of the UKAI implementation.
'''

import sys
import stat
import errno
import os

from fuse import FUSE, FuseOSError, Operations, LoggingMixIn

from ukai_config import UKAIConfig
from ukai_metadata import UKAIMetadata
from ukai_data import UKAIData

class UKAI(LoggingMixIn, Operations):
    '''
    The UKAI class is an implementaion of centrally controllable
    distributed local storage system, built on top of the FUSE
    mechanism.
    '''

    def __init__(self):
        '''
        Initializes metadata dictionary and data dictionary.
        '''

        # read all the metadata stored under the
        # UKAIConfig['meta_root'] path.
        self.meta_db = {}
        for meta_file in os.listdir(UKAIConfig['meta_root']):
            meta_path = '%s/%s' % (UKAIConfig['meta_root'], meta_file)
            self.meta_db[meta_file] = UKAIMetadata(meta_path)

        # initialize UKAIData instances for each metadata instance.
        self.data_db = {}
        for meta_file in self.meta_db.keys():
            self.data_db[meta_file] = UKAIData(self.meta_db[meta_file])

    def chmod(self, path, mode):
        '''
        Sets the file mode (not implemented).
        '''
        print 'XXX chmod not supported'
        return (0)

    def chown(self, path, uid, gid):
        '''
        Sets the file owner (not implemented).
        '''
        print 'XXX chwon not supported'
        return (0)

    def create(self, path, mode):
        '''
        Creates a new file.

        The UKAI filesystem does not support this operation.
        '''
        return (errno.EPERM)

    def getattr(self, path, fh=None):
        '''
        Returns a file stat information.
        '''
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
        '''
        Returns the extended attribute value specified by the name
        argument.

        The UKAI filesystem does not support The extended attribute
        mechanism.
        '''
        # XXX is ENODATA OK? there is no ENOATTR or ENOTSUPP error
        # codes in python.
        raise FuseOSError(errno.ENODATA)

    def listxattr(self, path):
        '''
        Returns all the extended attributed of the specified path.

        The UKAI filesystem does not support the extended attribute
        mechanism.
        '''
        return ([])

    def mkdir(self, path, mode):
        '''
        Creates a new directory.

        The UKAI filesystem does not support this operation.
        '''
        return (errno.EPERM)

    def open(self, path, flags):
        '''
        Opens and returns a filehandle of the open file specified by
        the path parameter.
        '''
        filename = path[1:]
        if filename not in self.data_db.keys():
            raise FuseOSError(errno.ENOENT)
        self.fd += 1
        return self.fd

    def read(self, path, size, offset, fh):
        '''
        Reads the specified length of data from the specified path
        with the specified length and offset, and returns the data.
        '''
        filename = path[1:]
        if filename not in self.data_db.keys():
            raise FuseOSError(errno.ENOENT)
        block = self.data_db[filename]
        return (block.read(size, offset))

    def readdir(self, path, fh):
        '''
        Returns a list of node name entries under the path specified
        by the path argument.
        '''
        return (['.', '..'] + self.meta_db.keys())

    def readlink(self, path):
        '''
        Returns the original file path of the symbolic link file
        specified by the path argument.

        The UKAI filesystem does not support this operation.
        '''
        return (errno.EPERM)

    def removexattr(self, path, name):
        '''
        Removes the extended attribute entry specified by the name
        argument.

        The UKAI filesystem does not support The extended attribute
        mechanism.
        '''
        return (errno.EPERM)

    def rename(self, old, new):
        '''
        Renames a file.

        The UKAI filesystem does not support this operation.
        '''
        return (errno.EPERM)

    def rmdir(self, path):
        '''
        Removes a directory.

        The UKAI filesystem does not support this operation.
        '''
        return (errno.EPERM)

    def setxattr(self, path, name, value, options, position=0):
        '''
        Sets the extended attribute entry specified by the arguments.

        The UKAI filesystem does not support The extended attribute
        mechanism.
        '''
        return (errno.EPERM)

    def statfs(self, path):
        '''
        Returns the file system information.  So far, the returned
        values are meaningless.
        '''
        return dict(f_bsize=512, f_blocks=4096, f_bavail=2048)

    def symlink(self, target, source):
        '''
        Creates a symbolic link file.

        The UKAI filesystem does not support this operation.
        '''
        return (errno.EPERM)

    def truncate(self, path, length, fh=None):
        '''
        Truncates the specified file to the specified length.

        The UKAI filesystem does not support this operation.
        '''
        return (errno.EPERM)

    def unlink(self, path):
        '''
        Removes the specified file.

        The UKAI filesystem does not support this operation.
        '''
        return (errno.EPERM)

    def utimens(self, path, times=None):
        pass

    def write(self, path, data, offset, fh):
        '''
        Writes the specified data to the specified path with the
        specified offset.
        '''
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
