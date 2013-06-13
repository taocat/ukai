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

import time
import threading

class UKAINodeErrorStateSet(object):
    def __init__(self):
        self._set = {}
        self._lock = threading.Lock()

    def add(self, address, reason):
        try:
            self._lock.acquire()
            self._set[address] = UKAINodeErrorState(address, reason)
        finally:
            self._lock.release()
        
    def is_in_failure(self, address):
        try:
            self._lock.acquire()
            if address not in self._set:
                return (False)
            if self._set[address].is_expired() is True:
                del self._set[address]
                return (False)
            return (True)
        finally:
            self._lock.release()

    def get_list(self):
        try:
            self._lock.acquire()
            copied_set = []
            for address in self._set:
                state = self._set[address]
                copied_set.append({'address': state.address,
                                   'reason': state.reason,
                                   'retry_after': state.retry_after
                                   })
            return (copied_set)
        finally:
            self._lock.release()
        
class UKAINodeErrorState(object):
    def __init__(self, address, reason):
        self._suspend_time = 60
        self._address = address
        self._reason = reason
        self._retry_after = time.time() + self._suspend_time

    @property
    def address(self):
        return (self._address)

    @property
    def reason(self):
        return (self._reason)

    @property
    def retry_after(self):
        return (self._retry_after)

    def is_expired(self):
        return (self._retry_after < time.time())

    def extend(self, reason):
        self._reason = reason
        self._retry_after = time.time() + self._suspend_time
