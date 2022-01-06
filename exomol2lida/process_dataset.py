"""
Module with functionality for processing ExoMol datasets into Lida data

The processing is controlled by the input/molecules.json (see ``read_inputs`` module
and its docstrings).
"""
import time

import pandas as pd
from exomole.read_data import states_chunks, trans_chunks

from config.config import STATES_CHUNK_SIZE, TRANS_CHUNK_SIZE
from .read_inputs import MoleculeInput


class DatasetProcessor:
    """Class for processing a single ExoMole dataset into the Lida data.

    Upon instantiation with a valid ``MoleculeInput`` instance, two methods must be
    called: ``lump_states`` and ``lump_transitions``. This will produce the
    Lida data.

    Parameters
    ----------
    molecule_input : MoleculeInput

    Attributes
    ----------
    resolved_quanta : list[str]
    lumped_states : pandas.DataFrame
    states_map_lumped_to_original : dict[int, set[int]]
    states_map_original_to_lumped : dict[int, int]
    lumped_transitions : pandas.DataFrame

    Methods
    -------
    lump_states
        Populates the ``lumped_states`` DataFrame and the states maps.
    lump_transitions
        Populates the ``lumped_transitions`` DataFrame.
    """

    states_chunk_size = STATES_CHUNK_SIZE
    trans_chunk_size = TRANS_CHUNK_SIZE
    discarded_quanta_values = {"*"}

    def __init__(self, molecule_input):
        self.formula = molecule_input.formula
        self.states_path = molecule_input.states_path
        self.trans_paths = molecule_input.trans_paths
        self.states_header = molecule_input.states_header
        self.resolve_el = molecule_input.resolve_el
        self.resolve_vib = molecule_input.resolve_vib
        self.only_with = molecule_input.only_with
        self.energy_max = molecule_input.energy_max

        self.resolved_quanta = self.resolve_el + self.resolve_vib

        self.lumped_states = None
        self.states_map_lumped_to_original = {}
        self.states_map_original_to_lumped = {}

        self.lumped_transitions = None

    @property
    def states_chunks(self):
        """Get chunks of the dataset states file.

        Generator of pandas.DataFrame chunks of the .states file, with
        (hopefully correctly) assigned columns, and indexed by states indices
        (the states indices are NOT present as a column, but as the dataframe index).
        The columns of each chunk are as follows:
        'E', 'g_tot', 'J' [, 'tau', 'g_J'], '<state1>' [, '<state2>', ..., '<stateN>']

        All the values in the DataFrames are str, except of J, E and g_tot.

        Yields
        -------
        states_chunk : pandas.DataFrame
            Generated chunks of the states file, each is a pd.DataFrame
        """
        assert self.states_header[0] == "i", f"Defense on {self.formula}"
        chunks_generator = states_chunks(
            states_path=self.states_path,
            chunk_size=self.states_chunk_size,
            columns=self.states_header[1:],
        )
        for chunk in chunks_generator:
            chunk.loc[:, "J"] = chunk.loc[:, "J"].astype("float64")
            chunk.loc[:, "E"] = chunk.loc[:, "E"].astype("float64")
            chunk.loc[:, "g_tot"] = chunk.loc[:, "g_tot"].astype("float64")
            yield chunk.copy(deep=True)

    @property
    def trans_chunks(self):
        """Get chunks of the dataset trans file.

        Generator of pandas.DataFrame chunks of all the .trans files for this dataset.
        The indices of the frame are irrelevant, the columns are as follows:
        'i', 'f', 'A_if' [, 'v_if'].
        The 'i' and 'f' columns correspond to the indices in the .states file.

        Yields
        -------
        trans_chunk : pandas.DataFrame
            Generated chunks of the trans file, each is a pd.DataFrame
        """
        for chunk in trans_chunks(
            trans_paths=self.trans_paths, chunk_size=self.trans_chunk_size
        ):
            yield chunk.copy(deep=True)

    def lump_states(self):
        """Method to lump all the non-resolved states into composite states.

        All the composite states are saved in ``self.lumped_states`` DataFrame and maps
        are created linking original to lumped state ids (indices in the original
        .states file and the ``lumped_states`` DataFrame).
        """
        lumped_states = None
        for chunk in self.states_chunks:
            # initial filtering based on the input and ``discarded_quanta_values``
            mask = pd.Series(True, index=chunk.index)
            for quantum, val in self.only_with.items():
                mask = mask & (chunk[quantum] == val)
            for quantum in self.resolved_quanta:
                for val in self.discarded_quanta_values:
                    mask = mask & (chunk[quantum] != val)
            if self.energy_max is not None:
                mask = mask & (chunk["E"] <= self.energy_max)
            chunk = chunk.loc[mask]
            if not len(chunk):
                # no states survived the filtering, go to the next iteration
                continue
            # group the states chunk into a multi-indexed DataFrame of composite states
            chunk_grouped = chunk.groupby(self.resolved_quanta)
            # process each multi-index into the final composite state and add the
            # processed chunk to the lumped_states
            lumped_states_chunk = chunk_grouped.apply(self._process_state_lump)
            if lumped_states is None:
                # seed the lumped_states dataframe
                lumped_states = pd.DataFrame(
                    index=lumped_states_chunk.index,
                    columns=lumped_states_chunk.columns,
                    dtype="float64",
                )
                lumped_states.loc[:, "J_en"] = float("inf")

            # ======================================================================== #
            # the ugly code in this bloc only ensures that energy for each lump is
            # calculated only from the lowest-J states, and I cannot know in which
            # chunk this will appear.

            # if in the current lumped_states_chunk there is either J
            # or a new index, I need to reset those rows in the lumped_states and
            # forget all the accumulated sum_w and sum_en_x_w...
            # new index:
            add_index = lumped_states_chunk.index.difference(lumped_states.index)
            # index of lower Js:
            index_intersection = lumped_states_chunk.index.intersection(
                lumped_states.index
            )
            reset_mask = lumped_states_chunk.J_en.loc[index_intersection].lt(
                lumped_states.J_en.loc[index_intersection]
            )
            reset_index = reset_mask.loc[reset_mask].index
            # all indices to reset:
            reset_index = reset_index.union(add_index, sort=False)
            # looks like I need to create temp. dataframe with union of the indices
            lumped_states_updated = pd.DataFrame(
                index=lumped_states.index.union(reset_index, sort=False),
                columns=lumped_states.columns,
                dtype="float64",
            )
            lumped_states_updated.loc[lumped_states.index] = lumped_states
            # and reset the values:
            lumped_states_updated.loc[reset_index, "J_en"] = lumped_states_chunk.loc[
                reset_index, "J_en"
            ]
            lumped_states_updated.loc[reset_index, ["sum_w", "sum_en_x_w"]] = [0, 0]
            # now to update the sum_w and sum_en_x_w accumulates
            index_intersection = lumped_states_updated.index.intersection(
                lumped_states_chunk.index
            )
            update_mask = lumped_states_updated.J_en.loc[index_intersection].eq(
                lumped_states_chunk.J_en.loc[index_intersection]
            )
            update_index = update_mask.loc[update_mask].index
            lumped_states_updated.loc[
                update_index, ["sum_w", "sum_en_x_w"]
            ] = lumped_states_updated.loc[update_index, ["sum_w", "sum_en_x_w"]].add(
                lumped_states_chunk.loc[update_index, ["sum_w", "sum_en_x_w"]]
            )
            # and get rid of the temp. dataframe
            lumped_states = lumped_states_updated
            # ======================================================================== #

        # calculate the g_tot-weighted energy average per each lump
        lumped_states["E"] = (lumped_states.sum_en_x_w / lumped_states.sum_w).round(5)
        # clean up the column names, remove temporary columns
        lumped_states["J(E)"] = lumped_states["J_en"]
        lumped_states.drop(columns=["J_en", "sum_w", "sum_en_x_w"], inplace=True)
        # add a column with lump size (number of original states in each lump):
        lumped_states.loc[:, "lump_size"] = [
            len(self.states_map_lumped_to_original[lumped_i])
            for lumped_i in lumped_states.index
        ]
        lumped_states.sort_values(by="E", inplace=True)
        # flatten the lumped_states multiindex into columns and reset index
        # each lumped state will get it's own integer index
        lumped_index_orig = list(lumped_states.index)
        lumped_states.reset_index(inplace=True)
        lumped_index_update_map = dict(zip(lumped_index_orig, lumped_states.index))
        # states_map_lumped_to_original was created (by _process_state_lump helper)
        # with the original multi-index, now I need to update it so it is
        # index-to-set[index] (int-to-set[int]).
        self.states_map_lumped_to_original = {
            lumped_index_update_map[key]: val
            for key, val in self.states_map_lumped_to_original.items()
        }
        # similarly: populate forward map from the original index to the lumped index:
        for lumped_i, original_indices in self.states_map_lumped_to_original.items():
            self.states_map_original_to_lumped.update(
                {i: lumped_i for i in original_indices}
            )
        # and save the result as an instance attribute
        self.lumped_states = lumped_states

    def lump_transitions(self):
        for chunk in self.trans_chunks:
            print("Original chunk")
            print(chunk)
            # add columns mapping initial and final states onto the lumped states
            t0 = time.time()
            chunk["lumped_i"] = chunk.i.transform(
                lambda i: self.states_map_original_to_lumped.get(i, None)
            )
            chunk["lumped_f"] = chunk.f.transform(
                lambda f: self.states_map_original_to_lumped.get(f, None)
            )
            print("After adding the lumped indices")
            print(chunk)
            # get rid of all the transitions from or to a non-existing lumped state
            chunk = chunk.dropna(axis="rows")
            # now I can convert the lumped index values into int
            chunk.loc[:, "lumped_i"] = chunk.lumped_i.astype("int64")
            chunk.loc[:, "lumped_f"] = chunk.lumped_f.astype("int64")
            print("After dropping nan values")
            print(chunk)
            # get rid of all the transitions within the same lumped state
            chunk = chunk.loc[chunk.lumped_i != chunk.lumped_f]
            print("After dropping the transitions within lump")
            print(chunk)
            print(f"Chunk processing time: {time.time() - t0}")
            break

    def _process_state_lump(self, df):
        """A helper function for processing a lumped states.

        This method is applied on a DataFrame of a group (lump) of states which all
        share the same values of the resolved quanta.

        Takes a dataframe filled with original states within one to-be composited state
        and does all the processing (like averaging energy, recording the J_ref for
        energy - lowest J, etc.). As the lumps are coming in states chunks, all
        needs to be done incrementally. This method is designed only as a helper method
        and only to be supplied to the ``apply`` method on a *grouped* pandas.DataFrame.

        Parameters
        ----------
        df : pandas.DataFrame

        Returns
        -------
        pandas.Series

        """
        # first record the lump into the states_map dict:
        lumped_state = tuple(df.iloc[0].loc[self.resolved_quanta])
        # lumped_state tuple will also be the new MultiIndex value after grouping
        if lumped_state not in self.states_map_lumped_to_original:
            self.states_map_lumped_to_original[lumped_state] = set()
        self.states_map_lumped_to_original[lumped_state].update(df.index)

        # now calculate the lumped state attributes:
        # energy is calculated as the average of energies over the states with
        # lowest J, weighted by the total degeneracy
        j_min = df.J.min()
        sub_df = df.loc[df.J == j_min]
        sub_df["en_x_w"] = sub_df.E * sub_df.g_tot
        sum_w, sum_en_x_w = sub_df[["g_tot", "en_x_w"]].sum(axis=0).values
        return pd.Series(
            [j_min, sum_w, sum_en_x_w],
            index=["J_en", "sum_w", "sum_en_x_w"],
            dtype="float64",
        )