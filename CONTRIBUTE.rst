Contribute
----------
We welcome any code contributions and hope that the documentation for this
library facilitates your understanding of the
``optical-automation`` repository.

.. note::
    While Ansys maintains the Optical Automation library and thoroughly
    reviews all submissions before merging them, its goal is to foster
    a community that can support user questions and develop new features
    to make this library useful for all users. As such, questions or
    submissions to this repository are welcomed and encouraged.

Installation
------------
Clone and install the Optimation Automation library in development
mode with:

.. code::

   git clone https://github.com/ansys/optical-automation.git
   cd optical-automation
   pre-commit install
   pip install -e .


Testing
-------
Tests are in the `tests <tests>`_ directory. A configuration file allows you
to choose the version of Ansys SPEOS and script API for tests. Running tests requires pytest as test runner. 

Test configuration file
~~~~~~~~~~~~~~~~~~~~~~~
The configuration file  `tests/config.py <tests/config.py>`_ located in tests folder 
contains version of Ansys SPEOS and the script API to use for running tests. You can
change the version parameters according to your test needs. For example:

- **SCDM_VERSION** (integer): Speos version is  ``222`` for 2022 R2.
- **API_VERSION** (integer): API version is ``21`` for V21. 
 
Launch unit tests
~~~~~~~~~~~~~~~~~
Run all tests defined in the ``tests`` folder with:

.. code::

   pytest -v tests

