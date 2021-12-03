import warnings
from collections import namedtuple

import requests
from pyvalem.formula import Formula

from utils import parse_exomol_line

ExomolDefBase = namedtuple(
    'ExomolDefBase',
    ['id', 'iso_formula', 'iso_slug', 'dataset_name', 'version', 'inchi_key',
     'isotopes', 'mass', 'symmetry_group', 'irreducible_representations', 'max_temp',
     'num_pressure_broadeners', 'dipole_availability', 'num_cross_sections',
     'num_k_coefficients', 'lifetime_availability', 'lande_factor_availability',
     'num_states', 'quanta_cases', 'quanta', 'num_transitions', 'num_trans_files',
     'max_wavenumber', 'high_energy_complete']
)

Isotope = namedtuple(
    'Isotope', 'number element_symbol'
)

IrreducibleRepresentation = namedtuple(
    'IrreducibleRepresentation', 'id label nuclear_spin_degeneracy'
)

QuantumCase = namedtuple(
    'QuantumCase', 'label'
)

Quantum = namedtuple(
    'Quantum', 'label format description'
)


class ExomolDef(ExomolDefBase):
    @property
    def quanta_labels(self):
        return [q.label for q in self.quanta]


def _get_exomol_def_raw(
        path=None, molecule_slug=None, isotopologue_slug=None, dataset_name=None
):
    """Get the raw text of a .def file.

    If called with a valid path (e.g. on the ExoWeb server or on a local test repo),
    the file under the path is read and returned, if called with None (default),
    the file is requested over https under the relevant URL via the ExoMol public
    API. In this case, molecule_slug, isotopologue_slug, and dataset_name must be
    supplied.

    Parameters
    ----------
    path : str | Path | None
        Path leading to the exomol.all file. If None is passed, the function requests
        the file from the url
        'https://www.exomol.com/db/<mol>/<iso>/<ds>/<iso>__<ds>.def'.
        In those cases, all the mol, iso and ds must be passed!
    molecule_slug : str
    isotopologue_slug : str
    dataset_name : str

    Returns
    -------
    str
        Raw text of the relevant .def file.
    """
    if path is None:
        if not all([molecule_slug, isotopologue_slug, dataset_name]):
            raise ValueError('If path not specified, you must pass all the other '
                             'parameters!')
        url = f'https://www.exomol.com/db/{molecule_slug}/{isotopologue_slug}/' \
              f'{dataset_name}/{isotopologue_slug}__{dataset_name}.def'
        return requests.get(url).text
    else:
        with open(path, 'r') as fp:
            return fp.read()


def _parse_exomol_def_raw(exomol_def_raw):
    """Parse the raw text of the .def file.

    Parse the text and construct the ExomolDef object instance holding all
    the data from the .def file in a nice nested data structure of named tuples.

    Parameters
    ----------
    exomol_def_raw : str
        Raw text of the .def file. Can be obtained by calling
        _get_exomol_def_raw function.

    Returns
    -------
    ExomolDef
        Custom named tuple holding all the (now structured) data. See the
        ExomolDefBase namedtuple instance. This class also defines additional
        functionality on top of the ExomolDefBase, such as quanta_labels attribute.
    """
    lines = exomol_def_raw.split('\n')
    n_orig = len(lines)

    def parse_line(expected_comment):
        return parse_exomol_line(lines, n_orig, expected_comment=expected_comment)

    kwargs = {
        'id': parse_line('ID'),
        'iso_formula': parse_line('IsoFormula'),
        'iso_slug': parse_line('Iso-slug'),
        'dataset_name': parse_line('Isotopologue dataset name'),
        'version': int(parse_line('Version number with format YYYYMMDD')),
        'inchi_key': parse_line('Inchi key of molecule'),
        'isotopes': []
    }
    num_atoms = int(parse_line('Number of atoms'))
    if len(Formula(kwargs['iso_formula']).atoms) != num_atoms:
        warnings.warn(f'Incorrect number of atoms in {kwargs["iso_slug"]}__'
                      f'{kwargs["dataset_name"]}.def!')
        num_atoms = len(Formula(kwargs['iso_formula']).atoms)
    for i in range(num_atoms):
        isotope_kwargs = {
            'number': int(parse_line(f'Isotope number {i + 1}')),
            'element_symbol': parse_line(f'Element symbol {i + 1}')
        }
        isotope = Isotope(**isotope_kwargs)
        kwargs['isotopes'].append(isotope)
    iso_mass_amu = float(parse_line('Isotopologue mass (Da) and (kg)').split()[0])
    kwargs.update({
        'mass': iso_mass_amu,
        'symmetry_group': parse_line('Symmetry group'),
        'irreducible_representations': []
    })
    num_irreducible_representations = int(
        parse_line('Number of irreducible representations'))
    for _ in range(num_irreducible_representations):
        ir_kwargs = {
            'id': int(parse_line('Irreducible representation ID')),
            'label': parse_line('Irreducible representation label'),
            'nuclear_spin_degeneracy': int(parse_line('Nuclear spin degeneracy'))
        }
        ir = IrreducibleRepresentation(**ir_kwargs)
        kwargs['irreducible_representations'].append(ir)
    kwargs.update({
        'max_temp': float(parse_line('Maximum temperature of linelist')),
        'num_pressure_broadeners': int(
            parse_line('No. of pressure broadeners available')),
        'dipole_availability': bool(parse_line('Dipole availability (1=yes, 0=no)')),
        'num_cross_sections': int(parse_line('No. of cross section files available')),
        'num_k_coefficients': int(parse_line('No. of k-coefficient files available')),
        'lifetime_availability': bool(
            parse_line('Lifetime availability (1=yes, 0=no)')),
        'lande_factor_availability': bool(
            parse_line('Lande g-factor availability (1=yes, 0=no)')),
        'num_states': int(parse_line('No. of states in .states file')),
        'quanta_cases': [],
        'quanta': []
    })
    num_quanta_cases = int(parse_line('No. of quanta cases'))
    for _ in range(num_quanta_cases):
        kwargs['quanta_cases'].append(
            QuantumCase(label=parse_line('Quantum case label')))
    num_quanta = int(parse_line('No. of quanta defined'))
    for i in range(num_quanta):
        q_kwargs = {
            'label': parse_line(f'Quantum label {i + 1}'),
            'format': parse_line(f'Format quantum label {i + 1}'),
            'description': parse_line(f'Description quantum label {i + 1}')
        }
        quantum = Quantum(**q_kwargs)
        kwargs['quanta'].append(quantum)
    kwargs.update({
        'num_transitions': parse_line('Total number of transitions'),
        'num_trans_files': parse_line('No. of transition files'),
        'max_wavenumber': parse_line('Maximum wavenumber (in cm-1)'),
        'high_energy_complete': parse_line(
            'Higher energy with complete set of transitions (in cm-1)'),
    })

    return ExomolDef(**kwargs)


def parse_exomol_def(
        path=None, molecule_slug=None, isotopologue_slug=None, dataset_name=None
):
    """Parse the .def file.

    Parse the text and construct the ExomolDef object instance holding all
    the data from the .def file in a nice nested data structure of named tuples.
    If called with a valid path (e.g. on the ExoWeb server or on a local test repo),
    the file under the path parsed, if called with None (default),
    the file is requested over https under the relevant URL via the ExoMol public
    API. In this case, molecule_slug, isotopologue_slug, and dataset_name must be
    all, supplied or a ValueError is raised.

    Parameters
    ----------
    path : str | Path | None
        Path leading to the exomol.all file. If None is passed, the function requests
        the file from the url
        'https://www.exomol.com/db/<mol>/<iso>/<ds>/<iso>__<ds>.def'.
        In those cases, all the mol, iso and ds must be passed!
    molecule_slug : str
    isotopologue_slug : str
    dataset_name : str

    Returns
    -------
    ExomolDef
        Custom named tuple holding all the (now structured) data. See the
        ExomolDefBase namedtuple instance. This class also defines additional
        functionality on top of the ExomolDefBase, such as quanta_labels attribute.

    Examples
    --------
    >>> parse_exomol_def(path='foo.def')
    Traceback (most recent call last):
      ...
    FileNotFoundError: [Errno 2] No such file or directory: 'foo.def'
    >>> exomol_def = parse_exomol_def(molecule_slug='H2_p',
    ...                               isotopologue_slug='1H-2H_p',
    ...                               dataset_name='CLT')
    >>> type(exomol_def)
    <class 'parse_def.ExomolDef'>
    >>> exomol_def.id
    'EXOMOL.def'
    >>> exomol_def.dataset_name
    'CLT'
    >>> type(exomol_def.isotopes[0])
    <class 'parse_def.Isotope'>
    >>> exomol_def.quanta_labels
    ['v']
    >>> parse_exomol_def(molecule_slug='foo')
    Traceback (most recent call last):
      ...
    ValueError: If path not specified, you must pass all the other parameters!
    """
    raw_text = _get_exomol_def_raw(
        path=path, molecule_slug=molecule_slug, isotopologue_slug=isotopologue_slug,
        dataset_name=dataset_name)
    return _parse_exomol_def_raw(raw_text)
