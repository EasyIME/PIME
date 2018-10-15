================================
pyuv: Python interface for libuv
================================

.. image:: https://badge.fury.io/py/pyuv.png
    :target: http://badge.fury.io/py/pyuv

pyuv is a Python module which provides an interface to libuv.
`libuv <http://github.com/libuv/libuv>`_ is a high performance
asynchronous networking and platform abstraction library.

libuv is built on top of epoll/kequeue/event ports/etc on Unix and
IOCP on Windows systems providing a consistent API on top of them.

pyuv's features:

- Non-blocking TCP sockets
- Non-blocking named pipes
- UDP support (including multicast)
- Timers
- Child process spawning
- Asynchronous DNS resolution (getaddrinfo)
- Asynchronous file system APIs
- High resolution time
- System memory information
- System CPUs information
- Network interfaces information
- Thread pool scheduling
- ANSI escape code controlled TTY
- File system events (inotify style and stat based)
- IPC and TCP socket sharing between processes
- Arbitrary file descriptor polling
- Thread synchronization primitives


CI status
=========

Stable branch (v1.x)

- Travis CI:
    .. image:: https://travis-ci.org/saghul/pyuv.svg?branch=v1.x
               :target: http://travis-ci.org/saghul/pyuv

- AppVeyor:
    .. image:: https://ci.appveyor.com/api/projects/status/ne2un9br9t0qs5cd?svg=true
               :target: https://ci.appveyor.com/project/saghul/pyuv


Versioning
==========

Starting with version 1.0.0, pyuv follows the `Semantic Versioning <http://semver.org/>`_
specification, like libuv does.

All releases are downloadable from `the GitHub tags page <https://github.com/saghul/pyuv/tags>`_,
and the latest stable release from `PyPI <https://pypi.python.org/pypi/pyuv>`_.


Documentation
=============

http://readthedocs.org/docs/pyuv/


Installing
==========

pyuv can be installed via pip as follows:

::

    pip install pyuv


Building
========

Get the source:

::

    git clone https://github.com/saghul/pyuv


Linux:

::

    ./build_inplace

Mac OSX:

::

    (XCode needs to be installed)
    export ARCHFLAGS="-arch x86_64"
    ./build_inplace

Microsoft Windows (with Visual Studio):

::

    python setup.py build_ext --inplace


Running the test suite
======================

There are several ways of running the test ruite:

- Run the test with the current Python interpreter:

  From the toplevel directory, run: ``nosetests -v``

- Use Tox to run the test suite in several virtualenvs with several interpreters

  From the toplevel directory, run: ``tox`` this will run the test suite
  on Python 2.7, 3.3 and 3.4 (you'll need to have them installed beforehand)


Author
======

Saúl Ibarra Corretgé <saghul@gmail.com>


License
=======

Unless stated otherwise on-file pyuv uses the MIT license, check LICENSE file.


Python versions
===============

Python 2.7, and Python >= 3.3 versions are supported.


Contributing
============

If you'd like to contribute, fork the project, make a patch and send a pull
request. Have a look at the surrounding code and please, make yours look
alike :-)



