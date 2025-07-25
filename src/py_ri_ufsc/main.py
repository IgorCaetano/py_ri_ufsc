import pandas as pd

from .get_metadata.utils import (
    get_available_values_in_dataset,get_available_columns_in_dataset,get_raw_dataset,
    get_filtered_raw_dataset
)
from .get_metadata.main import get_filtered_dataset_for_main_graphs
from .get_metadata.tests import TestRIUFSC


class RIUFSC():
    def __init__(self,
                 silence : bool = True):
        self.silence = silence
        if not silence:
            print('Não recomendamos carregar o dataset inteiro, tente sempre selecionar apenas as colunas que deseja utilizar.')

    def help(self):
        print('\n\n\tFunções disponíveis:\n')
        print('-'*100)
        print('get_available_columns_in_ri_ufsc_dataset -> lista todas as colunas disponíveis no dataset (RAM friendly).')
        print('-'*100)
        print('get_available_values_in_ri_ufsc_dataset -> lista todos os valores disponíveis na coluna desejada\nno dataset (RAM friendly).')
        print('-'*100)
        print('get_raw_ri_ufsc_dataset -> entrega um objeto DataFrame do pandas (selecione as colunas pelo parâmetro\n"columns_to_use" se não quiser carregar o dataset inteiro).')
        print('-'*100)
        print('get_filtered_raw_dataset_based_on_link_site_column -> entrega um objeto DataFrame do pandas com filtro\nde link_site aplicado para obter apenas registros que estejam presentes na lista "filter_links" (selecione\nas colunas que desejar no df de saída para minimizar o uso de RAM).')
        print('-'*100)
        print('get_filtered_ri_ufsc_dataset -> entrega um objeto DataFrame do pandas filtrado de acordo com os\nparâmetros selecionados.')
        print('-'*100)
        print('get_testing_object -> entrega um objeto TestRIUFSC para realização de testes com todo kit de ferramentas\nutilizado na construção/organização do dataset. Esse objeto tem funções próprias, veja o notebook de testes\ndisponibilizado no repositório.')
        print('-'*100)
        print('\n')

    def get_available_columns_in_ri_ufsc_dataset(self) -> list[str]:
        return get_available_columns_in_dataset()

    def get_available_values_in_ri_ufsc_dataset(self,column_name : str) -> list[str]:
        return get_available_values_in_dataset(column_name=column_name,silence=self.silence)

    def get_raw_ri_ufsc_dataset(self,columns_to_use : list[str]) -> pd.DataFrame:
        return get_raw_dataset(columns_to_use=columns_to_use)

    def get_filtered_raw_dataset_based_on_link_site_column(self,
                                                           columns_to_use : list[str],
                                                           filter_links : list[str]) -> pd.DataFrame:
        return get_filtered_raw_dataset(columns_to_use=columns_to_use,filter_links=filter_links)

    def get_filtered_ri_ufsc_dataset(self,
                                     type_filter : dict = {"use": False,"types":None,"exclude_empty_values":False},
                                     date_filter: dict = {"use": False, "date_1": None, "date_2": None,"exclude_empty_values":False},
                                     title_filter: dict = {"use": False, "words": None, "match_all": False,"exclude_empty_values":False},
                                     subjects_filter: dict = {"use": False, "subjects": None, "match_all": False,"exclude_empty_values":False},
                                     authors_filter: dict = {"use": False, "author_names": None, "match_all": False,"exclude_empty_values":False},
                                     advisors_filter: dict = {"use": False, "advisor_names": None, "match_all": False,"exclude_empty_values":False},
                                     gender_filter: dict = {"use": False, "genders": None, "just_contain": True,"exclude_empty_values":False},
                                     language_filter: dict = {"use": False, "languages": None, "exclude_empty_values": False},
                                     course_filter: dict = {"use": False, "courses": None, "exclude_empty_values": False},
                                     type_course_filter: dict = {"use": False, "type_courses": None, "exclude_empty_values": False},
                                     centro_filter: dict = {"use": False, "centros": None, "exclude_empty_values": False},
                                     campus_filter: dict = {"use": False, "campuses": None, "exclude_empty_values": False},
                                     exported_columns : list[str]|None = None) -> pd.DataFrame:
        return get_filtered_dataset_for_main_graphs(type_filter=type_filter,
                                                    date_filter=date_filter,
                                                    title_filter=title_filter,
                                                    subjects_filter=subjects_filter,
                                                    authors_filter=authors_filter,
                                                    advisors_filter=advisors_filter,
                                                    gender_filter=gender_filter,
                                                    language_filter=language_filter,
                                                    course_filter=course_filter,
                                                    type_course_filter=type_course_filter,
                                                    centro_filter=centro_filter,
                                                    campus_filter=campus_filter,
                                                    exported_columns=exported_columns,
                                                    silence=self.silence)

    def get_testing_object(self,
                           df : pd.DataFrame|None = None) -> TestRIUFSC:
        if not self.silence:
            print('A partir de agora use o objeto retornado como uma classe nova, específica para realização de testes.')
        return TestRIUFSC(df=df)
