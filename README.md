# UKAI: A Centrally Controllable Distributed Local Storage for a Virtual Machine Disk Image Storage

## Copyright Notice

Copyright 2013 IIJ Innovation Institute Inc. All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:

* Redistributions of source code must retain the above copyright
  notice, this list of conditions and the following disclaimer.
* Redistributions in binary form must reproduce the above copyright
  notice, this list of conditions and the following disclaimer in the
  documentation and/or other materials provided with the distribution.

THIS SOFTWARE IS PROVIDED BY IIJ INNOVATION INSTITUTE INC. ``AS IS'' AND
ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
ARE DISCLAIMED. IN NO EVENT SHALL IIJ INNOVATION INSTITUTE INC. OR
CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS;
OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY,
WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR
OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF
ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.


## Introduction

UKAI is an implementation of the concept of 'Centrally Controllable
Distributed Local Storage' as a virtual machine disk image storage.
UKAI provides a filesystem interface to a hypervisor.  A hypervisor
uses the files stored in the UKAI filesystem as a virtual machine disk
image files.  The UKAI filesystem is not a POSIX filesystem.  It only
provides limited (but enough) set of filesystem operations to a
hypervisor for a virtual machine disk image operation.

UKAI is a kind of distributed storage system.  Unlike other major
distributed file/storage systems, the UKAI filesystem is *NOT* an
*AUTONOMOUS* distributed system.  It is a fully manual controlled
distributed filesystem.  You must configure which file should be
stored on which storage node.  In other words, you have full control
on data placement/replacement which is sometimes important when naive
management is required.

For example, assuming that you have geographically distributed
datacenters for virtualization services.  In that case, you may want
to migrate a virtual machie from one hypervisor to a different
hypervisor which is located far place geographically.  The disk image
of the virtual machine must be accessible from any location, but
probably you want some locallity to achieve better disk I/O
performance, or to avoid network access failure to a remote storage.
Using the UKAI filesystem, you can collect your virtual machine disk
image data to UKAI storage nodes located near to the running virtual
machine.


## Installation

UKAI is a Python program built on top of the [FUSE][] mechanism.  The
following software modules are required to run the UKAI filesystem.

* [Python][python]: You know.
* [FUSE][fuse]: Filesystem in Userspace.
* [fusepy][fusepy]: A Python module that provides a simple interface
  to FUSE.
* [netifaces][netifaces]: A portable library to access network
  interfaces from Python.

In some environment (e.g. Ubuntu), you may need to join the 'fuse'
group and may need to configure the '/etc/fuse.conf' file to include
the following line to disclose the filesystem to other users than the
user running the UKAI filesystem.

    user_allow_other


## Configuration

Before running the UKAI filesystem, you need to check the
`ukai_config.py` file and setup appropriate parameters defined in the
file.  The following parameters are configurable.

* `metadata_root`: The path where the metadata information of
  disk images is located.
* `data_root`: The path where virtual machine disk image data is
  stored.
* `blockname_format`: The filename format of each piece of blocks.
* `control_port`: The port number of the contorl interface to get/set
  internal information of the UKAI filesystem.
* `proxy_port`: The port number of the proxy program when receiving
  read/write requests from remote UKAI nodes.


## Prepare a Disk Image

At this moment, there is no handy way to prepare a disk image for the
UKAI filesystem.  You have to prepare all the necessary pieces by hand.

The things you have to do is the following two.

* Prepare a metadata file for a disk image
* Prepare files used as a storage space of the disk image


### Prepare Metadata

The metadata is represented in a JSON format like below.

    {
        "name": "image01",
        "size": 8000000000,
        "block_size": 50000000,
        "blocks": [
            {
                "192.168.0.100": {
                    "synced": true
                }
            },
            {
                "192.168.0.100": {
                    "synced": true
                }
            }
            (continue 158 times)
        ]
    }

The `name` key is a name of the disk image.  The `size` key is the
total size of the disk image.  In the above example, 8GB disk is
defined.  The `block_size` key is the size of a block.  The disk image
will be divided into pieces of files based on the value of the
`block_size` key.  The `blocks` key is a list of location information
of each block.  Each block can have multiple UKAI remote sotrage
endpoint.  The 'synced' flag shows the status if the block data of the
node is up-to-date or not.

### Prepare a Disk Image Files

Once you've created the metadata file, put it to the
`UKAIConfig['metadata_root']` path.

You also need to prepare initial disk image files as defined in the
metadata file.  In the above example, you have to prepare 160 files
under the `UKAIConfig['data_root']/image01/` path of the
`192.168.0.100` node.  The filename of each block is defiend by
`UKAIConfig['blockname_format']`, defaults to `%016d`.  The block file
can have any contents since at the beginning, the contents doesn't
have any meaning.  You may create the files like below.

    for idx in `seq 0 159`
    do
        dd if=/dev/zero of=`printf %016d ${idx}`
    done


## Start the UKAI filesystem

To start the UKAI filesystem, you call the main function of the
`ukai.py` with the path to mount the filesystem.

    $ python ukai.py /ukai

You have to create a mount point (`/ukai` in the above example) before
mounting the UKAI filesystem.

You also need to run the same program under every UKAI remote nodes
defined in metadata files of your disk images.


## Insert a Disk Image

Initially, there is no disk image attached to the UKAI filesystem.  To
add the disk image (which you've prepared with a metadata file and
image data files), follow the instruction below.

    $ python
    >>> import xmlrpclib
    >>> s = xmlrpclib.ServerProxy('http://127.0.0.1:22221')
    >>> s.add_image('image01')
    >>> exit()

The port number of the XML-RPC server is the value defined as the
`UKAIConfig['control_port']` value.  The image name used with the
`add_image` method is the name of the disk image you defined in your
metadata file.

We will prepare friendlier control command in the future.

Once you complete the above process, you will see that your image is
added under the UKAI mount point.


## Using as a Disk Image

The image file can be used directly as a disk image file.  The
following is an example of the libvirt style disk definition.

    <disk type='file' device='disk'>
      <driver name='qemu' type='raw'/>
      <source file='/ukai/image01'/>
      <target dev='vda' bus='virtio'/>
      <alias name='virtio-disk0'/>
      <address type='pci' domain='0x0000' bus='0x00' slot='0x05' function='0x0'/>
    </disk>

__________________________________________________________
[python]: http://www.python.org/
  "Python Programming Language"
[fuse]: http://fuse.sourceforge.net
  "FUSE: Filesystem in Userspace"
[fusepy]: https://github.com/terencehonles/fusepy
  "A Python module that provides a simple interface to FUSE and MacFUSE"
[netifaces]: http://alastairs-place.net/projects/netifaces/
  "Portable access to network interfaces from Python"
