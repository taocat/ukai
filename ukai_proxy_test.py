import xmlrpclib

from ukai_config import UKAIConfig
from ukai_io import UKAIMetadata

UKAIConfig['image_root'] = './test/images'
UKAIConfig['meta_root'] = './test/meta'

meta = UKAIMetadata('./test/meta/test')

s = xmlrpclib.ServerProxy('http://localhost:%d' % UKAIConfig['proxy_port'])
print s.system.listMethods()

data = 'Hello World!'
offset = 10
for block in range(0, meta.size / meta.block_size):
    print 'block %d' % block
    s.write(meta.name, meta.block_size, block, offset, xmlrpclib.Binary(data))
    ver = s.read(meta.name, meta.block_size, block, offset, len(data)).data
    if ver != data:
        print 'error at block %d' % block
