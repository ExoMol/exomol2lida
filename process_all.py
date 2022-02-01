import sys

from exomole.exceptions import DefParseError

from exomol2lida.process_dataset import DatasetProcessor
from exomol2lida.postprocess_dataset import DatasetPostProcessor
from exomol2lida.exceptions import MoleculeInputError, DatasetPostProcessorError
from input.molecules import data as mol_formulas


def process_molecule(mol_formula, include_original_lifetimes=False):
    mol_processor = DatasetProcessor(mol_formula)
    mol_processor.process(include_original_lifetimes=include_original_lifetimes)


def postprocess_molecule(mol_formula):
    mol_postprocessor = DatasetPostProcessor(mol_formula)
    mol_postprocessor.postprocess()


if __name__ == "__main__":
    allowed_args = {"--include-tau", "--postprocess"}
    assert set(sys.argv[1:]).issubset(allowed_args)

    for mf in mol_formulas:
        print()
        try:
            process_molecule(mf, "--include-tau" in sys.argv)
        except (MoleculeInputError, DefParseError) as e:
            print(f"{mf} PROCESSING ABORTED: {type(e).__name__}: {e}")
            continue
        except FileExistsError as e:
            print(f"{mf} PROCESSED ALREADY: {type(e).__name__}: {e}")

        if "--postprocess" in sys.argv:
            try:
                postprocess_molecule(mf)
            except DatasetPostProcessorError as e:
                print(f"{mf} POST-PROCESSING ABORTED: {type(e).__name__}: {e}")
    print()
