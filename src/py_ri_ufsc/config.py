import os

############################################         DIRECTORIES         ############################################

#####################    GENERAL    #####################

ROOT_DIR = os.getcwd()
# ROOT_DIR = r'C:\Users\Igor\Documents\GitHub\py_ri_ufsc_constru\Testings_py_ri_ufsc'
MAIN_DIR = os.path.join(ROOT_DIR,'py_ri_ufsc')
RESULTS_MAIN_DIR = os.path.join(MAIN_DIR,'results')
LOGS_MAIN_DIR = os.path.join(MAIN_DIR,'logs')
UI_MAIN_DIR = os.path.join(MAIN_DIR,'ui_files')


#####################    ETL    #####################
RESULTS_DIR_ETL = os.path.join(RESULTS_MAIN_DIR,'etl')
LOGS_DIR_ETL = os.path.join(LOGS_MAIN_DIR,'etl')
COL_TO_NAME_CSV_FILE_PATH = os.path.join(RESULTS_DIR_ETL,'col_to_name.csv')
###### EXTRACTION ######
RESULTS_DIR_ETL_EXTRACTION = os.path.join(RESULTS_DIR_ETL,'extraction')
LOGS_DIR_ETL_EXTRACTION = os.path.join(LOGS_DIR_ETL,'extraction')
###### TRANSFORM AND LOAD ######
RESULTS_DIR_ETL_TRANSFORM_AND_LOAD = os.path.join(RESULTS_DIR_ETL,'transform_and_load')
LOGS_DIR_ETL_TRANSFORM_AND_LOAD = os.path.join(LOGS_DIR_ETL,'transform_and_load')
COMPLETED_DATA_PARQUET_FILE_PATH = os.path.join(RESULTS_DIR_ETL_TRANSFORM_AND_LOAD,'tabled_data_completed.parquet')

###### REPORT ######
RESULTS_DIR_ETL_REPORT = os.path.join(RESULTS_DIR_ETL,'report')
LOGS_DIR_ETL_REPORT = os.path.join(LOGS_DIR_ETL,'report')

######################## USER INTERFACE ########################

UI_DOWNLOADS = os.path.join(UI_MAIN_DIR,'downloads')

############################################         CONSTANTS         ############################################

#####################    ETL    #####################
###### EXTRACTION ######
BASE_URL = 'https://repositorio.ufsc.br'
BASE_API_SINTAX = '/oai/request?'
BASE_VERB = 'ListRecords'
BASE_METADATA_PREFIX = 'xoai'
# EXPECTED_NUMBER_OF_ITEMS = 157021
# MAX_ITEMS_RETURNED_FROM_API = 100


this_dir,this_file = os.path.split(__file__)
DATASET_PARQUET_FILE_PATH = os.path.join(this_dir,'src_files','dataset.parquet')
