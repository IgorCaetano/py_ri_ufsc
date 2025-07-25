
import pandas as pd

from .utils import get_raw_dataset
from .filters import (
    filter_types,filter_dates,filter_title_by_words,filter_subjects,
    filter_authors,filter_advisors,filter_gender,filter_language,
    filter_course,filter_type_course,filter_centro,filter_campus
)

def get_filtered_dataset_for_main_graphs(type_filter : dict = {"use": False,"types":None,"exclude_empty_values":False},
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
                                         exported_columns : list[str]|None = None,
                                         silence : bool = True) -> pd.DataFrame:
    
    columns_to_use = ['year','gender_name','language','link_site']
    if not silence:
        print(f'Colunas fixas para uso: {str(columns_to_use)}...')
    if type_filter.get('use',False):
        columns_to_use.append('type')
        if not silence:
            print('Adicionando coluna type...')
    # if date_filter.get('use',False):
    #     columns_to_use.append('year')
    if title_filter.get('use',False):
        columns_to_use.append('title')
        if not silence:
            print('Adicionando coluna title...')
    if subjects_filter.get('use',False):
        columns_to_use.append('subjects')
        if not silence:
            print('Adicionando coluna subjects...')
    if authors_filter.get('use',False):
        columns_to_use.append('authors')
        if not silence:
            print('Adicionando coluna authors...')
    if advisors_filter.get('use',False):
        columns_to_use.append('advisors')
        if not silence:
            print('Adicionando coluna advisors...')
    # if gender_filter.get('use',False):
    #     columns_to_use.append('gender_name')
    # if language_filter.get('use',False):
    #     columns_to_use.append('language')
    if course_filter.get('use',False):
        columns_to_use.append('course')
        if not silence:
            print('Adicionando coluna course...')
    if type_course_filter.get('use',False):
        columns_to_use.append('type_course')
        if not silence:
            print('Adicionando coluna type_course...')
    if centro_filter.get('use',False):
        columns_to_use.append('centro')
        if not silence:
            print('Adicionando coluna centro...')
    if campus_filter.get('use',False):
        columns_to_use.append('campus')
        if not silence:
            print('Adicionando coluna campus...')

    if exported_columns:
        if not silence:
            print('Obtendo dataframe via dataset com colunas para uso + colunas para exportação...')
        df = get_raw_dataset(columns_to_use=list(set(columns_to_use+exported_columns)))
    else:
        if not silence:
            print('Obtendo dataframe via dataset com colunas para uso...')
        df = get_raw_dataset(columns_to_use=columns_to_use)

    df_filtered = df.copy().reset_index().drop(columns=['index'])
    if not silence:
        print('Iniciando filtragem do dataframe...')
    # Datas
    if date_filter and date_filter.get("use", False):
        if not silence:
            print('Iniciando filtro de datas...')
        df_filtered = filter_dates(
            df=df_filtered,
            date_1=date_filter["date_1"],
            date_2=date_filter["date_2"],
            exclude_empty_values=date_filter['exclude_empty_values']
        )

    # Tipos
    if type_filter and type_filter.get("use", False):
        if not silence:
            print('Iniciando filtro de tipos...')
        df_filtered = filter_types(
            df=df_filtered,
            types=type_filter["types"],
            exclude_empty_values=type_filter["exclude_empty_values"]
        )

    # Language
    if language_filter and language_filter.get("use", False):
        if not silence:
            print('Iniciando filtro de idiomas...')
        df_filtered = filter_language(
            df=df_filtered,
            languages=language_filter["languages"],
            exclude_empty_values=language_filter['exclude_empty_values']
        )

    # Centro
    if centro_filter and centro_filter.get("use", False):
        if not silence:
            print('Iniciando filtro de centros...')
        df_filtered = filter_centro(
            df=df_filtered,
            centros=centro_filter["centros"],
            exclude_empty_values=centro_filter["exclude_empty_values"]
        )

    # Campus
    if campus_filter and campus_filter.get("use", False):
        if not silence:
            print('Iniciando filtro de campus...')
        df_filtered = filter_campus(
            df=df_filtered,
            campuses=campus_filter["campuses"],
            exclude_empty_values=campus_filter["exclude_empty_values"]
        )

    # Course
    if course_filter and course_filter.get("use", False):
        if not silence:
            print('Iniciando filtro de cursos...')
        df_filtered = filter_course(
            df=df_filtered,
            courses=course_filter["courses"],
            exclude_empty_values=course_filter["exclude_empty_values"]
        )

    # Type Course
    if type_course_filter and type_course_filter.get("use", False):
        if not silence:
            print('Iniciando filtro de tipos de curso...')
        df_filtered = filter_type_course(
            df=df_filtered,
            type_courses=type_course_filter["type_courses"],
            exclude_empty_values=type_course_filter["exclude_empty_values"]
        )

    # Gender
    if gender_filter and gender_filter.get("use", False):
        if not silence:
            print('Iniciando filtro de gênero dos autores...')
        df_filtered = filter_gender(
            df=df_filtered,
            genders=gender_filter["genders"],
            just_contain=gender_filter["just_contain"],
            exclude_empty_values=gender_filter['exclude_empty_values']
        )

    # Título
    if title_filter and title_filter.get("use", False):
        if not silence:
            print('Iniciando filtro de títulos...')
        df_filtered = filter_title_by_words(
            df=df_filtered,
            words=title_filter["words"],
            match_all=title_filter["match_all"],
            exclude_empty_values=title_filter["exclude_empty_values"]
        )

    # Subjects
    if subjects_filter and subjects_filter.get("use", False):
        if not silence:
            print('Iniciando filtro de assuntos...')
        df_filtered = filter_subjects(
            df=df_filtered,
            subjects=subjects_filter["subjects"],
            match_all=subjects_filter["match_all"],
            exclude_empty_values=subjects_filter['exclude_empty_values']
        )

    # Authors
    if authors_filter and authors_filter.get("use", False):
        if not silence:
            print('Iniciando filtro de autores...')
        df_filtered = filter_authors(
            df=df_filtered,
            author_names=authors_filter["author_names"],
            match_all=authors_filter["match_all"],
            exclude_empty_values=authors_filter['exclude_empty_values']
        )

    # Advisors
    if advisors_filter and advisors_filter.get("use", False):
        if not silence:
            print('Iniciando filtro de orientadores...')
        df_filtered = filter_advisors(
            df=df_filtered,
            advisor_names=advisors_filter["advisor_names"],
            match_all=advisors_filter["match_all"],
            exclude_empty_values=advisors_filter["exclude_empty_values"]
        )

    return df_filtered
