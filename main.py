from exomol2lida.process_dataset import DatasetProcessor


def main():
    mol_processor = DatasetProcessor("HCN")
    mol_processor.states_chunk_size = 10000
    mol_processor.trans_chunk_size = 100000
    mol_processor.lump_states()
    mol_processor.lump_transitions()


if __name__ == "__main__":
    main()
