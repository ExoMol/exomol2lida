import warnings
from collections import namedtuple
from pathlib import Path

import requests

from exomol2lida.exomol.utils import parse_exomol_line

file_dir = Path(__file__).parent.resolve()
project_dir = file_dir.parent.parent
test_resources = project_dir.joinpath('test', 'resources')

ExomolAll = namedtuple(
    'ExomolAll',
    'raw_text id version num_molecules num_isotopologues num_datasets molecules'
)

Molecule = namedtuple('Molecule', 'names formula isotopologues')

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

    lines = exomol_all_raw.split('\n')
    n_orig = len(lines)

    def parse_line(comment, val_type=None):
        return parse_exomol_line(
            lines, n_orig, comment, file_name='exomol.all', val_type=val_type,
            raise_warnings=True)

    kwargs = {
        'raw_text': exomol_all_raw, 'id': parse_line('ID'),
        'version': parse_line('Version number with format YYYYMMDD', int),
        'num_molecules': parse_line('Number of molecules in the database', int),
        'num_isotopologues': parse_line('Number of isotopologues in the database', int),
        'num_datasets': parse_line('Number of datasets in the database', int),
        'molecules': {}
    }

    # I shall verify the numbers of isotopologues and datasets by keeping track:
    all_isotopologues = []
    all_datasets = set()
    molecules_with_duplicate_isotopologues = []

    # loop over molecules:
    for _ in range(kwargs['num_molecules']):
        mol_kwargs = {
            'names': [],
            'isotopologues': {}
        }

        num_names = parse_line('Number of molecule names listed', int)

        # loop over the molecule names:
        for __ in range(num_names):
            mol_kwargs['names'].append(parse_line('Name of the molecule'))

        mol_kwargs['formula'] = parse_line('Molecule chemical formula')
        num_isotopologues = parse_line('Number of isotopologues considered', int)

        # loop over the isotopologues:
        for __ in range(num_isotopologues):
            iso_kwargs = {
                'inchi_key': parse_line('Inchi key of isotopologue'),
                'iso_slug': parse_line('Iso-slug'),
                'iso_formula': parse_line('IsoFormula'),
                'dataset_name': parse_line('Isotopologue dataset name'),
                'version': parse_line('Version number with format YYYYMMDD', int),
            }

            isotopologue = Isotopologue(**iso_kwargs)
            if iso_kwargs['iso_formula'] not in mol_kwargs['isotopologues']:
                mol_kwargs['isotopologues'][iso_kwargs['iso_formula']] = isotopologue
            else:
                warnings.warn(
                    f'{mol_kwargs["formula"]} lists more than one dataset for '
                    f'isotopologue {iso_kwargs["iso_formula"]}: '
                    f'Ignoring {iso_kwargs["dataset_name"]}'
                )
                molecules_with_duplicate_isotopologues.append(mol_kwargs['formula'])

            all_datasets.add(iso_kwargs['dataset_name'])
            all_isotopologues.append(isotopologue)

        # molecule slug is not present in the exomol.all data!
        kwargs['molecules'][mol_kwargs['formula']] = Molecule(**mol_kwargs)

    if kwargs['num_isotopologues'] != len(all_isotopologues):
        warnings.warn(
            f'Number of isotopologues stated ({kwargs["num_isotopologues"]}) does not '
            f'match the actual number ({len(all_isotopologues)})!'
        )

    if kwargs['num_datasets'] != len(all_datasets):
        warnings.warn(
            f'Number of datasets stated ({kwargs["num_datasets"]}) does not match the '
            f'actual number ({len(all_datasets)})!'
        )

    return ExomolAll(**kwargs)


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
    >>> exomol_all_instance = parse_exomol_all(path=test_resources / 'exomol.all')
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
    exomol_all = _parse_exomol_all_raw(exomol_all_raw)
    return exomol_all
