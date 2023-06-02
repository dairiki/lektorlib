"""Test helpers

"""
from __future__ import annotations

import re
from contextlib import contextmanager
from typing import Generator
from typing import TYPE_CHECKING

from lektor.context import get_ctx

if TYPE_CHECKING:
    from lektor.sourceobj import VirtualSourceObject


@contextmanager
def assert_no_dependencies(
    match: str | re.Pattern[str] | None = None,
) -> Generator[None, None, None]:
    def check_dep(dep: str | VirtualSourceObject) -> None:
        if match is not None:
            path = dep if isinstance(dep, str) else dep.path
            if not re.search(match, path):
                return
        raise AssertionError(f"Unexpected dependency: {dep!r}")

    with get_ctx().gather_dependencies(check_dep):
        yield
