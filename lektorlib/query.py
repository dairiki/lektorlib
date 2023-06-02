"""A Query-like object which can be used to access a precomputed
sequence of sources.  This works for virtual sources, too.


"""
from __future__ import annotations

import sys
from collections import OrderedDict
from typing import Generator
from typing import Iterable
from typing import Sequence
from typing import TYPE_CHECKING

from lektor.db import Pad
from lektor.db import Query
from lektor.db import Record
from lektor.environment import PRIMARY_ALT
from lektor.sourceobj import VirtualSourceObject

if sys.version_info >= (3, 10):
    from types import EllipsisType
elif TYPE_CHECKING:
    from builtins import ellipsis as EllipsisType


def get_source(
    pad: Pad,
    path: str,
    alt: str = PRIMARY_ALT,
    page_num: int | None = None,
    persist: bool = True,
) -> Record | VirtualSourceObject:
    """Like Pad.get() but works for paginated virtual sources as well as
    concrete records.

    """
    # lektor.db.Pad.get does not support page_num on a virtual path.
    # This is mostly because there seems to be no official syntax for
    # contructing a virtual path with a page number.
    #
    # Our virtual sources support pagination using their own virtual
    # path scheme (appending ``/page/<page_num>`` to their virtual path,
    # rather than appending ``@<page_num>`` as is done for concrete paths.)
    #
    # This function will use the ``source.pagination.for_page()``
    # method exposed by the pagination API to get the paginated
    # version of the source.
    #
    # NB: The user will have to ensure that pagination.for_page
    # is properly implemented for their virtual sources.

    if page_num is None or "@" not in path:
        return pad.get(path, alt=alt, page_num=page_num, persist=persist)

    source = pad.get(path, persist=persist, alt=alt)
    if source is None:
        return None
    try:
        pagination = source.pagination
    except (AttributeError, RuntimeError):
        # The lektor.db.Page.pagination property raises RuntimeError
        # rather than AttributeError if pagination is not enabled for
        # the page.
        return None

    paginated_source = pagination.for_page(page_num)
    pad.db.track_record_dependency(paginated_source)
    return paginated_source


class PrecomputedQuery(Query):  # type: ignore[misc]
    """This is a Query which yields a pre-computed sequence of children.

    This is useful in (at least) two circumstances:

    First, when the children to be queried are virtual source objects,
    the standard ``lektor.db.Query`` will not work.  This version will.

    Second, when we would like to generate a query of a pre-computed
    subset of a resource's children, this prevents intruducing
    unnecessary build dependencies.  If we used a standard query with
    a filter applied, still iterates of all of the parent nodes
    children, registering dependencies on all of them.

    """

    # Annotations for fields inherited from Query
    _order_by: Sequence[str] | None
    _page_num: int | None

    def __init__(
        self,
        path: str,
        pad: Pad,
        child_ids: Iterable[str],
        alt: str = PRIMARY_ALT,
    ):
        super().__init__(path, pad, alt=alt)
        # We really just want an ordered set, but we'll use an OrderedDict
        # to avoid requiring another library.
        self.__child_ids = OrderedDict((id_, None) for id_ in child_ids)
        self.__assert_is_not_attachment_query()

    def _get(
        self,
        id: str,
        persist: bool = True,
        page_num: int | None | EllipsisType = Ellipsis,
    ) -> Record | VirtualSourceObject:
        """Low level record access."""
        if id not in self.__child_ids:
            return None  # not in our query set
        return get_source(
            self.pad,
            path=f"{self.path}/{id}",
            page_num=self._page_num if page_num is Ellipsis else page_num,
            alt=self.alt,
            persist=persist,
        )

    def _iterate(self) -> Generator[Record | VirtualSourceObject, None, None]:
        self.__assert_is_not_attachment_query()
        # note dependencies
        self_record = self.pad.get(self.path, alt=self.alt)
        if self_record is not None:
            self.pad.db.track_record_dependency(self_record)

        for id in self.__child_ids:
            record = self._get(id, persist=False)
            if record is None:
                if self._page_num is not None:
                    # Sanity check: ensure the unpaginated version exists
                    unpaginated = self._get(id, persist=False, page_num=None)
                    if unpaginated is not None:
                        # Requested explicit page_num, but source does not
                        # support pagination.  Punt and skip it.
                        continue
                path = f"{self.path}/{id}"
                raise RuntimeError("could not load source for %r" % path)

            is_page = not getattr(record, "is_attachment", False)
            if is_page and self._matches(record):
                yield record

    def get_order_by(self) -> Sequence[str] | None:
        # child_ids are already in default order, so unless an ordering
        # is explicitly applied, we do not need to sort the results
        return self._order_by

    def __assert_is_not_attachment_query(self) -> None:
        if not self._include_pages or self._include_attachments:
            raise AssertionError("Attachment queries are not currently supported")

    def count(self) -> int:
        if self._pristine:
            # optimization
            return len(self.__child_ids)
        return super().count()  # type: ignore[no-any-return]

    def get(
        self, id: str, page_num: int | None | EllipsisType = Ellipsis
    ) -> Record | VirtualSourceObject | None:
        # optimization
        if id in self.__child_ids:
            return self._get(id, page_num=page_num)
        return None

    def __bool__(self) -> bool:
        if self._pristine:
            # optimization
            return len(self.__child_ids) > 0
        return super().__bool__()  # type: ignore[no-any-return]
