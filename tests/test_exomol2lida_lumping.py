from pathlib import Path

import pytest

from exomol2lida.read_inputs import MoleculeInput
from exomol2lida.process_dataset import DatasetProcessor

test_resources_dir = Path(__file__).parent / "resources"

mol_input = MoleculeInput(
    molecule_formula="HCN",
    **{
        "mol_slug": "HCN",
        "iso_slug": "1H-12C-14N",
        "dataset_name": "Harris",
        "states_header": [
            "i",
            "E",
            "g_tot",
            "J",
            "+/-",
            "kp",
            "iso",
            "v1",
            "v2",
            "l2",
            "v3",
        ],
        "resolve_vib": ["v1", "v2", "v3"],
        "energy_max": 9000,
        "only_with": {"iso": "1"},
    },
)
states_path = test_resources_dir / "dummy_data.states.bz2"
trans_paths_full = [test_resources_dir / "dummy_data.trans.bz2"]
trans_paths_split = sorted(test_resources_dir.glob("dummy_data.trans_0*.bz2"))

shared_for_comparison = {
    "lumped_states": None,
    "states_map_lumped_to_original": None,
    "states_map_original_to_lumped": None,
    "lumped_transitions": None,
}


@pytest.mark.parametrize("chunk_size", (1_000_000, 100_000, 10_000, 5_000))
def test_states_lumping(monkeypatch, chunk_size):
    processor = DatasetProcessor(molecule=mol_input)
    monkeypatch.setattr(processor, "states_path", states_path)
    processor.states_chunk_size = chunk_size
    processor.lump_states()
    if shared_for_comparison["lumped_states"] is None:
        shared_for_comparison["lumped_states"] = processor.lumped_states.copy(deep=True)
        shared_for_comparison[
            "states_map_lumped_to_original"
        ] = processor.states_map_lumped_to_original.copy()
        shared_for_comparison[
            "states_map_original_to_lumped"
        ] = processor.states_map_original_to_lumped.copy()
    else:
        assert processor.lumped_states.equals(shared_for_comparison["lumped_states"])
        assert (
            processor.states_map_lumped_to_original
            == shared_for_comparison["states_map_lumped_to_original"]
        )
        assert (
            processor.states_map_original_to_lumped
            == shared_for_comparison["states_map_original_to_lumped"]
        )


def test_trans_lumping(monkeypatch):
    pass
