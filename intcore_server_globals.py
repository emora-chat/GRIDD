
LOCAL = True
IS_SERIALIZING = False
IS_MEGA_SERIALIZING = False
INFERENCE = True
USECACHE = True
COBOTCACHE = False
DEBUG = True

KBCACHE = 'kbcache'
NLGCACHE = 'nlgcache'
INFCACHE = 'infcache'
NLUCACHE = 'nlucache'
CCACHE = 'cobotcache'
import platform
if platform.system()=="Windows":
    CACHESEP = '___'
else:
    CACHESEP = '>'
