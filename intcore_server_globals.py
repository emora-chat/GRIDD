
LOCAL = True
IS_SERIALIZING = False
INFERENCE = True
USECACHE = True
DEBUG = False

KBCACHE = 'kbcache'
NLGCACHE = 'nlgcache'
INFCACHE = 'infcache'
NLUCACHE = 'nlucache'
import platform
if platform.system()=="Windows":
    CACHESEP = '___'
else:
    CACHESEP = '>'
