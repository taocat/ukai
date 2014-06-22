# Copyright 2013, 2014
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

'''
The ukai_config.py module defines the global parameters of the
UKAI system.

metadata_servers: the location of the backend metadata servers
data_root: the location of the backend image storage space
blockname_format: the filename format of each block data file
core_server: the IP address of the UKAICore service
core_port: the port number of the UKAICore service
'''

import json
import re

UKAI_CONFIG_FILE_DEFAULT = '/etc/ukai/config'

comment_re = re.compile('^\s*#.*$', re.MULTILINE)

class UKAIConfig(object):
    ''' The UKAIConfig class provides interfaces to keep/get/set
    general configuration parameters.
    '''
    def __init__(self, config_file=UKAI_CONFIG_FILE_DEFAULT):
        ''' Initializes the UKAIConfig class.

        param config_file: a path name of a configuration file
        '''
        config_content = ''
        with open(config_file) as fp:
            config_content = ''.join(fp.readlines())
            match = comment_re.search(config_content)
            while match:
                config_content = (config_content[:match.start()]
                                  + config_content[match.end():])
                match = comment_re.search(config_content)
                
        self._config = json.loads(config_content)

    def get(self, key):
        ''' Returns a configuration value.  If the specified key
        doesn't exist in the UKAIConfig instance, None is returned.

        param key: a key to be retrieved
        '''
        if key in self._config:
            return (self._config[key])
        else:
            return (None)

    def set(self, key, value):
        ''' Sets a configuration value.  If the specified key doesn't
        exist, a new key entry will be created.

        param key: a key of the configuration value
        param value: a new value of the key
        '''
        self._config[key] = value

if __name__ == '__main__':
    config = UKAIConfig()
    print config._config
    if config.get('nonexistent') is None:
        print 'Getting non existent entry worked.'
    config.set('test', 'testvalue')
    if config.get('test') == 'testvalue':
        print 'Setting and getting worked.'
