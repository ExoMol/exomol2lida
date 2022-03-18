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
  in ``mhanici`` user folder on the exoweb server.
  This might be the best way to familiarize oneself with
  the structure of the outputs. The outputs are by design excluded from the git VCS.


Project structure
=================

The project structure is as follows. Parts of the project will be later discussed in
more detail.

- ``config`` package contains ``config`` and ``config_local`` (not under VCS) modules
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
  a part of LIDA data. This is just a utility package and is not used implicitly by
  any other parts of the ``exomol2lida`` workflow.

- ``tests_unit`` and ``tests_integration`` are testing harnesses written for ``pytest``.

- ``process.py`` and ``postprocess.py`` are top-level scripts doing processing and
  post-processing for a single molecule.


Input files
===========

The input files located in the ``input`` folder are currently the following:

- ``input/mapping_el.py``
- ``input/molecules.py``

Let us start with the ``molecules.py`` input file.


``molecules.py`` input
----------------------

The main input file contains the configuration for each molecule that is supposed to
be processed by ``exomol2lida``. The structure of the ``molecules.py`` file is the
``dict`` with molecule formulas as keys and dictionaries with number of mandatory and
optional attributes, as follows:

.. code-block:: python

    molecules = {
        "molecule formula": {
            "mol_slug": "molecule slug",  # mandatory
            "iso_slug": "isotopologue slug",  # mandatory
            "dataset_name": "the name of the dataset",  # mandatory
            "resolve_vib": ["quantum 1", ..., "quantum n"],  # at least one of "resolve_*" needs to be given
            "resolve_el": ["quantum 1", ..., "quantum m"],  # at least one of "resolve_*" needs to be given
            "states_header": ["i", "E", "g_tot", "J", ..., "q_1", ..., "q_k"],  # if given, both "resolve_*" ignored
            "energy_max": int("maximal energy [eV]"),  # optional, if not present, all data are used
            "only_with": {"quantum": value},  # optional, if not present, all data are used
            "only_without": {"quantum": value}  # optional, if not present, all data are used
        },

        ...,

        "other molecule formula": {...}
    }

The ``molecule formula`` here needs to be a ``pyvalem`` compatible formula, but does not
need to be the same as the ExoMol formula (but generally will be, with exception
of distinguishing between isomers and different isotopologues of hydrogen).

It might be best to show an example:

.. code-block:: python

    molecules = {
        "CO": {
            "mol_slug": "CO",
            "iso_slug": "12C-16O",
            "dataset_name": "Li2015",
            "resolve_vib": ["v"]
        },
        "HCN": {
            "mol_slug": "HCN",
            "iso_slug": "1H-12C-14N",
            "dataset_name": "Harris",
            "resolve_vib": ["v1", "v2", "v3"],
            "only_with": {"iso":  "0"}
        },
        "HNC": {
            "mol_slug": "HCN",
            "iso_slug": "1H-12C-14N",
            "dataset_name": "Harris",
            "resolve_vib": ["v1", "v2", "v3"],
            "only_with": {"iso":  "1"},
            "energy_max": 5.0
        },
        "VO": {
            "mol_slug": "VO",
            "iso_slug": "51V-16O",
            "dataset_name": "VOMYT",
            "states_header": [
              "i", "E", "g_tot", "J", "tau", "+/-", "e/f", "State", "v", "Lambda", "Sigma",
              "Omega"
            ],
            "resolve_el": ["State"],
            "resolve_vib": ["v"],
            "only_without": {"State": "0"},
        },
        "HD+":{
            "mol_slug": "H2",
            "iso_slug": "1H-2H_p",
            "dataset_name": "CLT",
            ...
        },

        ...

    }

The mandatory ``"mol_slug"``, ``"iso_slug"``, ``"dataset_name"`` attributes identify
the data within the ExoMol ecosystem. The ``"resolve_el"`` and ``"resolve_vib"``
attributes need to exist as columns in the .states file for the given dataset and these
quanta will be resolved in the final lida data. All the other quanta columns in the .states
file will be lumped and averaged over. At least one of the ``"resolve_el"`` and
``"resolve_vib"`` attributes need to be specified for each molecule.

The ``"states_header"`` defines the names of all columns in the .states file for the
dataset, and needs to have the same length as the number of the .states file's columns.
Of course, the ``resolve_el | resolve_vib`` need to be subset of the ``states_header``.
The ``"states_header"`` is optional in the configuration, if not provided, the columns
are inferred from the .def file, if possible, or an error is raised. Therefore the
``states_header`` attribute serves as a workaround for inconsistent .def/.states files.

Finally, the ``"energy_max"``, ``"only_with"``, and ``"only_without"`` attributes
specify the filtering of the data, in the way that states with higher energy than
specified, states with quanta values given by ``only_without`` and all the states
*other* than with quanta values given by ``only_with``, will be completely ignored, and
their transitions will not be considered at all for calculations of the lifetimes
of the final lumped states.

This is shown on the ``"HCN"`` and ``"HNC"`` example, which produces two LIDA molecules
out of a single ExoMol dataset, each only considering states with one of the
isomers, denoted in the ExoMol dataset by the ``"iso"`` column in the .states file.

Similarly, the ``"only_without"`` parameter can be used to filter out some unphysical
or nonsensical states, such as was done for the ``"VO"`` example, which has a state
(in the .states file) with value ``"0"`` under the ``"State"`` column, which needed to
be ignored. This could be used filter out all the states (and transitions to and from)
with a certain value of some specified quanta. One application would be to filter out
all the states with some vibrational quanta with values ``"*"`` or ``-1``, which indeed
do exist in many ExoMol dataset. But this was such a common occurrence, that such
filtering is hard-coded into the algorithm and does not need to be explicitly defined
by the input configuration file.

The ``"HCN"`` isomers, as well as the ``"HD+"`` molecule are examples of the
resulting LIDA molecule formulas differing from the ExoMol molecule formulas. The
keys in the ``molecules`` dictionary specify the *LiDa* molecule names, which need to be
unique within the LiDa ecosystem, while the first three mandatory parameters for each
molecule define the path to the correct dataset within the *ExoMol* database.


``mapping_el.py`` input
-----------------------

The `Lida database <https://github.com/ExoMol/lida-web>`_ will require ``pyvalem``
compatible formulas of species, isotopologues and states. For them to be constructed,
the electronic states *resolved* for each species need to take form of valid molecular
term symbols, which ``pyvalem`` can parse. This is often the case without any
intervention, often, when ExoMol dataset resolved electronic states, there exists a
``"State"`` column in the .states file, populated with values which are in the
``pyvalem`` compatible form already. In the cases where this is not the case, however,
a mapping between the ExoMol electronic states and the LiDa (``pyvalem`` compatible)
electronic state labels needs to be provided.

The structure of this input file is made clear by the following self-explanatory
example of the ``mapping_el.py`` input file:

.. code-block:: python

    mapping_el = {
        "SiH": {
            ("a4Sigma",): "a(4SIGMA-)",
            ("B2Sigma",): "B(2SIGMA-)",
        },
        "NaH": {
            ("X",): "X(1SIGMA+)",
            ("A",): "A(1SIGMA+)"
        },
        "CN": {
            ("X",): "X(2SIGMA+)",
            ("A",): "A(2PI)",
            ("B",): "B(2SIGMA+)"
        },

        ...

    }

In theory, there might be more than a single column of the ExoMol .states file
associated with the *electronic* state, all necessary to resolve for LiDa, which is
the reason for the keys of the mapping above being tuples. In all the examples above
(and indeed in all the datasets processed so far), however, there is only a single
column in the .states file describing the electronic state, which has been considered
important to resolve for the lumped LiDa states. That is why all the ``tuple`` keys in
the ``mapping_el`` dicts have only a single value. In the example above, the ``"X"`` and
``"A"`` as keys on the ``"NaH"`` molecule actually represent all the possible values
of the ``"State"`` column on the .states file for the NaH ExoMol dataset, where the
corresponding input in the ``molecules.py`` would be
``"NaH": {..., "resolve_el": ["State"], ...}``.


Output files
============

Running the ``exomol2lida`` algorithm (described further below) for all the molecules
defined in the input files will result in the output files saved into the ``output``
folder with a similar structure as:

.. code-block:: bash

    $ tree output/

    output
    ├── ...
    |   ...
    ├── CN
    │   ├── meta_data.json
    │   ├── states_composite_map.py
    │   ├── states_data.csv
    │   ├── states_electronic.csv
    │   ├── states_electronic_raw.csv
    │   ├── states_vibrational.csv
    │   └── transitions_data.csv
    ├── CO
    │   ├── meta_data.json
    │   ├── states_composite_map.py
    │   ├── states_data.csv
    │   ├── states_vibrational.csv
    │   └── transitions_data.csv
    |   ...
    ├── ...


``metadata.json``
-----------------
This file compiles all the metadata about the processed dataset, as an example, the
following was recorded for the ``CN`` molecule:

.. code-block:: console
    $ nano output/CN/meta_data.json

    {
      "input": {
        "mol_slug": "CN",
        "iso_slug": "12C-14N",
        "dataset_name": "Trihybrid",
        "states_header": [
          "i", "E", "g_tot", "J", "unc", "tau", "g", "+/-", "e/f", "State", "v",
          "Lambda", "Sigma", "Omega", "Source", "E_Duo"
        ],
        "resolve_el": ["State"],
        "resolve_vib": ["v"]
      },
      "iso_formula": "(12C)(14N)",
      "version": 20210526,
      "mass": 26.0030740045,
      "processed_on": "2022-02-02 12:25:56.214840"
    }

The metadata file contains the original input file for the molecule exactly as was
when the dataset was processed, plus some more metadata belonging to the ExoMol dataset.
In particular, the version recorded might be used in some automatic management of
newly released ExoMol line lists and their *propagation* into the LiDa database.


``states_data.csv``
-------------------
This is a file recording the lifetimes and energies of all the newly defined *lumped*
states, generated by the ``exomol2lida`` algorithm from the original states from the
ExoMol dataset's .states file. The lifetimes are in [s] and the energies in [eV]. The
example for the CN molecule looks as follows:

.. code-block:: console

    $ nano output/CN/states_data.csv

    i,   tau,                    E
    0,   inf,                    0.00023
    1,   0.10943243874229817,    0.25345
    2,   0.057139791266185895,   0.50341
    3,   0.03905472113608493,    0.75011
    ...
    98,  1.4510310386401931e-06, 7.25698
    99,  0.33311171927799127,    7.26205
    100, 0.0001961755103469539,  7.27088

The ``i`` column gives the unique ids of the *lumped* states generated from the original
ExoMol highly resolved states.


``states_composite_map.py``
---------------------------
This file gives the mapping between the ids of the *lumped* states and the ids of the
*original* ExoMol states (from the first column of the .states file). Again, the example
for the molecule above would be

.. code-block:: console

    $ nano output/CN/states_composite_map.py

    data = {
        0: {1, 102, 203, ..., 27798, 27868, 27937},
        1: {...},
        ...
        99: {...},
        100: {101, 202, 342, ..., 5275, 5413, 5551}
    }

This mapping makes for easy checks which of the original highly resolved states belong
to each lumped state (or *composite state*).


``states_vibrational.csv``
--------------------------
This file specifies the resolved vibrational quanta per each lumped state, e.g.

.. code-block:: console

    $ nano output/CN/states_vibrational.csv

    i,   v
    0,   0
    1,   1
    2,   2
    ...
    98,  20
    99,  39
    100, 39

In this example, only a single column ``v`` exists, because input config for this dataset
would have been set as ``"CN": {..., "resolve_vib": ["v"], ...}``, but more vibrational
quanta will generally be resolved for polyatomic molecules, resulting in more columns, such
as columns ``i, v1, v2, v3`` for the ``HCN`` molecule for example.
For the datasets which do not resolve vibrational states, these files will not exist.


``states_electronic_raw.csv``, ``states_electronic.csv``
--------------------------------------------------------
These files specify the resolved electronic quanta per each lumped state. The raw file
simply gives the original values of the columns in the ``"resolve_el": ["q1", ...]``
input parameter. The second file reflects the mapping from ``input/mapping_el.py`` and
gives the ``pyvalem`` compatible molecular term symbols, such as

.. code-block:: console

    $ nano output/CN/states_electronic_raw.csv

    i,   State
    0,   X
    1,   X
    2,   X
    ...
    98,  B
    99,  X
    100, A

    $ nano output/CN/states_electronic.csv

    i,   State
    0,   X(2SIGMA+)
    1,   X(2SIGMA+)
    2,   X(2SIGMA+)
    ...
    98,  B(2SIGMA+)
    99,  X(2SIGMA+)
    100, A(2PI)

In the cases where the electronic quanta values from the ExoMol .states file are already
``pyvalem`` compatible molecular terms and no ``input/mapping_el.py`` entry is needed,
both the ``output/formula/states_electronic_raw.csv`` and
``output/formula/states_electronic.csv`` will exist and will simply be identical.
For the datasets which will not resolve electronic states, these files will not exist.
While the ``states_electronic_raw.csv`` is produced by the ``exomol2lida.process_dataset``
module, the ``states_electronic.csv`` is produced by the ``exomol2lida.postprocess_dataset``


``transitions_data.csv``
------------------------
The last output file contains the transitions between the *lumped* states with their
calculated partial lifetimes. The same example of the ``CN`` molecule gives

.. code-block:: console

    $ nano output/CN/transitions_data.csv

    i,   f,  tau_if
    1,   0,  0.10943243874229817
    2,   0,  1.2059110179290697
    2,   1,  0.059981920029654155
    ...
    100, 29, 56790.90109600513
    100, 30, 0.9100356742558192
    100, 31, 0.00029494955495862026

The ``i``, ``f`` values refer to the ids of the *lumped* states.


The ``exomol2lida`` algorithm
=============================

In this section, the main state-lumping algorithm is briefly described verbally. The
algorithm follows these steps:

1.  Filter the original states from the .states file. This is where the input parameters
    ``energy_max``, ``only_with`` and ``only_without`` come in, see the *inputs* section.
    All the original states which do not survive this filtering will be completely
    ignored for the further calculations.

2.  Define the lumped states, create mapping between the original state ids and the lumps.
    Each lumped state is uniquely identified by the set of distinct values of the columns
    defined by the ``resolve_el`` and ``resolve_vib`` in the input file. In the example
    case of ``{..., "resolve_vib": ["v1", "v2", "v3"], "resolve_el": ["State"], ...}``,
    each lumped state is a collection of distinct values of the ``State, v1, v2, v3``
    columns from the ExoMol .states file. Each lump will consist of a number of original
    ExoMol states characterised with the same resolved quanta, but generally with different
    values under *other* columns, and other quanta, such as "+/-", "J", etc. A mapping
    is created between the lumped indices ``i`` and the original states indices ``i_orig``,
    ``i -> {i_orig}``

3.  Assign energies to the lumped states. Within each lump, the lowest-J states are
    identified and the energy of the lump is set to be the average of the original
    resolved states with the lowest J number, weighted by the ``g_tot`` total
    degeneracies.

4.  Lump the transitions and calculate the partial lifetimes of the lumped transitions.
    First, all the in-lump transitions are ignored and not used in any way in the
    calculations. Also, any transitions from and to a non-existing lump (such as to
    and from the original states that did not survive the filtering within the state
    lumping process, either too high energy, or regarding the ``only_with``, ``only_without``
    parameters) are completely ignored.
    If ``i``, ``f`` are the indices of the lumped states and ``i_orig``, ``f_orig`` are
    indices of the filtered original states from the .trans file, the partial lifetimes
    of each *lumped* transition ``i -> f`` is calculated as

    .. math::

        \tau_{i \to f} = \mathrm{avg}_{f_\mathrm{orig} \in f} (\tau_{i \to f_\mathrm{orig}}),

        \frac{1}{\tau_{i \to f_\mathrm{orig}}} = \sum_{i_\mathrm{orig} \in i} A_{i_\mathrm{orig} \to f_\mathrm{orig}}.

    Here, ``A`` refers to the einstein coefficients from the original .trans file.

5.  Calculate the total lifetimes of the lumped states, as

    .. math::

        \frac{1}{\tau_i} = \sum_{f} \tau_{i \to f}.

The algorithm described above is implemented in the ``exomol2lida.process_dataset``
module inside the ``DataProcessor`` class. The class is well documented and the
docstrings and the in-line comments serve as the best source of documentation and
usage. A the end of the processing workflow, most of the output files (discussed above)
are created. Apart the ``DataProcessor``, there is also the
``exomol2lida.postprocess_dataset.DatasetPostProcessor`` class, which handles the
conversion between electronic states as are in the ExoMol database, and ``pyvalem``
compatible molecular term symbol labels expected by the LiDa database.


The top-level scripts
=====================
Two top-level script exist which trigger the whole workflow. Assuming there exist an
input entry for molecule, e.g. ``"H2O"`` in the ``input/molecules.py`` file, the
calculation of the LiDa data for this molecule can be run by

.. code-block:: bash

    python process.py H2O

Similarly, the data can be post-processed (after processing finished) aby running

.. code-block:: bash

    python postprocess.py H2O

This assumes that if electronic states are resolved for this molecule, they either
can be parsed automatically by the ``DatasetPostProcessor``, or the
``input/mapping_el.py`` input file has defined the mapping to the valid molecular term
symbols.

Both can be run together by

.. code-block:: bash

    python process.py H2O --postprocess

If anything goes wrong, hopefully the error message will give a hint on what happened.
The processing and post-processing workflow can also be run on all the molecules found
in the input files, by running

.. code-block:: bash

    python process.py all --postprocess


The known issues
================

This section discusses some of the known issues of the codebase and ideas for further
development.

-   A more powerful state filtering system is needed. As an example, the H3+ dataset
    contains the ground state with (v1, v2) = (0, 0), which does not physically exist,
    therefore does not have energy defined. The ``exomol2lida`` code runs fine, but
    the lida database code breaks, as the energy of the (0, 0) state is set to ``NaN``
    by the ``exomol2lida``, which cannot be dealt with by the lida code (different repo).
    What is needed is the way to specify something like
    ``"H3+": {..., "only_without": {("v1", "v2"): (0, 0)}, ...}``. This is currently
    not supported, and the option of ``"only_without": {"v1": 0, "v2": 0}``, which is
    supported, would also filter out states with vibrational quanta (0, 1), (0, 2), ...,
    (1, 0), (2, 0), ...

-   In the case of LiDa data built from the multiple isomers, such as the case of
    HCN, built from ``"HCN": {..., "only_with": {"iso": 0}, ...}``, and
    HNC, built from ``"HNC": {..., "only_with": {"iso": 1}, ...}``, both LiDa datasets
    are built from a single ExoMol dataset, under the same molecule slug and isotopologue
    slug. The ``exomol2lida`` code runs fine, but problems are created for the lida code
    (different repo), because both isomers have the same isotopologue formula saved in
    the ``meta_data.json`` output, specifically ``"(1H)(12C)(14N)"``. This is used by
    the LiDa database code and there cannot exist two ``Isotopologue`` instances with
    the same formula. What is needed is something like

    .. code-block:: python

        molecules = {

            ...

            "HNC": {
                "mol_slug": "HCN",
                "iso_slug": "1H-12C-14N",
                "dataset_name": "Harris",
                "resolve_vib": ["v1", "v2", "v3"],
                "only_with": {"iso":  "1"},
                "surrogate_iso_formula": "(1H)(14N)(12C)"
            },

            ...

        }

    and change in the processing code, which would save the surrogate formula into the
    output ``meta_data.json`` file.

-   The process -> postprocess workflow as currently implemented works fine for the case
    where there is a 1-to-1 relationship between the original state labels and the needed
    ``pyvalem`` compatible labels defined in the ``input/mapping_el.py``. Unfortunatelly
    there are cases of many-to-1 relationships, such as in the case of the VO molecule, 
    for which the mapping looks like
    
    .. code-block:: python
    
        mapping_el = {
            ...
            "VO": {
                ("b2Gamma",): "b(2GAMMA)",
                ("X",): "X(4SIGMA-)",
                ("a2",): "a(2SIGMA-)",
                ("Ap",): "A'(4PHI)",
                ("A",): "A(4PI)",
                ("b2",): "b(2GAMMA)",
                ("c2",): "c(2DELTA)",
                ("d2",): "d(2SIGMA+)",
                ("B",): "B(4PI)",
                ("e2",): "e(2PHI)",
                ("C",): "C(4SIGMA-)",
                ("f2",): "f(2PI)",
                ("D",): "D(4DELTA)",
                ("g2",): "g(2PI)",
            },
            ...
        }
    
    As we can see, the ``"b2Gamma"`` and ``"b2"`` original states both need to be mapped
    into a single ``pyvalem`` compatible ``"b(2GAMMA)"`` state string.    
    This breaks the code unfortunately, as the lumped states are created using the original
    state strings
    and in the post-processing we end up with two lumped states which should have been
    a single one. To fix this, the electronic state label substitution for the ``pyvalem``
    compatible strings needs to happen inside the lumping procedure within the processing.
    This would than shift the post-processing workflow to the beginning of the processing
    workflow - the state re-labeling will happen inside processing and post-processing will
    not exist anymore. This needs to be implemented, as currently VO molecule fails in 
    the post-processing step due to the reasons described.

-   Some datasets show very high lifetimes after processing, which are surely unphysical.
    I have not looked into this in detail, but it does deserve some attention, to decide
    if the ExoMol data are incorrect or if there is a problem with the algorithm. An example
    of this is the SiH2 molecule, where all the states have lifetimes between 1e3 - 1e14 s.
    But as other molecules have reasonable lifetimes, it is more probable that the .trans
    file for this ExoMol dataset is in some way faulty, like incorrect units of einstein
    coefficients, of swapped columns, etc. Investigation is needed, as well as some
    safeguards against this happening.

-   We get quite a lot of transitions from lower-energy states to higher-energy states.
    This is understood, and it is the result of how the states are lumped, as each lump
    includes states of the whole range of J numbers, but energy of the lump is calculated
    only regarding the lowest-energy J. This is just to draw attention to the issue.

-   In some cases, we see ground states with finite lifetimes. This should probably never
    happen, and it can signal some possible problems with the algorithm (or inconsistent
    .trans files to begin with, where there exist transitions from the ground states).
    Further investigation is needed, examples of molecules with finite lifetimes of
    the ground states are e.g. CaO, H2, NaCl, and others.

-   Another non-bug is that we see some high-energy states with very high lifetimes,
    caused by the .trans file not being complete and missing some radiation channels
    for the very high energy states. This will often be a problem, because the .trans
    files must be truncated somewhere. Question is where should the LiDa states and
    transitions truncated, and how to detect incomplete transitions, so the lumped
    transition and its initial state could be simply ignored as incomplete and therefore
    with compromised data. One option could be truncate LiDa states by energy, but
    question is where to set the threshold.

-   The fact is that there probably is a strong need for some truncation. The algorithm
    runs very slowly on the big molecules. Fact is that only molecules of manageable
    size have been so far processed, and the largest molecules will probably take way
    too long to be done by the algorithm as it is. The lumped states and transitions
    probably will have to be truncated to limit the computational load, as well as
    the size of the lumped dataset. Another thing is that the lifetimes and transitions
    are so far lumped over all the J numbers, which might not be feasible for the large
    molecules, and instead a reference J could be picked and the data calculated only
    for that single J.

-   Apart from the fact that some molecules are simply too large for the algorithm,
    there appears to be a problem with the computational cost, where state lumping and
    transitions lumping algorithm takes more and more time with each chunk of the
    dataset data read from the exoweb server for a single molecule. For some reason,
    more data is processed already, more time it takes to process the remaining data,
    which should not be the case. Probably some profiling and optimization is needed,
    I did not have the time to pinpoint the issue, but I'm fairly certain that the algo
    could be optimized.
