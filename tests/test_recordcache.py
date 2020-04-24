# -*- coding: utf-8 -*-

import pytest

from lektor.sourceobj import VirtualSourceObject

from lektorlib.recordcache import get_or_create_virtual


class Test_get_or_create_virtual(object):
    @pytest.fixture
    def record(self, lektor_pad):
        return lektor_pad.get('/about')

    @pytest.fixture
    def virtual_source(self, record):
        return DummyVirtualSource(record, 'virtual/path')

    def test_finds_cached_record(self, lektor_pad, record, virtual_source):
        lektor_pad.cache.remember(virtual_source)

        def creator():
            pytest.fail("should not be called")
        rv = get_or_create_virtual(record, 'virtual/path', creator)
        assert rv is virtual_source

    def test_creates_record(self, record, virtual_source):
        def creator():
            creator.calls.append(())
            return virtual_source
        creator.calls = []

        for n in range(2):
            rv = get_or_create_virtual(record, 'virtual/path', creator)
            assert rv is virtual_source
        assert creator.calls == [()]

    @pytest.mark.parametrize('persist', [True, False])
    def test_persist(self, record, virtual_source, persist, lektor_pad):
        def creator():
            return virtual_source
        get_or_create_virtual(record, 'virtual/path', creator,
                              persist=persist)
        if persist:
            assert virtual_source in lektor_pad.cache.persistent.values()
        else:
            assert virtual_source in lektor_pad.cache.ephemeral.values()

    def test_remembers_missing(self, record):
        def creator():
            creator.calls.append(())
            return None
        creator.calls = []

        for n in range(2):
            rv = get_or_create_virtual(record, 'virtual/path', creator)
            assert rv is None
        assert creator.calls == [()]


class DummyVirtualSource(VirtualSourceObject):
    def __init__(self, record, virtual_path):
        VirtualSourceObject.__init__(self, record)
        self._virtual_path = virtual_path

    @property
    def path(self):
        return "{}@{}".format(self.record.path, self._virtual_path)
