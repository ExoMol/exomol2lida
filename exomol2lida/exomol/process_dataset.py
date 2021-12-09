from config.config import STATES_CHUNK_SIZE, TRANS_CHUNK_SIZE
from exomol2lida.exomol.utils import load_dataframe_chunks, get_num_columns
from input.molecules_inputs import (
    MoleculeInput, ExomolDefStatesMismatchError, MoleculeInputError)


class ExomolTransParseError(Exception):
    pass


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
        self.only_with, self.energy_max = {}, None
        for attr in ['resolve_el', 'resolve_vib', 'only_with', 'energy_max']:
            if hasattr(molecule_input, attr):
                setattr(self, attr, getattr(molecule_input, attr))
        if not len(self.resolve_el) and not len(self.resolve_vib):
            raise MoleculeInputError(
                f'Input for {self.formula} needs to implement at least one of '
                f'"resolve_el", "resolve_vib"')

        self.lumped_states = {}
        self.states_map = {}

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
            column_names=self.states_header, index_col=0
        )
        for chunk in states_chunks:
            if list(chunk.columns) != self.states_header[1:]:
                raise ExomolDefStatesMismatchError(f'Defense: {self.states_path}')
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
            raise ExomolTransParseError(
                f'Unexpected number of columns in '
                f'{self.trans_paths[0].name}: {num_cols}')
        # yield all the chunks:
        for file_path in self.trans_paths:
            trans_chunks = load_dataframe_chunks(
                file_path=file_path, chunk_size=TRANS_CHUNK_SIZE,
                column_names=column_names)
            for chunk in trans_chunks:
                yield chunk

    def _process_states(self):
        # TODO: get resolve_el_states, resolve_vib_states, and populate the
        #       self.lumped_states and self.states_map dicts.
        raise NotImplementedError
        # TODO: start with a line-by-line implementation and work from there...
