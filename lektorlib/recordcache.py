"""Helper for dealing with the Lektor record cache.

Note that ``lektor.db.Pad.get`` normally handles caching for regular
records, however, at present it does not appear that it ever caches
virtual source objects in the cache.  That said, the record cache is
perfectly capable of caching virtual sources.

"""
from __future__ import annotations

from typing import Callable
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from lektor.db import Record
    from lektor.sourceobj import VirtualSourceObject


def get_or_create_virtual(
    record: Record,
    virtual_path: str,
    creator: Callable[[], VirtualSourceObject],
    persist: bool = True,
) -> VirtualSourceObject:
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
