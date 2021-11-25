from pathlib import Path


def local_config_exists():
    """
    Returns
    -------
    bool
        Boolean value if the local config file is found or not.
    """
    file_path = Path(__file__)
    local_config_file = file_path.joinpath('..', 'processing_config_local.py')
    return local_config_file.is_file()


# chunk size for .states files: approx 1,000,000 per 1GB of RAM
STATES_CHUNK_SIZE = 1_000_000
# chunk size for .trans files: roughly 10,000,000 per 1GB of RAM
TRANS_CHUNK_SIZE = 10_000_000

if local_config_exists():
    pass
