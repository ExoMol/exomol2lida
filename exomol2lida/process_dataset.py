"""
Module with functionality for processing ExoMol datasets into Lida data

The processing is controlled by the dict in input/molecules.py (see `read_inputs` module
and its docstrings).
"""
import math
import json
from datetime import datetime
from pprint import pprint

import pandas as pd
from exomole.read_data import states_chunks, trans_chunks
from tqdm import tqdm

from config.config import STATES_CHUNK_SIZE, TRANS_CHUNK_SIZE, OUTPUT_DIR
from .read_inputs import MoleculeInput
from .utils import EV_IN_CM


class DatasetProcessor:
    """Class for processing a single ExoMole dataset into the Lida data.

    Upon instantiation with a valid `MoleculeInput` instance, two methods must be
    called: `lump_states` and `lump_transitions`. This will produce the
    Lida data.

    Parameters
    ----------
    molecule : MoleculeInput or str
        If str passed, MoleculeInput is instantiated with data from the input file for
        the given ``molecule_formula = molecule`` passed.

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
        Populates the `lumped_states` DataFrame and the states maps.
    lump_transitions
        Populates the `lumped_transitions` DataFrame.
    process
        Lump states and transitions and log the data.
    """

    states_chunk_size = STATES_CHUNK_SIZE
    trans_chunk_size = TRANS_CHUNK_SIZE
    discarded_quanta_values = {"*"}
    include_original_lifetimes = None

    def __init__(self, molecule):
        if isinstance(molecule, MoleculeInput):
            molecule_input = molecule
        else:
            molecule_input = MoleculeInput(molecule_formula=molecule)

        self.molecule_input = molecule_input
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
        # if tau in states_header and self.include_original_lifetimes, populate this:
        self.states_map_lumped_to_tau = {}

        self.lumped_transitions = None

        self.output_dir = OUTPUT_DIR / self.formula
        if self.output_dir.exists() and list(self.output_dir.iterdir()):
            raise FileExistsError(f"The directory {self.output_dir} is not empty!")

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
        chunks_generator = states_chunks(
            states_path=self.states_path,
            chunk_size=self.states_chunk_size,
            columns=self.states_header,
        )
        for chunk in chunks_generator:
            chunk.loc[:, "J"] = chunk.loc[:, "J"].astype("float64")
            chunk.loc[:, "E"] = chunk.loc[:, "E"].astype("float64")
            chunk.loc[:, "g_tot"] = chunk.loc[:, "g_tot"].astype("float64")
            if self.include_original_lifetimes and "tau" in self.states_header:
                chunk.loc[:, "tau"] = pd.to_numeric(
                    chunk.loc[:, "tau"], errors="coerce"
                )
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
            # print(f"loaded a chunk of a .trans file of size {len(chunk):,}")
            yield chunk.copy(deep=True)

    def lump_states(self):
        """Method to lump all the non-resolved states into composite states.

        All the composite states are saved in `self.lumped_states` `DataFrame` and maps
        are created linking original to lumped state ids (indices in the original
        .states file and the `lumped_states` `DataFrame`).
        """
        lumped_states = None
        num_states = self.molecule_input.def_parser.num_states
        total_iter = math.ceil(
            num_states / self.states_chunk_size if num_states else float("inf")
        )
        for chunk in tqdm(
            self.states_chunks, total=total_iter, desc=f"{self.formula} states"
        ):
            # initial filtering based on the input and `discarded_quanta_values`
            mask = pd.Series(True, index=chunk.index)
            for quantum, val in self.only_with.items():
                mask = mask & (chunk.loc[mask, quantum] == val)
            for quantum in self.resolved_quanta:
                for val in self.discarded_quanta_values:
                    mask = mask & (chunk.loc[mask, quantum] != val)
            # get rid of all the states with negative integer vibrational quanta
            for quantum in self.resolve_vib:
                mask = mask & (chunk.loc[mask, quantum].astype("int64") >= 0)
            if self.energy_max is not None:
                mask = mask & (chunk.loc[mask, "E"] <= self.energy_max)
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
        lumped_states["E"] = (
            lumped_states.sum_en_x_w / lumped_states.sum_w / EV_IN_CM
        ).round(5)
        # clean up the column names, remove temporary columns
        lumped_states["J(E)"] = lumped_states["J_en"]
        lumped_states.drop(columns=["J_en", "sum_w", "sum_en_x_w"], inplace=True)
        # prepare a column for lifetimes:
        lumped_states["tau"] = float("inf")
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
        # and reindex the map between lump ids and original lifetimes, where appropriate
        if self.include_original_lifetimes and "tau" in self.states_header:
            self.states_map_lumped_to_tau = {
                lumped_index_update_map[key]: val
                for key, val in self.states_map_lumped_to_tau.items()
            }
        # and save the result as an instance attribute
        self.lumped_states = lumped_states

    def lump_transitions(self):
        """Method to lump all the transitions into composites only from and to resolved
        composite states.

        All the composite transitions are saved in `self.lumped_transitions`
        DataFrame.
        """
        # rolling sums of A_if for each transitions prelump (original_i -> lumped_f)
        prelumps_einstein_coeff_sums = pd.Series(dtype="float64")
        # rolling prelump sizes for each transitions prelump (original_i -> lumped_f)
        prelumps_sizes = pd.Series(dtype="float64")

        num_trans = self.molecule_input.def_parser.num_transitions
        total_iter = (
            math.ceil(num_trans / self.trans_chunk_size) if num_trans else float("inf")
        )
        for chunk in tqdm(
            self.trans_chunks, total=total_iter, desc=f"{self.formula} transitions"
        ):
            # add columns mapping initial and final states onto the lumped states
            chunk["lumped_i"] = chunk.i.transform(
                lambda i: self.states_map_original_to_lumped.get(i, None)
            )
            chunk["lumped_f"] = chunk.f.transform(
                lambda f: self.states_map_original_to_lumped.get(f, None)
            )
            # get rid of all the transitions from or to a non-existing lumped state
            chunk.dropna(axis="rows", inplace=True)
            # get rid of all the transitions within the same lumped state
            chunk = chunk.loc[chunk.lumped_i != chunk.lumped_f]
            if not len(chunk):
                # no transitions survived the filtering, go to the next iteration
                continue
            # now I can convert the lumped index values into int ("lumped_i" column
            # will be lost during the first grouping, so not worrying about it.)
            with pd.option_context("mode.chained_assignment", None):
                # just so suppress the SettingWithCopyWarning
                chunk.loc[:, "lumped_f"] = chunk.lumped_f.astype("int64")
            # after iteration over the chunks, I need sums of einstein coefficients
            # for transitions from the *original* initial index to the *lumped* final
            # index
            chunk_groupby = chunk.groupby(["i", "lumped_f"])
            current_prelumps_einstein_coeff_sums = (
                chunk_groupby["A_if"].sum().astype("float64")
            )
            current_prelumps_sizes = chunk_groupby["A_if"].count().astype("float64")

            if not len(prelumps_einstein_coeff_sums):
                # seed both the rolling prelump series:
                prelumps_einstein_coeff_sums = current_prelumps_einstein_coeff_sums
                prelumps_sizes = current_prelumps_sizes
            else:
                # just add to the rolling sums
                prelumps_einstein_coeff_sums = prelumps_einstein_coeff_sums.add(
                    current_prelumps_einstein_coeff_sums, fill_value=0
                )
                prelumps_sizes = prelumps_sizes.add(
                    current_prelumps_sizes, fill_value=0
                )
        # dataframe with partial lifetimes of individual pre-lumps
        # (between i_orig and f_lumped)
        prelumped_transitions = pd.DataFrame(
            {
                "tau_i_orig_f_lumped": 1 / prelumps_einstein_coeff_sums,
                "prelump_size": prelumps_sizes,
            }
        )
        prelumped_transitions.reset_index(inplace=True)
        # re-add the i_lumped and combine the pre-lumps into the final composite
        # transitions
        prelumped_transitions["lumped_i"] = prelumped_transitions.i.transform(
            lambda i: self.states_map_original_to_lumped[i]
        )
        prelumped_transitions_groupby = prelumped_transitions.groupby(
            ["lumped_i", "lumped_f"]
        )
        # create the lumped_transitions dataframe
        tau_if = prelumped_transitions_groupby["tau_i_orig_f_lumped"].mean()
        lump_size = prelumped_transitions_groupby["prelump_size"].sum()
        lumped_transitions = pd.DataFrame()
        lumped_transitions["tau_if"] = tau_if
        lumped_transitions["lump_size"] = lump_size.astype("int64")
        lumped_transitions.reset_index(inplace=True)
        lumped_transitions.columns = ["i", "f", "tau_if", "lump_size"]
        self.lumped_transitions = lumped_transitions

        # populate the total lifetimes for the composite states
        transitions_copy = lumped_transitions.copy(deep=True)
        transitions_copy.loc[:, "tau_if_inverse"] = 1 / transitions_copy["tau_if"]
        tau_i_inverse = transitions_copy.groupby("i")["tau_if_inverse"].sum()
        assert set(tau_i_inverse.index).issubset(self.lumped_states.index), "defense"
        self.lumped_states.loc[tau_i_inverse.index, "tau"] = 1 / tau_i_inverse

    def _process_state_lump(self, df):
        """A helper function for processing to-be-lumped states.

        This method is applied on a DataFrame of a group (lump) of states which all
        share the same values of the resolved quanta.

        Takes a dataframe filled with original states within one to-be composited state
        and does all the processing (like averaging energy, recording the J_ref for
        energy - lowest J, etc.). As the lumps are coming in states chunks, all
        needs to be done incrementally. This method is designed only as a helper method
        and only to be supplied to the `apply` method on a *grouped* pandas.DataFrame.

        Parameters
        ----------
        df : pandas.DataFrame

        Returns
        -------
        pandas.Series
        """
        # first record the lump into the states_map dict:
        if len(self.resolved_quanta) == 1:
            lumped_state = df.iloc[0].loc[self.resolved_quanta[0]]  # str
        else:
            lumped_state = tuple(df.iloc[0].loc[self.resolved_quanta])  # tuple[str]
        # lumped_state tuple will also be the new MultiIndex value after grouping
        if lumped_state not in self.states_map_lumped_to_original:
            self.states_map_lumped_to_original[lumped_state] = set()
        self.states_map_lumped_to_original[lumped_state].update(df.index)
        # now the original lifetimes, if relevant:
        if self.include_original_lifetimes and "tau" in self.states_header:
            if lumped_state not in self.states_map_lumped_to_tau:
                self.states_map_lumped_to_tau[lumped_state] = []
            self.states_map_lumped_to_tau[lumped_state].extend(df.tau)

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

    @staticmethod
    def _log_dict(data, file_path):
        with open(file_path, "w") as stream:
            stream.write("data = \\\n")
            pprint(data, width=88, compact=True, stream=stream)

    def _log_dataset_metadata(self):
        """Log all the relevant metadata for the current processing session.

        The meta-data are logged into the output folder in the .json format.
        Included are various molecule and isotopologue-related data needed by the
        lida-web project, as well as the dataset version and the full *raw input*
        from the ``input`` folder, for checking if the processed data are up-to-date
        with the ExoMol data or with the input file.
        """
        self.output_dir.mkdir(parents=True, exist_ok=True)
        metadata = {
            "input": self.molecule_input.raw_input,
            "iso_formula": self.molecule_input.iso_formula,
            "version": self.molecule_input.version,
            "mass": self.molecule_input.mass,
            "processed_on": str(datetime.now()),
        }
        metadata_path = self.output_dir / "meta_data.json"
        with open(metadata_path, "w") as fp:
            json.dump(metadata, fp, indent=2)

    def _log_states_metadata(self):
        """Log the lumped states metadata for the current processing session.

        If the `self.lump_states` method has not yet been run, this method will
        not log anything silently.
        The data are logged into the output folder in the .csv format under several
        files, containing the electronic and vibrational resolved quanta, and also a
        dict (called `data`) in states_composite_map.py file, mapping IDs of the lumped
        states back to the original ids of the ExoMol states.
        """
        if self.lumped_states is None:
            return
        self.output_dir.mkdir(parents=True, exist_ok=True)
        el_cols = self.resolve_el
        if len(el_cols):
            with open(self.output_dir / "states_electronic.csv", "w") as fp:
                self.lumped_states[el_cols].to_csv(
                    fp, header=True, index=True, index_label="i"
                )
        vib_cols = self.resolve_vib
        if len(vib_cols):
            with open(self.output_dir / "states_vibrational.csv", "w") as fp:
                self.lumped_states[vib_cols].to_csv(
                    fp, header=True, index=True, index_label="i"
                )
        self._log_dict(
            self.states_map_lumped_to_original,
            self.output_dir / "states_composite_map.py",
        )
        if self.include_original_lifetimes and "tau" in self.states_header:
            self._log_dict(
                self.states_map_lumped_to_tau,
                self.output_dir / "states_original_tau.py",
            )

    def _log_states_data(self):
        """Log the lumped states data for the current processing session.

        If the `self.lump_states` method has not yet been run, this method will
        not log anything silently.
        The data are logged into the output folder in the .csv format.
        """
        if self.lumped_states is None:
            return
        self.output_dir.mkdir(parents=True, exist_ok=True)
        data_cols = [col for col in ["tau", "E"] if col in self.lumped_states.columns]
        with open(self.output_dir / "states_data.csv", "w") as fp:
            self.lumped_states[data_cols].to_csv(
                fp, header=True, index=True, index_label="i"
            )

    def _log_transitions_data(self):
        """Log all the relevant lumped transitions data for the current processing
        session.

        If the `self.lump_transition` method has not yet been run, this method will
        not log anything silently.
        The data are logged into the output folder in the .csv format. The output file
        has the following header: ['i', 'f', 'tau_if'], where ``'i'`` and ``'f'``
        columns values correspond to the index column of the logged states .csv files.
        """
        if self.lumped_transitions is None:
            return
        self.output_dir.mkdir(parents=True, exist_ok=True)
        cols = ["i", "f", "tau_if"]
        with open(self.output_dir / "transitions_data.csv", "w") as fp:
            self.lumped_transitions[cols].to_csv(fp, header=True, index=False)

    def process(self, include_original_lifetimes=False):
        """Lump states and transitions and log all the outputs into the relevant
        location.

        Parameters
        ----------
        include_original_lifetimes : bool, default=False
            If True, also log the map between the composite state ids and lists
            of lifetimes of the original states belonging to each composite state.
        """
        self.include_original_lifetimes = include_original_lifetimes
        # lump and log the states:
        self.lump_states()
        self._log_dataset_metadata()
        self._log_states_metadata()
        self._log_states_data()
        # lump and log the transitions (the states file gets the "tau" column, so must
        # be re-logged.)
        self.lump_transitions()
        self._log_dataset_metadata()  # updated timestamp
        self._log_states_data()
        self._log_transitions_data()
