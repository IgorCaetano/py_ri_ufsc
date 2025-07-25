from os.path import exists
from . .config import DATASET_PARQUET_FILE_PATH

if not exists(DATASET_PARQUET_FILE_PATH):
    from .utils import download_ri_ufsc_dataset_via_hugging_face
    download_ri_ufsc_dataset_via_hugging_face()
