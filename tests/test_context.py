# -*- coding: utf-8 -*-

import pytest

from lektor.context import (
    get_ctx,
    Context,
    )

from lektorlib.context import (
    disable_dependency_recording,
    DependencyIgnoringContextProxy,
    )


class Test_disable_dependency_recording(object):

    @pytest.mark.usefixtures('lektor_context')
    def test(self):
        get_ctx().record_dependency('a')
        with disable_dependency_recording():
            get_ctx().record_dependency('b')
        get_ctx().record_dependency('c')
        assert get_ctx().referenced_dependencies == set(['a', 'c'])

    def test_no_context(self):
        assert get_ctx() is None
        with disable_dependency_recording():
            assert get_ctx() is None
        assert get_ctx() is None


class TestDependencyIgnoringContextProxy(object):
    @pytest.fixture
    def proxy(self, lektor_context):
        return DependencyIgnoringContextProxy(lektor_context)

    def test_sets_context(self, proxy, lektor_context):
        assert get_ctx() is lektor_context
        with proxy:
            assert get_ctx() is proxy
        assert get_ctx() is lektor_context

    def test_isinstance(self, proxy):
        assert isinstance(proxy, DependencyIgnoringContextProxy)
        assert isinstance(proxy, Context)

    def test_cache(self, proxy, lektor_context):
        proxy.cache['test'] = 'value'
        assert lektor_context.cache['test'] == 'value'

    def test_record_dependency(self, proxy, lektor_context):
        lektor_context.record_dependency('a')
        proxy.record_dependency('b')
        assert proxy.referenced_dependencies == set('a')

    def test_record_virtual_dependency(self, proxy, lektor_context,
                                       lektor_pad):
        proxy.record_virtual_dependency(lektor_pad.get('/projects@1'))
        assert not proxy.referenced_virtual_dependencies
        lektor_context.record_virtual_dependency(lektor_pad.get('/projects@2'))
        assert proxy.referenced_virtual_dependencies
