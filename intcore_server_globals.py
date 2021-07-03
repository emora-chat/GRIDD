
LOCAL = True
IS_SERIALIZING = False
INFERENCE = True
USECACHE = True
COBOTCACHE = False
DEBUG = False

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
