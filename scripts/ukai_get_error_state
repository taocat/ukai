#!/usr/bin/env python

import sys
import xmlrpclib

from ukai.ukai_config import UKAIConfig

c = xmlrpclib.ServerProxy('http://127.0.0.1:%d' % UKAIConfig['control_port'])
print c.get_node_error_state_set()
