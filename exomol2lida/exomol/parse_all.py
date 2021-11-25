import warnings
from collections import namedtuple
from pathlib import Path

import requests

res_dir = Path(__file__).parent.absolute().resolve()

ExomolAll = namedtuple(
    'ExomolAll', 'id version num_molecules num_isotopologues num_datasets molecules'
)

Molecule = namedtuple(
    'Molecule', 'num_names names formula num_isotopologues isotopologues'
)

Isotopologue = namedtuple(
    'Isotopologue', 'inchi_key iso_slug iso_formula dataset_name version'
)


def _get_exomol_all_raw(path=None):
    """Get the raw text of the exomol.all file.

    If called with a valid path (e.g. on the ExoWeb server or on a local test repo),
    the file under the path is read and returned, if called with None (default),
    the file is requested over https under the relevant URL (hardcoded).

    Parameters
    ----------
    path : str | Path | None
        Path leading to the exomol.all file. If None is passed, the function requests
        the file from the url 'https://www.exomol.com/db/exomol.all'.
    Returns
    -------
    str
        Raw text of the exomol.all file.

    Examples
    --------
    >>> _get_exomol_all_raw('foo')
    Traceback (most recent call last):
      ...
    FileNotFoundError: [Errno 2] No such file or directory: 'foo'
    >>> exomol_all_raw = _get_exomol_all_raw(path=None)
    >>> type(exomol_all_raw)
    <class 'str'>
    """
    if path is None:
        return requests.get('https://www.exomol.com/db/exomol.all').text
    else:
        with open(path, 'r') as fp:
            return fp.read()


def _parse_exomol_all_raw(exomol_all_raw):
    """Parse the raw text of the exomol.all file.

    Parse the text and construct the ExomolAll object instance holding all
    the data from exomol.all in a nice nested data structure of named tuples.

    Parameters
    ----------
    exomol_all_raw : str
        Raw text of the exomol.all file. Can be obtained by calling
        _get_exomol_all_raw function.

    Returns
    -------
    ExomolAll
        Named tuple holding all the (now structured) data. See the ExomolAll
        namedtuple instance.
    """

    def parse_line(expected_comment):
        """Parse the top line among the lines (defined outside in the closure).
        Changes the lines instance as an externality (by popping the first
        line)!

        Parameters
        ----------
        expected_comment : str

        Returns
        -------
        str
        """
        while True:
            line = lines.pop(0)
            line_num = n - len(lines)
            if line:
                break
            else:
                warnings.warn(f'Empty line detected on line {line_num}!')
        try:
            val, comment = line.split('# ')
        except ValueError:
            raise AssertionError(f'Inconsistency detected on line {line_num}!')
        assert comment == expected_comment, \
            f'Inconsistent comment detected on line {line_num}!'
        return val.strip()

    lines = exomol_all_raw.split('\n')
    n = len(lines)

    exomol_id = parse_line('ID')

    all_version = parse_line('Version number with format YYYYMMDD')

    num_molecules = parse_line('Number of molecules in the database')
    num_molecules = int(num_molecules)
    molecules = {}

    num_all_isotopologues = parse_line('Number of isotopologues in the database')
    num_all_isotopologues = int(num_all_isotopologues)
    all_isotopologues = []

    num_all_datasets = parse_line('Number of datasets in the database')
    num_all_datasets = int(num_all_datasets)
    all_datasets = set()

    molecules_with_duplicate_isotopologues = []

    # loop over molecules:
    for _ in range(num_molecules):
        num_names = parse_line('Number of molecule names listed')
        num_names = int(num_names)
        names = []

        # loop over the molecule names:
        for __ in range(num_names):
            name = parse_line('Name of the molecule')
            names.append(name)

        assert num_names == len(names)

        formula = parse_line('Molecule chemical formula')

        num_isotopologues = parse_line('Number of isotopologues considered')
        num_isotopologues = int(num_isotopologues)
        isotopologues = {}

        # loop over the isotopologues:
        for __ in range(num_isotopologues):
            inchi_key = parse_line('Inchi key of isotopologue')
            iso_slug = parse_line('Iso-slug')
            iso_formula = parse_line('IsoFormula')
            dataset_name = parse_line('Isotopologue dataset name')
            version = parse_line('Version number with format YYYYMMDD')

            isotopologue = Isotopologue(
                inchi_key, iso_slug, iso_formula, dataset_name, version
            )

            if iso_formula not in isotopologues:
                isotopologues[iso_formula] = isotopologue
            else:
                warnings.warn(
                    f'{formula} lists more than one dataset for isotopologue '
                    f'{iso_formula}: Ignoring {dataset_name}'
                )

            all_datasets.add(dataset_name)
            all_isotopologues.append(isotopologue)

        # check if all the isotopologues are in fact different
        # (only a single dataset should be recommended):
        if len(isotopologues) != len(set(
                isotopologue.iso_formula
                for isotopologue in isotopologues.values()
        )):
            molecules_with_duplicate_isotopologues.append(formula)

        molecule = Molecule(
            num_names, names, formula, num_isotopologues, isotopologues
        )
        molecules[formula] = molecule

    # final assertions:
    if len(molecules_with_duplicate_isotopologues):
        warnings.warn(
            f'Molecules with duplicate isotopologues detected: '
            f'{molecules_with_duplicate_isotopologues}'
        )

    assert num_molecules == len(molecules)

    if num_all_isotopologues != len(all_isotopologues):
        warnings.warn(
            f'Number of isotopologues stated ({num_all_isotopologues}) does not '
            f'match the actual number ({len(all_isotopologues)})!'
        )

    if num_all_datasets != len(all_datasets):
        warnings.warn(
            f'Number of datasets stated ({num_all_datasets}) does not match the '
            f'actual number ({len(all_datasets)})!'
        )

    return ExomolAll(
        exomol_id, all_version, num_molecules, num_all_isotopologues,
        num_all_datasets, molecules
    )


def parse_exomol_all(path=None):
    """Parses the exomol.all file.

    Creates a structured named tuple instance of ExomolAll.
    ExomolAll.molecules is a dict filled with Molecule instances and for
    each, Molecule.isotopologues is a dict filled with Isotopologue instances
    containing all the lower-level data.

    Parameters
    ----------
    path : str | Path | None
        Path to the exomol.all. If None is passed (default), the exomol.all file
        gets requested over the ExoMol API.

    Returns
    -------
    ExomolAll
        Named tuple containing structured data of the exomol.all file.

    Examples
    --------
    >>> exomol_all_instance = parse_exomol_all(path=None)
    >>> all_molecules = exomol_all_instance.molecules
    >>> type(all_molecules)
    <class 'dict'>
    >>> water_molecule = all_molecules['H2O']
    >>> water_isotopologue = water_molecule.isotopologues['(1H)2(16O)']
    >>> water_isotopologue.iso_formula
    '(1H)2(16O)'
    >>> water_isotopologue.iso_slug
    '1H2-16O'
    """

    exomol_all_raw = _get_exomol_all_raw(path)
    # print(exomol_all_raw)
    exomol_all = _parse_exomol_all_raw(exomol_all_raw)
    return exomol_all
