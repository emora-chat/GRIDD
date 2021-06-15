
LOCAL = True
IS_SERIALIZING = True
INFERENCE = True
USECACHE = True
KBCACHE = 'kbcache'
NLGCACHE = 'nlgcache'
INFCACHE = 'infcache'
NLUCACHE = 'nlucache'
import platform
if platform.system()=="Windows":
    CACHESEP = '___'
else:
    CACHESEP = '>'
