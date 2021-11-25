# from pathlib import Path
#
# import pandas as pd
#
# from exomol2lida.config.processing_config import STATES_CHUNK_SIZE, TRANS_CHUNK_SIZE
#
#
# class DatasetProcessor:
#
#     def __init__(self, dataset_dir):
#         ds_dir = Path(dataset_dir).resolve()
#         assert ds_dir.is_dir()
#         iso_slug, ds_name = ds_dir.parent.name, ds_dir.name
#
#         # determine the full paths to all the relevant files
#         self.def_file_path = ds_dir / f'{iso_slug}__{ds_name}.def'
#         assert self.def_file_path.is_file()
#
#         states_file_paths = sorted(ds_dir.glob(f'{iso_slug}__{ds_name}*.states.bz2'))
#         assert len(states_file_paths) == 1
#         self.states_file_path = states_file_paths[0]
#         self.trans_file_paths = sorted(
#             ds_dir.glob(f'{iso_slug}__{ds_name}__*0-*0.trans.bz2')
#         )
#         assert len(self.trans_file_paths) > 0
#
#     @staticmethod
#     def load_dataframe_chunks(file_path, chunk_size, column_names, index_col=None):
#         df_chunks = pd.read_csv(
#             file_path, compression='bz2', sep=r'\s+', header=None, index_col=index_col,
#             names=column_names, chunksize=chunk_size, iterator=True, low_memory=False
#         )
#         return df_chunks
#
#     def process_states_file(self):
#         chunks = self.load_dataframe_chunks(
#             file_path=self.states_file_path, chunk_size=STATES_CHUNK_SIZE,
#             column_names=[str(a) for a in range(29)], index_col=0
#         )
#         for ch in chunks:
#             print(ch)
