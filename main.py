from exomol2lida.process_dataset import DatasetProcessor


def main():
    mol_processor = DatasetProcessor("HCN")

    mol_processor.lump_states()
    mol_processor.lump_transitions()

    print("\n\n")
    print(mol_processor.lumped_states)
    print("\n\n")
    print(mol_processor.lumped_transitions)


if __name__ == "__main__":
    main()
