# -*- coding: utf-8 -*-
"""Helpers

"""
from contextlib import contextmanager

from lektor.context import (
    get_ctx,
    Context,
    )


@contextmanager
def disable_dependency_recording():
    """Disable dependency recording within context

    We do this by pushing a new context onto the context stack.  The
    new context proxies all access — except for depency reporting —
    back to the original context.

    """
    ctx = get_ctx()
    if ctx is None:
        yield
    else:
        with DependencyIgnoringContextProxy(ctx):
            yield


class DependencyIgnoringContextProxy(Context):
    __slots__ = ['_ctx']

    def __init__(self, ctx):
        self._ctx = ctx

    def __getattr__(self, attr):
        return getattr(self._ctx, attr)

    def record_dependency(self, filename):
        pass

    def record_virtual_dependency(self, virtual_source):
        pass
