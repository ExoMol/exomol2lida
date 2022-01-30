import sys

from exomole.exceptions import DefParseError

from exomol2lida.process_dataset import DatasetProcessor
from exomol2lida.exceptions import MoleculeInputError
from input.molecules import data as mol_formulas


def process_molecule(mol_formula, include_original_lifetimes=True):
    mol_processor = DatasetProcessor(mol_formula)
    mol_processor.process(include_original_lifetimes=include_original_lifetimes)


if __name__ == "__main__":
    allowed_args = {"--include-tau"}
    assert set(sys.argv[1:]).issubset(allowed_args)
    # read all the molecule formulas from the input file:
    for mf in mol_formulas:
        try:
            process_molecule(mf, "--include-tau" in sys.argv)
        except (MoleculeInputError, FileExistsError, DefParseError) as e:
            print(f"{mf} ABORTED!")
            print(f"{type(e).__name__}: {e}")
        print()
