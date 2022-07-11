Contribute
----------
We welcome any code contributions and we hope that this
guide will facilitate an understanding of the ansys-optical-automation code
repository. It is important to note that while the ansys-optical-automation
is maintained by Ansys and any submissions will be reviewed
thoroughly before merging, we still seek to foster a community that can
support user questions and develop new features to make this library
a useful tool for all users.  As such, we welcome and encourage any
questions or submissions to this repository.

Installation
------------
Clone and install in development mode with:

.. code::

   git clone https://github.com/ansys/optical-automation.git
   cd optical-automation
   pre-commit install
   pip install -e .

Testing
-------
Tests are in `tests <tests>`_ directory. A configuration file allows to choose the version
of Ansys SPEOS and script API for tests. Running tests requires pytest as test runner. 

Test configuration file
~~~~~~~~~~~~~~~~~~~~~~~
The configuration file  `tests/config.py <tests/config.py>`_ located in tests folder 
contains version of Ansys SPEOS and script API used for running tests. The version 
parameters can be changed according to your test needs. Example:

- **SCDM_VERSION** (integer): Speos version as 222 for 2022R2.
- **API_VERSION** (integer): API version as 21 for V21. 
 
Launch unit tests
~~~~~~~~~~~~~~~~~
To run all the tests defined under tests folder.

.. code::

   pytest -v tests

Building Documentation
~~~~~~~~~~~~~~~~~~~~~~

.. code::

   cd doc
   sphinx-apidoc -o api ..\ansys_optical_automation
   make.bat html

