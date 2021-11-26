import warnings
from collections import namedtuple

from utils import parse_exomol_line

ExomolDef = namedtuple(
    'ExomolDef',
    ['id', 'iso_formula', 'iso_slug', 'dataset_name', 'version', 'inchi_key',
     'isotopes', 'mass', 'irreducible_representations', 'max_temp',
     'num_pressure_broadeners', 'dipole_availability', 'num_cross_sections',
     'num_k_coefficients', 'lifetime_availability', 'lande_factor_availability',
     'num_states', 'quanta_cases', 'quanta', 'num_transitions', 'num_trans_files',
     'max_wavenumber', 'high_energy_complete']
)

Isotope = namedtuple()

IrreducibleRepresentation = namedtuple()

QuantumCase = namedtuple()

Quantum = namedtuple()


def _parse_exomol_def(exomol_def_raw):
    lines = exomol_def_raw.split('\n')
    n_orig = len(lines)


