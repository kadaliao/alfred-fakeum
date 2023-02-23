from datetime import timedelta
import weakref
from collections import OrderedDict


class _TzSingleton(type):
    def __init__(self, *args, **kwargs):
        self.__instance = None
        super(_TzSingleton, self).__init__(*args, **kwargs)

    def __call__(self):
        if self.__instance is None:
            self.__instance = super(_TzSingleton, self).__call__()
        return self.__instance


class _TzFactory(type):
    def instance(self, *args, **kwargs):
        """Alternate constructor that returns a fresh instance"""
        return type.__call__(self, *args, **kwargs)


class _TzOffsetFactory(_TzFactory):
    def __init__(self, *args, **kwargs):
        self.__instances = weakref.WeakValueDictionary()
        self.__strong_cache = OrderedDict()
        self.__strong_cache_size = 8

    def __call__(self, name, offset):
        if isinstance(offset, timedelta):
            key = (name, offset.total_seconds())
        else:
            key = (name, offset)

        instance = self.__instances.get(key, None)
        if instance is None:
            instance = self.__instances.setdefault(key, self.instance(name, offset))

        self.__strong_cache[key] = self.__strong_cache.pop(key, instance)

        # Remove an item if the strong cache is overpopulated
        # TODO: Maybe this should be under a lock?
        if len(self.__strong_cache) > self.__strong_cache_size:
            self.__strong_cache.popitem(last=False)

        return instance


class _TzStrFactory(_TzFactory):
    def __init__(self, *args, **kwargs):
        self.__instances = weakref.WeakValueDictionary()
        self.__strong_cache = OrderedDict()
        self.__strong_cache_size = 8

    def __call__(self, s, posix_offset=False):
        key = (s, posix_offset)
        instance = self.__instances.get(key, None)

        if instance is None:
            instance = self.__instances.setdefault(key, self.instance(s, posix_offset))

        self.__strong_cache[key] = self.__strong_cache.pop(key, instance)


        # Remove an item if the strong cache is overpopulated
        # TODO: Maybe this should be under a lock?
        if len(self.__strong_cache) > self.__strong_cache_size:
            self.__strong_cache.popitem(last=False)

        return instance

