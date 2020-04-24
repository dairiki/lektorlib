# -*- coding: utf-8 -*-
"""Helper for dealing with the Lektor record cache.

Note that ``lektor.db.Pad.get`` normally handles caching for regular
records, however, at present it does not appear that it ever caches
virtual source objects in the cache.  That said, the record cache is
perfectly capable of caching virtual sources.

"""


def get_or_create_virtual(record, virtual_path, creator, persist=True):
    cache = record.pad.cache
    source = cache.get(record.path, record.alt, virtual_path)
    if source is Ellipsis:
        source = creator()
        if source is None:
            cache.remember_as_missing(record.path, record.alt, virtual_path)
        elif persist:
            cache.persist(source)
        else:
            cache.remember(source)
    return source
