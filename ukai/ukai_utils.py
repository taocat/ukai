import netifaces
import time

from ukai_config import UKAIConfig

UKAIIfaddrCache = {
    'expiration_time': 0,
    'cached_addrs': [],
}
UKAI_IFADDR_CACHE_VALID_TIME = 1

def UKAIIsLocalNode(node):
    now = time.time()

    if (('ifaddr_cache' in UKAIConfig)
        and (UKAIConfig['ifaddr_cache'] is True)):
        # ifaddr cache is enabled.
        if UKAIIfaddrCache['expiration_time'] > now:
            return (node in UKAIIfaddrCache['cached_addrs'])

    UKAIIfaddrCache['cached_addrs'] = []
    for interface in netifaces.interfaces():
        ifaddresses = netifaces.ifaddresses(interface)
        for family in ifaddresses.keys():
            for addr in ifaddresses[family]:
                UKAIIfaddrCache['cached_addrs'].append(addr['addr'])
    UKAIIfaddrCache['expiration_time'] = (now
                                          + UKAI_IFADDR_CACHE_VALID_TIME)

    return (node in UKAIIfaddrCache['cached_addrs'])
