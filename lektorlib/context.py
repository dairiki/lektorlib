"""Helpers

"""
from __future__ import annotations

from contextlib import contextmanager
from typing import Any
from typing import Generator
from typing import TYPE_CHECKING

from lektor.context import Context
from lektor.context import get_ctx

if TYPE_CHECKING:
    from lektor.sourceobj import VirtualSourceObject


@contextmanager
def disable_dependency_recording() -> Generator[None, None, None]:
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


class DependencyIgnoringContextProxy(Context):  # type: ignore[misc]
    __slots__ = ["_ctx"]

    def __init__(self, ctx: Context):
        self._ctx = ctx

    def __getattr__(self, attr: str) -> Any:
        return getattr(self._ctx, attr)

    def record_dependency(self, filename: str, affects_url: bool | None = None) -> None:
        pass

    def record_virtual_dependency(self, virtual_source: VirtualSourceObject) -> None:
        pass
