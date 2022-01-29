import sys

from exomol2lida.process_dataset import DatasetProcessor


def process(mol_formula, include_original_lifetimes):
    mol_processor = DatasetProcessor(mol_formula)
    mol_processor.process(include_original_lifetimes=include_original_lifetimes)


if __name__ == "__main__":
    process(sys.argv[1], "-tau" in sys.argv)
