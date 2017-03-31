curb_energy
===========

.. image:: https://travis-ci.org/ginoledesma/curb_energy.svg?branch=develop
    :target: https://travis-ci.org/ginoledesma/curb_energy

.. image:: https://readthedocs.org/projects/curb-energy/badge/?version=latest
    :target: http://curb-energy.readthedocs.io/en/latest/?badge=latest
    :alt: Documentation Status


A Python library to interact with the `Curb API`_ built on top of `asyncio`_
and `aiohttp`_.


Disclaimer
==========

This project is not affiliated with `Curb Inc.`_. Curb maintains a
`github repository <https://github.com/curb>`_ of various projects and
documents their API, which is built upon `HAL`_.

I wanted something more pythonic than using HAL-tools to consume the API, and
it was also a good opportunity for experimenting with using asyncio and
aiohttp for handling streaming data.


Requirements
============

curb_energy requires Python 3.5 or later, mostly due to the async and type
hint syntax used in the library.


Installation
============

curb_energy can be installed using ``pip``, ``easy_install`` or ``setup.py``

.. code-block:: bash

    pip install curb_energy

You may want to install the library in a `virtual environment <https://www
.python.org/dev/peps/pep-0405/>`_ to test things out.


License
=======

curb_energy is offered under the `Apache License 2.0`_.


.. _Apache License 2.0: LICENSE
.. _Curb Inc.: http://energycurb.com/
.. _Curb API: http://docs.energycurb.com/
.. _HAL: http://stateless.co/hal_specification.html
.. _asyncio: https://docs.python.org/3/library/asyncio.html
.. _aiohttp: http://aiohttp.readthedocs.io