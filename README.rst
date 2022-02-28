***********
exomol2lida
***********

A software suite for processing the ExoMol line lists into standardised inputs for the
`Lida database <https://github.com/ExoMol/lida-web>`_.

The code inside this repository is designed to be executed directly on the *exoweb*
server, as it reads the exomol line list data and process them into the LiDa-compatible
lifetimes data.

This documentation page compiles hopefully all the information to get anyone fluent in
python up to speed and running.


Getting started
===============

- Clean virtual environment on the exoweb server.

- Clone the repo: ``git clone git@github.com:ExoMol/lida-web.git``

- Create the ``config/config_local.py`` file. The contents of which should be

  .. code-block:: python

    from pathlib import Path
    EXOMOL_DATA_DIR = Path("/absolute/path/to/exomol3_data")
    # the directory with individual molecules

  This points to the data, and can be changed for testing on a local PC anywhere.

- Install dependencies: ``pip install -r requirements.txt``

- Test the package if all ok: ``pytest`` will test all docstrings, integration tests and
  unit tests, ``pytest tests_integration`` and ``pytest tests_unit`` break down the
  testing.

- **Note**: The outputs for processed molecules are saved in the ``outputs`` directory.
  I have run the code on 27 molecules already, outputs of which can be found on exoweb
  in ``mhanici`` user folder. This might be the best way to familiarize oneself with
  the structure of the outputs. The outputs are by design excluded from the git VCS.


Project structure
=================

The project structure is as follows. Parts of the project will be later discussed in
more detail.

- ``config`` package contains ``config`` and ``config_local`` (not in VCS) modules
  with some project-wide configuration options.

- ``exomol2lida`` package contains all the code for the actual data generation
  and processing.

- ``input`` folder contains the input files configuring the processing of individual
  molecules.

- ``output`` folder is where the data processing outputs are saved to. Contents of this
  folder (paths to) are what needs to be passed to the data population script in the
  `lida-web <https://github.com/ExoMol/lida-web>`_. project.
  This folder is not a part of VCS (while input folder *is*). Reason is outputs can be
  quite bulky. I have, however, processed 27 molecules in the past already, outputs of
  which can be found on exoweb in ``mhanici`` user folder (in ``code``, where this
  repo is cloned). This might be the best way to familiarize oneself with
  the structure of the outputs.

- ``preferred_isotopologues`` is a package grouping some functionality for guessing
  which isotopologue for each molecule is likely the most abundant one, and should be
  a part of LIDA data.

- ``tests_unit`` and ``tests_integration`` are testing harnesses written for ``pytest``.

- ``process.py`` and ``postprocess.py`` are top-level scripts doing processing and
  post-processing for a single molecule.


Input files
===========

