# import os
# import logging
# import pytz

# from datetime import datetime, timedelta
# from . .config import (
#     RESULTS_MAIN_DIR,LOGS_MAIN_DIR,UI_MAIN_DIR,
#     RESULTS_DIR_ETL_EXTRACTION,LOGS_DIR_ETL_EXTRACTION,
#     RESULTS_DIR_ETL_TRANSFORM_AND_LOAD,LOGS_DIR_ETL_TRANSFORM_AND_LOAD,
#     RESULTS_DIR_ETL_REPORT,LOGS_DIR_ETL_REPORT
# )

# def ensure_dir(path : str|list[str]):
#     if isinstance(path,str):
#         if not os.path.exists(path):
#             os.makedirs(path,exist_ok=True)
#     elif isinstance(path,list):
#         for p in [p for p in path if isinstance(p,str)]:
#             os.makedirs(p,exist_ok=True)

# def setup_dirs():        
#     ensure_dir([RESULTS_MAIN_DIR,
#                 LOGS_MAIN_DIR,
#                 UI_MAIN_DIR,
#                 RESULTS_DIR_ETL_EXTRACTION,
#                 LOGS_DIR_ETL_EXTRACTION,
#                 RESULTS_DIR_ETL_TRANSFORM_AND_LOAD,
#                 LOGS_DIR_ETL_TRANSFORM_AND_LOAD,                
#                 RESULTS_DIR_ETL_REPORT,
#                 LOGS_DIR_ETL_REPORT])

# def get_current_datetime() -> str:
#     brasilia_tz = pytz.timezone('America/Sao_Paulo')
#     brasilia_time = datetime.now(brasilia_tz)
#     return brasilia_time.strftime('d_%d_%m_%Y_t_%H_%M_%S')

# def get_old_loggings_file_paths(dir_path: str, max_days_living: int) -> list[str]:
#     brasilia_tz = pytz.timezone("America/Sao_Paulo")
#     now = datetime.now(tz=brasilia_tz)

#     log_files = [f for f in os.listdir(dir_path) if f.endswith('.log')]
#     files_to_delete = []

#     for log_file in log_files:
#         file_path = os.path.join(dir_path, log_file)

#         try:
#             # Pegando a data da última modificação
#             mod_timestamp = os.path.getmtime(file_path)
#             mod_datetime = datetime.fromtimestamp(mod_timestamp, tz=brasilia_tz)

#             # Verificando se o arquivo ultrapassou o tempo de vida
#             if now - mod_datetime > timedelta(days=max_days_living):
#                 files_to_delete.append(file_path)

#         except Exception as e:
#             pass

#     return files_to_delete
 

# def get_logger_for_current_run(loggings_full_file_path : str,
#                                remove_old_loggings : bool = True,
#                                max_days_living : int = 30):

#     if not loggings_full_file_path.endswith('.log'):
#         loggings_full_file_path += '.log'
    
#     if os.path.exists(loggings_full_file_path):
#         os.remove(loggings_full_file_path)
#     else:        
#         if os.path.dirname(loggings_full_file_path).strip():
#             ensure_dir(os.path.dirname(loggings_full_file_path))
    
#     if not os.path.dirname(loggings_full_file_path).strip():
#         loggings_full_file_path = os.path.join(os.getcwd(),loggings_full_file_path)
    
#     logging_config = {
#         'version': 1,
#         'disable_existing_loggers': False,
#         'formatters': {
#             'default': {
#                 'format': '%(asctime)s - %(levelname)s - %(message)s',
#                 'datefmt': '%d-%m-%Y %H:%M:%S',
#             },
#         },
#         'handlers': {
#             'file': {
#                 'class': 'logging.FileHandler',
#                 'filename': loggings_full_file_path,
#                 'level': 'INFO',
#                 'formatter': 'default',
#                 'encoding': 'utf-8',
#             },
#         },
#         'root': {
#             'handlers': ['file'],
#             'level': 'INFO',
#         },
#     }

#     # Configura o logger global
#     logging.config.dictConfig(logging_config)

#     # Retorna o logger para o módulo atual
#     logger = logging.getLogger(__name__)

#     if remove_old_loggings:
#         logger.info('Procurando arquivos antigos de log no diretório atual de log')
#         log_file_paths_to_delete = get_old_loggings_file_paths(dir_path=os.path.dirname(loggings_full_file_path),
#                                                                 max_days_living=max_days_living)
#         logger.info(f'Quantidade de arquivos de log para deletar: {len(log_file_paths_to_delete)}')
#         for log_file_path_to_delete in log_file_paths_to_delete:
#             os.remove(log_file_path_to_delete)

#     return logger
