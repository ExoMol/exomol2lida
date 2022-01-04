from time import time

from exomol2lida.read_inputs import get_input
from exomol2lida.process_dataset import DatasetProcessor


mol_input = get_input("HCN", input_json_path="input/molecules.json")
print(f"states header : {mol_input.states_header}")
mol_processor = DatasetProcessor(mol_input)

t0 = time()
mol_processor.lump_states()
print(f"Process time: {time() - t0}")

print(mol_processor.lumped_states)
