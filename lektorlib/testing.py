"""Test helpers

"""
from contextlib import contextmanager
import re

from lektor.context import get_ctx


@contextmanager
def assert_no_dependencies(match=None):
    def check_dep(dep):
        if match is not None:
            path = dep if isinstance(dep, str) else dep.path
            if not re.search(match, path):
                return
        assert False, "Unexpected dependency: %r" % dep

    with get_ctx().gather_dependencies(check_dep):
        yield
