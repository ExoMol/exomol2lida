import sys

from exomol2lida.process_dataset import DatasetProcessor


def main():
    mol_formula = sys.argv[1]
    mol_processor = DatasetProcessor(mol_formula)
    if "--print-def" in sys.argv:
        print(mol_processor.molecule_input.def_parser.raw_text)
    mol_processor.process()


if __name__ == "__main__":
    main()
