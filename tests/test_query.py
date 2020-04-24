# -*- coding: utf-8 -*-

import inspect
import re

import pytest

from lektor.environment import (
    Expression,
    PRIMARY_ALT,
    )
from lektor.pluginsystem import Plugin
from lektor.sourceobj import VirtualSourceObject

from lektorlib.query import (
    get_source,
    PrecomputedQuery,
    )


class DummyVirtualSource(VirtualSourceObject):
    virtual_path_prefix = 'dummy-virtual'

    def __init__(self, record, extra_path=None):
        VirtualSourceObject.__init__(self, record)
        self.extra_path = extra_path

    @property
    def path(self):
        fmt = "{0.record.path}@{0.virtual_path_prefix}"
        if self.extra_path:
            fmt += "/{0.extra_path}"
        return fmt.format(self)


class PaginatedVirtualSource(DummyVirtualSource):
    virtual_path_prefix = 'paginated-virtual'

    def __init__(self, record, extra_path=None, page_num=None):
        super(PaginatedVirtualSource, self).__init__(record, extra_path)
        self.page_num = page_num

    @property
    def path(self):
        path = super(PaginatedVirtualSource, self).path
        if self.page_num is not None:
            path += "/page={:d}".format(self.page_num)
        return path

    @property
    def pagination(self):
        return DummyPaginationController(self)


class DummyPaginationController(object):
    def __init__(self, source):
        self.source = source

    def for_page(self, page_num):
        source = self.source
        if page_num == source.page_num:
            return source
        return PaginatedVirtualSource(
            source.record, source.extra_path, page_num)


class DummyPlugin(Plugin):
    def on_setup_env(self, **extra):
        env = self.env

        @env.virtualpathresolver('dummy-virtual')
        def resolve_virtual(record, pieces):
            if 'missing' not in pieces:
                return DummyVirtualSource(record, extra_path='/'.join(pieces))

        @env.virtualpathresolver('paginated-virtual')
        def resolve_paginated(record, pieces):
            if pieces and re.match(r'page=(\d+)\Z', pieces[-1]):
                page_num = int(pieces[-1][len('page='):])
                pieces = pieces[:-1]
            else:
                page_num = None
            if 'missing' not in pieces:
                return PaginatedVirtualSource(
                    record, extra_path='/'.join(pieces), page_num=page_num)


@pytest.fixture
def dummy_plugin(lektor_env):
    # Configure lektor_env with our dummy plugin
    plugin_controller = lektor_env.plugin_controller
    plugin_controller.instanciate_plugin('dummy-plugin', DummyPlugin)
    plugin_controller.emit('setup-env')
    return lektor_env.plugins['dummy-plugin']


@pytest.mark.usefixtures('dummy_plugin')
class Test_get_source(object):
    @pytest.mark.parametrize("path", [
        "/",
        "/about",
        "/about@dummy-virtual",
        "/projects@dummy-virtual/foo",
        ])
    def test_get_unpaginated(self, lektor_pad, path):
        source = get_source(lektor_pad, path)
        assert source.path == path
        assert getattr(source, 'page_num', None) is None

    @pytest.mark.parametrize("path", [
        "/projects",
        "/projects@paginated-virtual",
        "/@paginated-virtual/foo",
        ])
    def test_get_paginated(self, lektor_pad, path):
        page_num = 1
        source = get_source(lektor_pad, path, page_num=page_num)
        if '@' in path:
            assert source.path == '%s/page=%d' % (path, page_num)
        else:
            assert source.path == '%s@%d' % (path, page_num)
        assert source.page_num == page_num

    @pytest.mark.parametrize("path", [
        "/@dummy-virtual",
        ])
    def test_get_paginated_unsupported(self, lektor_pad, path):
        page_num = 1
        source = get_source(lektor_pad, path, page_num=page_num)
        assert source is None

    @pytest.mark.parametrize("path", [
        "/missing",
        "/missing@dummy-virtual",
        "/about@missing-virtual",
        ])
    def test_get_missing(self, lektor_pad, path):
        assert get_source(lektor_pad, path) is None
        assert get_source(lektor_pad, path, page_num=1) is None


@pytest.mark.usefixtures('dummy_plugin')
class QueryTestBase(object):

    @pytest.fixture
    def make_query(self, query_path, lektor_pad):
        def make_query(child_ids, **kw):
            return PrecomputedQuery(query_path, lektor_pad, child_ids, **kw)
        return make_query

    @pytest.fixture
    def jinja_eval(self, lektor_env, lektor_pad):
        def jinja_eval(expr, this=None, alt=None, **kw):
            frame = inspect.currentframe()
            try:
                # Get locals from calling frame
                locals = dict(frame.f_back.f_locals)
            finally:
                del frame
            locals.update(kw)
            return Expression(lektor_env, expr).evaluate(
                lektor_pad, this=this, values=locals, alt=alt)
        return jinja_eval

    @pytest.fixture
    def query(self, make_query, child_ids):
        return make_query(child_ids)

    @pytest.mark.parametrize("extra_kw, expected_alt", [
        ({}, PRIMARY_ALT),
        ({'alt': 'xx'}, 'xx'),
        ])
    def test_with_alt(self, make_query, child_ids, extra_kw, expected_alt):
        query = make_query(child_ids, **extra_kw)
        assert query.first().alt == expected_alt

    def test_assert_is_not_attachment_query(self, query):
        query._include_attachments = True
        with pytest.raises(AssertionError,
                           match=r'(?i)attachment\b.* not\b.* supported'):
            query.first()

    @pytest.mark.parametrize("child_ids", [('missing',)])
    def test_raises_on_missing_id(self, query):
        with pytest.raises(RuntimeError):
            query.first()

    def test__get_bad_id(self, query):
        assert query._get('missing', persist=False) is None

    def test_count(self, query, lektor_context):
        # .count() on a pristine PrecomputedQuery should not register deps
        n = query.count()
        assert not lektor_context.referenced_dependencies
        assert not lektor_context.referenced_virtual_dependencies

        # .on a non-pristine query, it does
        assert n == query.filter(lambda r: True).count()
        assert lektor_context.referenced_dependencies \
            or lektor_context.referenced_virtual_dependencies

    def test_bool(self, query, lektor_context):
        # .__bool__() on a pristine PrecomputedQuery should not register deps
        assert query
        assert not lektor_context.referenced_dependencies
        assert not lektor_context.referenced_virtual_dependencies

        # .on a non-pristine query, it does
        assert not query.filter(lambda r: False)
        assert lektor_context.referenced_dependencies \
            or lektor_context.referenced_virtual_dependencies


class TestConcreteSourceQuery(QueryTestBase):
    @pytest.fixture
    def query_path(self):
        return '/'

    @pytest.fixture
    def child_ids(self):
        return ('about', 'projects')

    def test_iter(self, query):
        assert [obj.path for obj in query] == ['/about', '/projects']

    @pytest.mark.parametrize("child_ids", [('about',)])
    def test_get(self, query):
        assert query.get('about')['_id'] == 'about'
        assert query.get('projects') is None

    def test_filter(self, query, jinja_eval):
        assert jinja_eval("query.filter(F.title == 'Projects').count()") == 1

    def test_order_by(self, query, jinja_eval):
        reversed = query.order_by('-title')
        assert [obj['title'] for obj in reversed] == [
            'Projects',
            'About this Website',
            ]


class TestVirtualSourceQuery(QueryTestBase):
    virtual_path_prefix = DummyVirtualSource.virtual_path_prefix

    @pytest.fixture
    def query_path(self):
        return '/projects@{}'.format(self.virtual_path_prefix)

    @pytest.fixture
    def child_ids(self):
        return ('a', 'b')

    def test_iter(self, query):
        assert [obj.path for obj in query] == [
            '/projects@{}/a'.format(self.virtual_path_prefix),
            '/projects@{}/b'.format(self.virtual_path_prefix),
            ]

    def test_get(self, query):
        assert query.get('a').extra_path == 'a'
        assert query.get('x') is None

    def test_request_page(self, query):
        assert list(query.request_page(1)) == []


class TestPaginatedVirtualSourceQuery(TestVirtualSourceQuery):
    virtual_path_prefix = PaginatedVirtualSource.virtual_path_prefix

    def test_request_page(self, query):
        assert [obj.path for obj in query.request_page(1)] == [
            '/projects@paginated-virtual/a/page=1',
            '/projects@paginated-virtual/b/page=1',
            ]
