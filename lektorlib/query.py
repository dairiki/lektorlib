# -*- coding: utf-8 -*-
"""A Query-like object which can be used to access a precomputed
sequence of sources.  This works for virtual sources, too.


"""
from collections import OrderedDict

import six

from lektor.db import Query
from lektor.environment import PRIMARY_ALT


def get_source(pad, path, alt=PRIMARY_ALT, page_num=None, persist=True):
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

    if page_num is None or '@' not in path:
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


class PrecomputedQuery(Query):
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
    def __init__(self, path, pad, child_ids, alt=PRIMARY_ALT):
        super(PrecomputedQuery, self).__init__(path, pad, alt=alt)
        # We really just want an ordered set, but we'll use an OrderedDict
        # to avoid requiring another library.
        self.__child_ids = OrderedDict((id_, None) for id_ in child_ids)
        self.__assert_is_not_attachment_query()

    def _get(self, id, persist=True, page_num=Ellipsis):
        """Low level record access."""
        if id not in self.__child_ids:
            return None         # not in our query set
        if page_num is Ellipsis:
            page_num = self._page_num
        return get_source(self.pad,
                          path='%s/%s' % (self.path, id),
                          page_num=page_num, alt=self.alt, persist=persist)

    def _iterate(self):
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
                path = '%s/%s' % (self.path, id)
                raise RuntimeError("could not load source for %r" % path)

            is_page = not getattr(record, 'is_attachment', False)
            if is_page and self._matches(record):
                yield record

    def get_order_by(self):
        # child_ids are already in default order, so unless an ordering
        # is explicitly applied, we do not need to sort the results
        return self._order_by

    def __assert_is_not_attachment_query(self):
        if not self._include_pages or self._include_attachments:
            raise AssertionError(
                "Attachment queries are not currently supported")

    def count(self):
        if self._pristine:
            # optimization
            return len(self.__child_ids)
        return super(PrecomputedQuery, self).count()

    def get(self, id, page_num=Ellipsis):
        # optimization
        if id in self.__child_ids:
            return self._get(id, page_num=page_num)

    def __bool__(self):
        if self._pristine:
            # optimization
            return len(self.__child_ids) > 0
        return super(PrecomputedQuery, self).__bool__()

    if six.PY2:                 # pragma: no cover
        __nonzero__ = __bool__
