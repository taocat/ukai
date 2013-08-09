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
The ukai_control.py module provides a contol interface to UKAI system
operators.
'''

import SocketServer
import xmlrpclib
from SimpleXMLRPCServer import SimpleXMLRPCServer
import json

from ukai_config import UKAIConfig
from ukai_metadata import UKAIMetadata
from ukai_metadata import UKAI_IN_SYNC, UKAI_SYNCING, UKAI_OUT_OF_SYNC
from ukai_data import UKAIData
from ukai_statistics import UKAIStatistics, UKAIImageStatistics

class AsyncSimpleXMLRPCServer(SocketServer.ThreadingMixIn,
                              SimpleXMLRPCServer): pass

def UKAIControlWorker(metadata_set, data_set, node_error_state_set):
    '''
    The UKAIControlWorker function is used as a thread function called
    by the main UKAI thread to serve as a contol message reception
    interface.

    metatada_set: The dictionary object that contains metadata
        instances of the UKAIMetadata class.
    data_set: The dictionaly object that contains disk block
        information instances of the UKAIData class.
    node_error_state_set: The instance of the UKAINodeErrorStateSet
        class.

    Return values: This function does not return.
    '''
    server = AsyncSimpleXMLRPCServer(('localhost',
                                      UKAIConfig['control_port']),
                                     logRequests=False)
    server.register_instance(UKAIControl(metadata_set,
                                         data_set,
                                         node_error_state_set))
    server.serve_forever()

class UKAIControl(object):
    '''
    The UKAIControl class provides a set of interfaces to control
    virtual disk information.
    '''
    def __init__(self, metadata_set, data_set, node_error_state_set):
        '''
        Initializes internal data references.

        metatada_set: The dictionary object that contains metadata
            instances of the UKAIMetadata class.
        data_set: The dictionaly object that contains disk block
            information instances of the UKAIData class.
        node_error_state_set: The instance of the
            UKAINodeErrorStateSet class.

        Return values: This function does not return any values.
        '''
        self._metadata_set = metadata_set
        self._data_set = data_set
        self._node_error_state_set = node_error_state_set

    def add_image(self, image_name):
        '''
        Adds a virtual disk image specified by the image_name
        parameter to the running UKAI system.  The disk image metadata
        and disk image block data must be present before adding it.

        image_name: The name of a virtual disk image to be added.

        Return values: 0 on success, -1 on failure.
        '''
        if image_name in self._metadata_set:
            return (-1)
        metadata_path = '%s/%s' % (UKAIConfig['metadata_root'], image_name)
        metadata = UKAIMetadata(metadata_path)
        self._metadata_set[image_name] = metadata
        self._data_set[image_name] = UKAIData(metadata,
                                              self._node_error_state_set)
        UKAIStatistics[image_name] = UKAIImageStatistics()

        return (0)

    def remove_image(self, image_name):
        '''
        Removes a disk image information specified by the image_name
        parameter from the running UKAI system.  Before removing a
        disk image, an operator must stop the virtual machine that is
        using the target virtual disk.

        image_name: The name of a virtual disk image to be removed.

        Return values: 0 on success, -1 on failure.
        '''
        if image_name not in self._metadata_set:
            return (-1)
        del self._metadata_set[image_name]
        del self._data_set[image_name]
        del UKAIStatistics[image_name]

        return (0)

    def get_metadata(self, image_name):
        '''
        Returns a metadata information in the form of the JSON format.

        image_name: The name of a virtual disk image.

        Return values: A JSON string of the specified virtual disk
        image information on success, '' if there is no disk image
        specified by the parameter.
        '''
        if image_name not in self._metadata_set:
            return ('')
        # XXX need to add a copy interface to the UKAIMetadata class
        # to avoid any thread conflicting.
        metadata = self._metadata_set[image_name]

        return(json.dumps(metadata.metadata))

    def get_node_error_state_set(self):
        '''
        Returns a list of dictionary objects that indicates failure
        status of nodes listed in the failure list.

        Return values: A list object of a dictionary object of
        following format.

            {
                'address': NODE_ADDRESS,
                'reason': FAILURE_REASON,
                'retry_after': RETRY_TIME
            }

        Currently NODE_ADDRESS will be in the IPv4 printable string
        format.  FAILURE_REASON is always 0.  RETRY_TIME indicates
        expiration time of this entry to be removed.  Once the entry
        is removed from the list, the UKAI system will try to contact
        the node again.
        '''
        return(self._node_error_state_set.get_list())

    def add_hypervisor(self, image_name, hypervisor):
        '''
        Adds a new hypervisor address (currently in IPv4 printable
        string format only) to the specified virtual disk image.  If
        you are planning a migration operation of a virtual machine
        using this disk image, you need to add a destination
        hypervisor address before performing a migration operation.

        image_name: The name of a virtual disk image.
        hypervisor: The IP address of a new hypervisor to be added.

        Return values: 0 on success, -1 on failure.
        '''
        if image_name not in self._metadata_set:
            return (-1)

        metadata = self._metadata_set[image_name]
        metadata.add_hypervisor(hypervisor)

        return (0)

    def remove_hypervisor(self, image_name, hypervisor):
        '''
        Removes the specified hypervisor address from the specified
        disk image.  If you no longer use a hypervisor as a migration
        target hyprevisor, you may remove the information from a
        virtual disk image information.  By removing a hypervisor
        entry from the disk image information, the synchronization
        overhead of metadata information will be reduced.

        image_name: The name of a virtual disk image.
        hypervisor: The IP address of a new hypervisor to be removed.

        Return values: 0 on success, -1 on failure.
        '''
        if image_name not in self._metadata_set:
            return (-1)

        metadata = self._metadata_set[image_name]
        metadata.remove_hypervisor(hypervisor)

        return (0)

    def add_location(self, image_name, location, start_idx=0, end_idx=-1,
                     sync_status=UKAI_OUT_OF_SYNC):
        '''
        Adds a new storage location information (currently in the IPv4
        printable string format) to the specified range of disk
        blocks.  If no indexes are specified, the new location
        information will be added to all the disk blocks.  The
        'sync_status' parameter indicates initial synchronization
        status of newly added location information, defaults to
        out-of-sync.  The out-of-sync blocks will be synchronized
        on-demand when they are written some data.  If you are sure
        that the new blocks already exists and syncronized, then you
        can specify them as in-sync (UKAI_IN_SYNC) state.

        image_name: The name of a virtual disk image.
        location: The IP address of a new storage location to be added.
        start_idx: The first block index of disk blocks to which
            the new location information is added.
        end_idx: The last block index of disk blocks to which
            the new location information is added.
        sync_status: Initial synchronization status of the blocks
            which will have the new location information.

        Return values: 0 on success, -1 on failure.
        '''
        if image_name not in self._metadata_set:
            return (-1)

        metadata = self._metadata_set[image_name]
        metadata.add_location(location, start_idx, end_idx, sync_status)

        return (0)

    def remove_location(self, image_name, location, start_idx=0, end_idx=-1):
        '''
        Removes the location information from the specified block
        range of the specified virtual disk image.  If a block has
        only one location information, or location information left
        after this removal don't have any in-sync status, the location
        information is not removed.

        image_name: The name of a virtual disk image.
        location: The IP address of a new storage location to be added.
        start_idx: The first block index of disk blocks to which
            the new location information is added.
        end_idx: The last block index of disk blocks to which
            the new location information is added.
        sync_status: Initial synchronization status of the blocks
            which will have the new location information.

        Return values: 0 on success, -1 on failure.
        '''
        if image_name not in self._metadata_set:
            return (-1)

        metadata = self._metadata_set[image_name]
        metadata.remove_location(location, start_idx, end_idx)

        return (0)

    def synchronize(self, image_name, start_index=0, end_index=-1,
                    verbose=False):
        '''
        Synchronizes the specified block range of the specified
        virtual disk image.  

        image_name: The name of a virtual disk image.
        start_idx: The first block index of disk blocks to which
            the new location information is added.
        end_idx: The last block index of disk blocks to which
            the new location information is added.
        verbose: (XXX just for debug) If set to True, then this
            function prints a progress information on the screen.

        Return values: 0 on success, -1 on failure.
        '''
        if image_name not in self._metadata_set:
            return (-1)
        metadata = self._metadata_set[image_name]
        data = self._data_set[image_name]
        if end_index == -1:
            end_index = (metadata.size / metadata.block_size) - 1
        for blk_idx in range(start_index, end_index + 1):
            if verbose is True:
                print 'syncing block %d (from %d to %d)' % (blk_idx, start_index, end_index)
            if data.synchronize_block(blk_idx) is True:
                metadata.flush()

        return (0)
            
    def get_statistics(self, image_name = ''):
        if image_name == '':
            stats = {}
            for name in UKAIStatistics:
                stats[name] = UKAIStatistics[name].stats
        else:
            stats = UKAIStatistics[image_name].stats

        return (json.dumps(stats))
