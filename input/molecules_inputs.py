from pathlib import Path
import json

from config.config import EXOMOL_DATA_DIR
from exomol2lida.exomol.parse_def import parse_exomol_def, ExomolDefParseError

with open(Path(__file__).parent.joinpath('molecules.json'), 'r') as fp:
    inputs_dict = json.load(fp)


class MoleculeInputError(Exception):
    pass


class MoleculeInput:
    def __init__(self, molecule_formula, **kwargs):
        self.formula = molecule_formula
        try:
            self.mol_slug = kwargs['mol_slug']
            self.iso_slug = kwargs['iso_slug']
            self.dataset_name = kwargs['dataset_name']
        except KeyError:
            raise MoleculeInputError(
                f'Input data for {molecule_formula} missing some of the mandatory '
                f'attributes ("mol_slug", "iso_slug", "dataset_name")')
        for attr, val in kwargs.items():
            setattr(self, attr, val)

        mol_root = EXOMOL_DATA_DIR / self.mol_slug
        if not mol_root.is_dir():
            raise MoleculeInputError(f'The molecule directory not found: {mol_root}')
        iso_root = mol_root / self.iso_slug
        if not iso_root.is_dir():
            raise MoleculeInputError(
                f'The isotopologue directory not found: {iso_root}')
        ds_root = iso_root / self.dataset_name
        if not ds_root.is_dir():
            raise MoleculeInputError(
                f'The dataset directory not found: {ds_root}')

        file_name_stem = f'{self.iso_slug}__{self.dataset_name}'

        self.def_path = ds_root / f'{file_name_stem}.def'
        if not self.def_path.is_file():
            raise MoleculeInputError(f'The .def file not found under {self.def_path}')

        # TODO: uncomment before running on the server!
        # self.states_path = ds_root / f'{file_name_stem}.states.bz2'
        # if not self.states_path.is_file():
        #     raise MoleculeInputError(
        #         f'The .states file not found under {self.states_path}')
        # trans_wc = f'{file_name_stem}__*.trans.bz2'
        # self.trans_paths = sorted(ds_root.glob(trans_wc))
        # if not len(self.trans_paths):
        #     raise MoleculeInputError(
        #         f'No .trans files found under {ds_root / trans_wc}')

        self.parsed_def = parse_exomol_def(self.def_path)


def validate_all_inputs():
    # total counts:
    clear, with_error = 0, 0
    for formula, input_dict in inputs_dict.items():
        try:
            MoleculeInput(formula, **input_dict)
        except ExomolDefParseError as e:
            print(f'{formula}: {e}')
            with_error += 1
        finally:
            clear += 1
    print()
    print(f'Cleared: {clear}')
    print(f'Raised errors: {with_error}')


def get_all_inputs():
    pass


if __name__ == '__main__':
    validate_all_inputs()
