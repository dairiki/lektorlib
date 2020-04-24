# -*- coding: utf-8 -*-

import pytest

from lektor.context import get_ctx

from lektorlib.testing import assert_no_dependencies


@pytest.mark.usefixtures('lektor_context')
class Test_assert_no_deps(object):

    def test_dep(self):
        with pytest.raises(AssertionError):
            with assert_no_dependencies():
                get_ctx().record_dependency('dependency')

    def test_no_deps(self):
        with assert_no_dependencies():
            pass

    def test_dep_matches(self):
        with pytest.raises(AssertionError):
            with assert_no_dependencies('bad'):
                get_ctx().record_dependency('bad')

    def test_no_match(self):
        with assert_no_dependencies('bad'):
            get_ctx().record_dependency('good')
