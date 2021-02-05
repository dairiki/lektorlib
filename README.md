# Lektorlib

[![PyPI version](https://img.shields.io/pypi/v/lektorlib.svg)](https://pypi.org/project/lektorlib/)
[![PyPI Supported Python Versions](https://img.shields.io/pypi/pyversions/lektorlib.svg)](https://pypi.python.org/pypi/lektorlib/)
[![GitHub license](https://img.shields.io/github/license/dairiki/lektorlib)](https://github.com/dairiki/lektorlib/blob/master/LICENSE)
[![GitHub Actions (Tests)](https://github.com/dairiki/lektorlib/workflows/Tests/badge.svg)](https://github.com/dairiki/lektorlib)

A few bits which may possibly be useful to developers of [Lektor][] plugins.

## Bits Included

### `lektorlib.query.PrecomputedQuery`

A subclass of `lektor.db.Query` which yields a pre-computed
sequence of children.

This is useful in (at least) two circumstances:

First, when the children to be queried are virtual source objects,
the standard `lektor.db.Query` will not work.  This version will.

Second, when we would like to generate a query of a pre-computed
subset of a resource's children, this prevents intruducing
unnecessary build dependencies.  If we used a standard query with
a filter applied, still iterates of all of the parent nodes
children, registering dependencies on all of them.

### `lektorlib.context.disable_dependency_recording`

A python context manager which (temporarily) disables lektor’s
dependency recording system.

### `lektorlib.recordcache.get_or_create_virtual`

This function is a helper to streamline the caching of virtual
source objects in the lektor record cache.

`Lektor.db.Pad.get()` handles caching for regular records,
at present, however, it does not appear that it ever caches
virtual source objects, even though its record cache is perfectly
capable of doing so.

### `lektorlib.testing.assert_no_dependencies(match=None)`

This context manager is a testing helper which can be used to
check that no dependencies are recorded with lektor’s dependency
tracking system.

## Author

Jeff Dairiki <dairiki@dairiki.org>

[Lektor]: <https://www.getlektor.com/> "Lektor Static Content Management System"
