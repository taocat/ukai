![UKAI Logo](ukai_logo.png)

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
	"hypervisors": [
	    "192.0.2.100"
	]
        "blocks": [
            {
                "192.0.2.100": {
                    "sync_status": 0
                }
            },
            {
                "192.0.2.100": {
                    "sync_status": 0
                }
            }
            (continue 158 times)
        ]
    }

The `name` key is a name of the disk image.  The `size` key is the
total size of the disk image.  In the above example, 8GB disk is
defined.  The `block_size` key is the size of a block.  The disk image
will be divided into pieces of files based on the value of the
`block_size` key.  The `hypervisors` key is a list of hypervisors on
which a virtual machine that uses this disk image runs.  If you are
planning migration of a virtual machine, you need to list all the
possible destination hypervisors in this list.  The `blocks` key is a
list of location information of each block.  Each block can have
multiple UKAI remote sotrage endpoint.  The 'sync_status' value shows
the status if the block data of the node is in-sync or out-of-sync.  0
means in-sync, and 2 means out-of-sync.

A metadata file can be created with the utility command provided as
`create_metadata.py` in the `commands` subdirectory of the
distribution.  For example to generate the same metadata as in the
example above, issue the following command.

    $ PYTHONPATH=${UKAIROOT} python create_metadata.py -s 8000000000 -b 50000000 -h 192.0.2.100 -l 192.0.2.100 image01


### Prepare a Disk Image Files

Once you've created the metadata file, put it to the
`UKAIConfig['metadata_root']` path.

You also need to prepare initial disk image files as defined in the
metadata file.  In the above example, you have to prepare 160 files
under the `UKAIConfig['data_root']/image01/` path of the
`192.0.2.100` node.  The filename of each block is defiend by
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
image data files), use the `add_image.py` command.

    $ PYTHONPATH=${UKAIROOT} python add_image.py image01

Once you complete the above process, you will see that your image is
added under the UKAI mount point.

If you are running multiple hypervisors and planning a migration
operation between them, you must insert the disk image on all the
hypervisors.  When any updates happens on metadata information, all
the changes will be disseminated to all the hypervisors listed in the
`hypervisors` key of the metadata file.


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


## Note about Migration

When you want to migrate a virtual machine from one hypervisor to
another hypervisor which is using the UKAI system, you must run
the UKAI system on both hypervisors, and insert the same disk image
on all the hypervisors.


## Utility Commands

To shortcut various UKAI operations, some handy commands are provided
in the `commands` subdirectory.  Most of them need to import UKAI
classes, you need to make sure that UKAI system files are in your
`PYTHONPATH`.

### Create a Metadata File

The `create_metadata.py` command generates a metadata file of a
virtual disk image.  The generated image must be copied to the
metadata directory specified by the `UKAIConfig['metadata_root']`
parameter.  The acutal disk block files must also be prepared before
using the virtual disk.

Once you've copied the metadata file (and completed preparing disk
block files), use the `add_image.py` command to put the disk online.

    Usage: create_metadata.py -s SIZE -b BLOCK_SIZE -n LOCATION IMAGE_NAME


### Add a Disk

The `add_image.py` command adds a virtual disk image defined as a
metadata file to the running UKAI system.

    Usage: add_image.py IMAGE_NAME


### Remove a Disk

The `remove_image.py` command removes a virtual disk image from the
UKAI system.  Do not remove a disk image which is still used by a
virtual machine.

    Usage: remove_image.py IMAGE_NAME


### Get Disk Information

The `get_diskinfo.py` command displays information of a virtual disk.
You can view the metadata information (name, size, block_size, and
location information) of the specified virtual disk.

    Usage: get_diskimage.py IMAGE_NAME


### Add Hypervisor

The `add_hypervisor.py` command adds a new hypervisor address to the
specified virtual disk image.  If you are planning a migration
operation of a virtual machine, then the destination hypervisor must
be added using this command.

    Usage: add_hypervisor.py IMAGE_NAME HYPERVISOR


### Remove Hypervisor

The `remove_hypervisor.py` command removes a hypervisor address from
the specified virtual disk image.  If you no longer migrate a virtual
machine to a certain hypervisor, then you better to remove the address
from the hypervisor list to reduce metadata synchronization overhead.

    Usage: remove_hypervisor.py IMAGE_NAME HYPERVISOR


### Add Location

The `add_location.py` command adds a new location to an existing
virtual disk image.  The initial synchronization status of the new
location is set to out-of-sync.

    Usage: add_location.py IMAGE_NAME LOCATION


### Remove Location

The `remove_location.py` command removes location information from an
existing virtual disk image.  If the location is the only location
that have a in-sync state in a block, then the removal will not
executed.

    Usage: remove_location.py IMAGE_NAME LOCATION


### Error Node List

The `get_error_state.py` command displays the list of nodes which are
not available.  The list does not mean all the other nodes specified
in virtual disk images are available.  Some nodes may also be
unavailable.  When the UKAI system tries to contact them, then they
will also be listed in the list.

    Usage: get_error_state.py

__________________________________________________________
[python]: http://www.python.org/
  "Python Programming Language"
[fuse]: http://fuse.sourceforge.net
  "FUSE: Filesystem in Userspace"
[fusepy]: https://github.com/terencehonles/fusepy
  "A Python module that provides a simple interface to FUSE and MacFUSE"
[netifaces]: http://alastairs-place.net/projects/netifaces/
  "Portable access to network interfaces from Python"
