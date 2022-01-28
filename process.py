import sys

from exomol2lida.process_dataset import DatasetProcessor

if __name__ == "__main__":
    include_original_lifetimes = "-tau" in sys.argv
    mol_formula = sys.argv[1]
    mol_processor = DatasetProcessor(mol_formula)
    mol_processor.process(include_original_lifetimes=include_original_lifetimes)
