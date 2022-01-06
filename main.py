from time import time

from exomol2lida.read_inputs import get_input
from exomol2lida.process_dataset import DatasetProcessor


mol_input = get_input("HCN", input_json_path="input/molecules.json")

mol_processor = DatasetProcessor(mol_input)

mol_processor.lump_states()
mol_processor.lump_transitions()

print('\n\n')
print(mol_processor.lumped_states)
print('\n\n')
print(mol_processor.lumped_transitions)
