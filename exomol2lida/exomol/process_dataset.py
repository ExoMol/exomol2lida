import pandas as pd

from config.config import STATES_CHUNK_SIZE, TRANS_CHUNK_SIZE
from exomol2lida.exomol.utils import load_dataframe_chunks, get_num_columns
from input.molecules_inputs import MoleculeInput
from exceptions import MoleculeInputError, StatesParseError, TransParseError


class DatasetProcessor:

    def __init__(self, molecule_input):
        """

        Parameters
        ----------
        molecule_input : MoleculeInput
            The passed object needs to implement the following interface of attributes:
                formula : str
                states_path : str | Path
                trans_paths : list[str | Path]
                states_header : list[str]
                resolve_el: list[str], optional
                resolve_vib: list[str], optional
                only_with: dict[str, Any], optional
                energy_max: number, optional
        """
        self.molecule_input = molecule_input

        self.formula = molecule_input.formula
        self.states_path = molecule_input.states_path
        self.trans_paths = molecule_input.trans_paths
        self.states_header = molecule_input.states_header

        self.resolve_el, self.resolve_vib = [], []
        self.only_with = {}
        self.energy_max = None
        for attr in ['resolve_el', 'resolve_vib', 'only_with', 'energy_max']:
            if hasattr(molecule_input, attr):
                setattr(self, attr, getattr(molecule_input, attr))
        if not len(self.resolve_el) and not len(self.resolve_vib):
            raise MoleculeInputError(
                f'Input for {self.formula} needs to implement at least one of '
                f'"resolve_el", "resolve_vib"')
        # some verification on the passed parameters
        for name, quanta in zip(['resolve_el', 'resolve_vib', 'only_with'],
                                [self.resolve_el, self.resolve_vib, self.only_with]):
            if not set(quanta).issubset(self.states_header[4:]):
                raise MoleculeInputError(
                    f'Unrecognised {name} passed: {quanta} not among states columns.')
        if self.energy_max is not None:
            self.energy_max = float(self.energy_max)
        self.resolved_quanta = self.resolve_el + self.resolve_vib

        self.lumped_states = None
        self.states_map_lumped_to_original = {}
        self.states_map_original_to_lumped = {}

        self.lumped_transitions = None

    @property
    def states_chunks(self):
        """
        Get chunks of the dataset states file.

        Generator of pd.DataFrame chunks of the .states file, with
        (hopefully correctly) assigned columns, and indexed by states indices
        (the states indices are NOT present as a column, but as the dataframe index).
        The columns of each chunk are as follows:
        'E', 'g_tot', 'J' [, 'tau', 'g_J'], '<state1>' [, '<state2>', ..., '<stateN>']

        Yields
        -------
        states_chunk : pd.DataFrame
            Generated chunks of the states file, each is a pd.DataFrame

        Examples
        --------
        TODO: add an example loading a df from test resources and showing the cols
        """
        assert self.states_header[0] == 'i', f'Defense on {self.formula}'
        states_chunks = load_dataframe_chunks(
            file_path=self.states_path, chunk_size=STATES_CHUNK_SIZE,
            column_names=self.states_header, index_col=0, dtype=str
        )
        for chunk in states_chunks:
            if list(chunk.columns) != self.states_header[1:]:
                raise StatesParseError(f'Defense: {self.states_path}')
            chunk.loc[:, 'J'] = chunk.loc[:, 'J'].astype('float64')
            chunk.loc[:, 'E'] = chunk.loc[:, 'E'].astype('float64')
            chunk.loc[:, 'g_tot'] = chunk.loc[:, 'g_tot'].astype('float64')
            yield chunk

    @property
    def trans_chunks(self):
        """
        Get chunks of the dataset trans file.

        Generator of pd.DataFrame chunks of all the .trans files for this dataset.
        The indices of the frame are irrelevant, the columns are as follows:
        'i', 'f', 'A_if' [, 'v_if'].
        The 'i' and 'f' columns correspond to the indices in the .states file.

        Yields
        -------
        trans_chunk : pd.DataFrame
            Generated chunks of the trans file, each is a pd.DataFrame

        Examples
        --------
        TODO: add an example loading a df from test resources and showing the cols
        """
        # columns of the .trans files?
        num_cols = get_num_columns(self.trans_paths[0])
        column_names = ['i', 'f', 'A_if']
        if num_cols == 4:
            column_names.append('v_if')
        elif num_cols != 3:
            raise TransParseError(
                f'Unexpected number of columns in '
                f'{self.trans_paths[0].name}: {num_cols}')
        # yield all the chunks:
        for file_path in self.trans_paths:
            trans_chunks = load_dataframe_chunks(
                file_path=file_path, chunk_size=TRANS_CHUNK_SIZE,
                column_names=column_names)
            for chunk in trans_chunks:
                yield chunk

    def lump_states(self):
        lumped_states = None
        for chunk in self.states_chunks:
            # initial filtering
            mask = pd.Series(True, index=chunk.index)
            for quanta, val in self.only_with.items():
                mask = mask & (chunk[quanta] == val)
            if self.energy_max is not None:
                mask = mask & (chunk['E'] <= self.energy_max)
            chunk = chunk.loc[mask]
            if not len(chunk):
                # no states survived the filtering, go to the next iteration
                continue
            chunk_grouped = chunk.groupby(self.resolved_quanta)
            lumped_states_chunk = chunk_grouped.apply(self._process_state_lump)
            if lumped_states is None:
                # seed the lumped_states dataframe
                lumped_states = pd.DataFrame(
                    index=lumped_states_chunk.index,
                    columns=lumped_states_chunk.columns, dtype='float64')
                lumped_states.loc[:, 'J'] = float('inf')
            # if in the current lumped_states_chunk there is either  J
            # or a new index, I need to reset those rows in the lumped_states and
            # forget all the accumulated sum_w and sum_en_x_w...
            # new index:
            add_index = lumped_states_chunk.index.difference(
                lumped_states.index)
            # index of lower Js:
            index_intersection = lumped_states_chunk.index.intersection(
                lumped_states.index)
            reset_mask = lumped_states_chunk.J.loc[index_intersection].lt(
                lumped_states.J.loc[index_intersection])
            reset_index = reset_mask.loc[reset_mask].index
            # all indices to reset:
            reset_index = reset_index.union(add_index, sort=False)
            # looks like I need to create temp. dataframe with union of the indices
            lumped_states_updated = pd.DataFrame(
                index=lumped_states.index.union(reset_index, sort=False),
                columns=lumped_states.columns, dtype='float64')
            lumped_states_updated.loc[lumped_states.index] = lumped_states
            # and reset the values:
            lumped_states_updated.loc[reset_index, 'J'] = \
                lumped_states_chunk.loc[reset_index, 'J']
            lumped_states_updated.loc[reset_index, ['sum_w', 'sum_en_x_w']] = [0, 0]
            # now to update the sum_w and sum_en_x_w accumulates
            index_intersection = lumped_states_updated.index.intersection(
                lumped_states_chunk.index)
            update_mask = lumped_states_updated.J.loc[index_intersection].eq(
                lumped_states_chunk.J.loc[index_intersection])
            update_index = update_mask.loc[update_mask].index
            lumped_states_updated.loc[update_index, ['sum_w', 'sum_en_x_w']] = \
                lumped_states_updated.loc[update_index, ['sum_w', 'sum_en_x_w']].add(
                    lumped_states_chunk.loc[update_index, ['sum_w', 'sum_en_x_w']])
            # and get rid of the temp. dataframe
            lumped_states = lumped_states_updated

        # calculate the energy weighted average and get rid of temp. columns
        lumped_states['E'] = (lumped_states.sum_en_x_w / lumped_states.sum_w).round(5)
        lumped_states = lumped_states.drop(columns=['sum_w', 'sum_en_x_w'])
        # and save the result as an instance attribute
        self.lumped_states = lumped_states

    def lump_transitions(self):
        for chunk in self.trans_chunks:
            # add columns mapping initial and final states on to the lumped states
            chunk['lumped_i'] = chunk.i.transform(
                lambda i: self.states_map_original_to_lumped.get(i, None))
            chunk['lumped_f'] = chunk.f.transform(
                lambda f: self.states_map_original_to_lumped.get(f, None))
            # get rid of all the transitions from or to a non-existing lumped state
            chunk = chunk.dropna(axis='rows')
            # get rid of all the transitions within the same lumped state
            chunk = chunk.loc[chunk.lumped_i != chunk.lumped_f]

    def _process_state_lump(self, df):
        # this is applied on a dataframe of a group (lump) of states which all share
        # the same values of the resolved quanta

        # first record the lump into the states_map dicts:
        lumped_state = tuple(df.iloc[0].loc[self.resolved_quanta])
        if lumped_state not in self.states_map_lumped_to_original:
            self.states_map_lumped_to_original[lumped_state] = set()
        self.states_map_lumped_to_original[lumped_state].update(df.index)
        self.states_map_original_to_lumped.update(
            {i: lumped_state for i in df.index})

        # now calculate the lumped state attributes:
        # energy is calculated as the average of energies over the states with
        # lowest J, weighted by the total degeneracy
        j_min = df.J.min()
        sub_df = df.loc[df.J == j_min]
        sub_df['en_x_w'] = sub_df.E * sub_df.g_tot
        sum_w, sum_en_x_w = sub_df[['g_tot', 'en_x_w']].sum(axis=0).values
        return pd.Series([j_min, sum_w, sum_en_x_w],
                         index=['J', 'sum_w', 'sum_en_x_w'], dtype='float64')


if __name__ == '__main__':
    from input.molecules_inputs import get_input
    from time import time

    mol_input = get_input('HCN')
    mol_processor = DatasetProcessor(mol_input)

    t0 = time()
    mol_processor.lump_states()
    print(f'Process time: {time() - t0}')

    print(mol_processor.lumped_states.sort_values('E'))
