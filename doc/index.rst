******************************
Python library for *temporenc*
******************************

This is a Python library implementing the `temporenc format
<http://temporenc.org>`_ for dates and times.

Features:

* Support for all *temporenc* types

* Interoperability with the ``datetime`` module

* Time zone support, including conversion to local time

* Compatibility with both Python 2 (2.6+) and Python 3 (3.2+)

* Decent performance

* Permissive BSD license

____


.. rubric:: Contents

.. contents::
   :local:

____


Installation
============


Use ``pip`` to install the library (e.g. into a ``virtualenv``):

.. code-block:: shell-session

    $ pip install temporenc

____


Usage
=====

.. py:currentmodule:: temporenc

Basic usage
-----------

All functionality is provided by a single module with the name ``temporenc``::

    >>> import temporenc

To encode date and time information into a byte string, use the :py:func:`packb`
function::

    >>> temporenc.packb(year=2014, month=10, day=23)
    b'\x8f\xbd6'

This function automatically determines the most compact representation for the
provided information. In this case, the result uses *temporenc* type ``D``, but
if you want to use a different type, you can provide it explicitly::

    >>> temporenc.packb(type='DT', year=2014, month=10, day=23)
    b'\x1fzm\xff\xff'

To unpack a byte string, use :py:func:`unpackb`::

    >>> moment = temporenc.unpackb(b'\x1fzm\xff\xff')
    >>> moment
    <temporenc.Moment '2014-10-23'>
    >>> print(moment)
    2014-10-23

As you can see, unpacking returns a :py:class:`Moment` instance. This class has
a reasonable string representation, but it is generally more useful to access
the individual components using one of its many attributes::

    >>> print(moment.year)
    2014
    >>> print(moment.month)
    10
    >>> print(moment.day)
    13
    >>> print(moment.second)
    None

Since all fields are optional in *temporenc* values, and since no time
information was set in this example, some of the attributes (e.g. `second`) are
`None`.

Integration with the ``datetime`` module
----------------------------------------

Python has built-in support for date and time handling, provided by the
``datetime`` module in the standard library, which is how applications usually
work with date and time information. Instead of specifying all the fields
manually when packing data, which is cumbersome and error-prone, the
``temporenc`` module integrates with the built-in ``datetime`` module::

    >>> import datetime
    >>> now = datetime.datetime.now()
    >>> now
    datetime.datetime(2014, 10, 23, 18, 45, 23, 612883)
    >>> temporenc.packb(now)
    b'W\xde\x9bJ\xd5\xe5hL'

As you can see, instead of specifying all the components manually, instances of
the built-in ``datetime.datetime`` class can be passed directly as the first
argument to :py:func:`packb`. This also works for ``datetime.date`` and
``datetime.time`` instances.

Since the Python ``datetime`` module *always* uses microsecond precision, this
library defaults to *temporenc* types with sub-second precision (e.g. ``DTS``)
when an instance of one of the ``datetime`` classes is passed. If no subsecond
precision is required, you can specify a different type to save space::

    >>> temporenc.packb(now, type='DT')
    b'\x1fzm+W'

The integration with the ``datetime`` module works both ways. Instances of the
:py:class:`Moment` class (as returned by the unpacking functions) can be
converted to the standard date and time classes using the
:py:meth:`~Moment.datetime`, :py:meth:`~Moment.date`, and
:py:meth:`~Moment.time` methods::

    >>> moment = temporenc.unpackb(b'W\xde\x9bJ\xd5\xe5hL')
    >>> moment
    <temporenc.Moment '2014-10-23 18:45:23.612883'>
    >>> moment.datetime()
    datetime.datetime(2014, 10, 23, 18, 45, 23, 612883)
    >>> moment.date()
    datetime.date(2014, 10, 23)
    >>> moment.time()
    datetime.time(18, 45, 23, 612883)

Conversion to and from classes from the ``datetime`` module have full time zone
support. See the API docs for :py:meth:`Moment.datetime` for more details about
time zone handling.

.. warning::

   The Python ``temporenc`` module only concerns itself with encoding and
   decoding. It does *not* do any date and time calculations, and hence does not
   validate that dates are correct. For example, it handles the non-existent
   date `February 30` just fine. Always convert to native classes from the
   ``datetime`` module if you need to work with date and time information in
   your application.


Working with file-like objects
------------------------------

The *temporenc* encoding format allows for reading data from a stream without
knowing in advance how big the encoded byte string is. This library supports
this through the :py:func:`unpack` function, which consumes exactly the required
number of bytes from the stream::

    >>> import io
    >>> fp = io.BytesIO()  # this could be a real file
    >>> fp.write(b'W\xde\x9bJ\xd5\xe5hL')
    >>> fp.write(b'foo')
    >>> fp.seek(0)
    >>> temporenc.unpack(fp)
    <temporenc.Moment '2014-10-23 18:45:23.612883'>
    >>> fp.tell()
    8
    >>> fp.read()
    b'foo'

For writing directly to a file-like object, the :py:func:`pack` function can be
used, though this is just a shortcut.

____


API
===

The :py:func:`packb` and :py:func:`unpackb` functions operate on byte strings.

.. autofunction:: packb
.. autofunction:: unpackb

The :py:func:`pack` and :py:func:`unpack` functions operate on file-like
objects.

.. autofunction:: pack
.. autofunction:: unpack

Both :py:func:`unpackb` and :py:func:`unpack` return an instance of the
:py:class:`Moment` class.

.. autoclass:: Moment
   :members:

____


Contributing
============

Source code, including the test suite, is maintained at Github:

  `temporenc-python on github <https://github.com/wbolster/temporenc-python>`_

Feel free to submit feedback, report issues, bring up improvement ideas, and
contribute fixes!

____


Version history
===============

* x.y (not yet released)

  * no longer perform utc conversion, see
    `temporenc#8 <https://github.com/temporenc/temporenc/issues/8>`_

* 0.1

  Release date: 2014-10-30

  Initial public release.

____

.. license is in a separate file

.. include:: ../LICENSE.rst
