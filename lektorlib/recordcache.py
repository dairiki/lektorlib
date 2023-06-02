"""Helper for dealing with the Lektor record cache.

Note that ``lektor.db.Pad.get`` normally handles caching for regular
records, however, at present it does not appear that it ever caches
virtual source objects in the cache.  That said, the record cache is
perfectly capable of caching virtual sources.

"""
from __future__ import annotations

import sys
from typing import Callable
from typing import overload
from typing import TYPE_CHECKING
from typing import TypeVar

if sys.version_info >= (3, 10):
    from types import EllipsisType
elif TYPE_CHECKING:
    from builtins import ellipsis as EllipsisType

if TYPE_CHECKING:
    from lektor.db import Record
    from lektor.sourceobj import VirtualSourceObject


_VSO = TypeVar("_VSO", bound="VirtualSourceObject")


@overload
def get_or_create_virtual(
    record: Record,
    virtual_path: str,
    creator: Callable[[], _VSO],
    persist: bool = True,
) -> _VSO:
    ...


@overload
def get_or_create_virtual(
    record: Record,
    virtual_path: str,
    creator: Callable[[], _VSO | None],
    persist: bool = True,
) -> _VSO | None:
    ...


def get_or_create_virtual(
    record: Record,
    virtual_path: str,
    creator: Callable[[], _VSO | None],
    persist: bool = True,
) -> _VSO | None:
    cache = record.pad.cache
    source: VirtualSourceObject | None | EllipsisType
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
