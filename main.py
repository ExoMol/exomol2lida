from time import time

from exomol2lida.read_inputs import get_input
from exomol2lida.process_dataset import DatasetProcessor


mol_input = get_input("HCN", input_json_path="input/molecules.json")
mol_processor = DatasetProcessor(mol_input)

t0 = time()
mol_processor.lump_states()
print(f"Process time: {time() - t0}")

print(mol_processor.lumped_states)

# case = 1
# with open(f'output/lumped_states_{case}.csv', 'w') as fp:
#     mol_processor.lumped_states.to_csv(fp)
#
# forward_map = mol_processor.states_map_original_to_lumped
# with open(f'output/forward_map_{case}.py', 'w') as fp:
#     print('states_map_original_to_lumped = {', file=fp)
#     for map_i in sorted(forward_map):
#         print(f'    {map_i}: {forward_map[map_i]}, ', file=fp)
#     print('}', file=fp)
#
# backward_map = mol_processor.states_map_lumped_to_original
# with open(f'output/backward_map_{case}.py', 'w') as fp:
#     print('states_map_lumped_to_original = {', file=fp)
#     for map_i in sorted(backward_map):
#         print(f'    {map_i}: {sorted(backward_map[map_i])}, ', file=fp)
#     print('}', file=fp)
