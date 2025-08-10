
import pandas as pd

from .utils import get_raw_dataset
from .filters import (
    filter_types,filter_dates,filter_title_by_words,filter_subjects,
    filter_authors,filter_advisors,filter_gender,filter_language,
    filter_course,filter_type_course,filter_centro,filter_campus
)

def get_filtered_dataset(type_filter : list = [],
                         date_filter: tuple = (),
                         title_filter : list = [],
                         subjects_filter : list = [],
                         authors_filter : list = [],
                         advisors_filter : list = [],
                         match_all : bool = False,
                         gender_filter : list = [],
                         just_contain : bool = True,
                         language_filter : list = [],
                         course_filter : list = [],
                         type_course_filter : list = [],
                         centro_filter : list = [],
                         campus_filter : list = [],
                         exported_columns : list[str]|None = None,
                         exclude_empty_values : bool = False,
                         replace_empty_values : str|None = None) -> pd.DataFrame:
    """
    ### Funcionalidades
    - Atua como a interface principal e unificada para consultar e filtrar o dataset do Repositório Institucional da UFSC.
    - Carrega de forma otimizada apenas as colunas necessárias para os filtros ativados, economizando memória.
    - Aplica uma série de filtros de forma sequencial, onde o resultado de um filtro se torna a entrada para o próximo.
    - Suporta múltiplos tipos de filtros, incluindo correspondência exata (ex: campus, curso), busca por palavras-chave (ex: título, autores) e intervalos (ex: datas).
    - Oferece controle granular sobre a lógica de filtragem através de parâmetros como `match_all`, `just_contain` e `exclude_empty_values`.
    - Permite ao usuário selecionar as colunas exatas que deseja no DataFrame final.
    - Opcionalmente, pode substituir todos os marcadores de valores vazios ou não identificados por uma string personalizada.

    ### Parâmetros
    - type_filter (list): Lista com os tipos de trabalho a serem mantidos (ex: ['TCC', 'ARTIGO']).
    - date_filter (tuple): Tupla com o ano de início e fim do filtro (ex: (2020, 2022)).
    - title_filter (list): Lista de palavras a serem buscadas no título.
    - subjects_filter (list): Lista de palavras-chave a serem buscadas nos assuntos.
    - authors_filter (list): Lista de nomes de autores a serem buscados.
    - advisors_filter (list): Lista de nomes de orientadores a serem buscados.
    - match_all (bool): Se `True`, filtros de texto (título, autor, etc.) exigem que *todos* os termos fornecidos estejam presentes no registro.
    - gender_filter (list): Lista de gêneros a serem filtrados (ex: ['F'], ['M']).
    - just_contain (bool): Se `True`, o filtro de gênero busca registros que *contenham* o gênero especificado (ex: 'F' corresponde a 'F' e 'F,M'). Se `False`, busca por correspondência exata.
    - language_filter (list): Lista com os códigos de idioma a serem mantidos.
    - course_filter (list): Lista com os nomes dos cursos a serem mantidos.
    - type_course_filter (list): Lista com os níveis de curso a serem mantidos ('GRAD', 'POS').
    - centro_filter (list): Lista com as siglas dos centros a serem mantidos.
    - campus_filter (list): Lista com as siglas dos campi a serem mantidos.
    - exported_columns (list[str] | None): Se fornecida, o DataFrame final conterá apenas as colunas desta lista.
    - exclude_empty_values (bool): Se `True`, registros com valores vazios no campo sendo filtrado são descartados. Se `False`, são mantidos e rotulados como 'NÃO IDENTIFICADO'/'NÃO ESPECIFICADO'.
    - replace_empty_values (str | None): Se uma string for fornecida (ex: 'N/A'), todos os valores vazios ou não identificados no resultado final serão substituídos por ela.

    ### Saídas
    - pd.DataFrame: Um DataFrame do pandas contendo os dados que correspondem a todos os critérios de filtro aplicados.
    """
    columns_to_use = ['link_site']
    if type_filter:
        columns_to_use.append('type')        
    if date_filter:
        columns_to_use.append('year')
    if title_filter:
        columns_to_use.append('title')        
    if subjects_filter:
        columns_to_use.append('subjects')        
    if authors_filter:
        columns_to_use.append('authors')        
    if advisors_filter:
        columns_to_use.append('advisors')        
    if gender_filter:
        columns_to_use.append('gender_name')
    if language_filter:
        columns_to_use.append('language')
    if course_filter:
        columns_to_use.append('course')        
    if type_course_filter:
        columns_to_use.append('type_course')        
    if centro_filter:
        columns_to_use.append('centro')        
    if campus_filter:
        columns_to_use.append('campus')        

    if exported_columns:        
        df = get_raw_dataset(columns_to_use=list(set(columns_to_use+exported_columns)))
    else:    
        df = get_raw_dataset(columns_to_use=columns_to_use)

    df_filtered = df.copy().reset_index().drop(columns=['index'])    
    
    # Datas
    if date_filter:        
        df_filtered = filter_dates(
            df=df_filtered,
            date_1=date_filter[0],
            date_2=date_filter[1],
            exclude_empty_values=exclude_empty_values
        )

    # Tipos
    if type_filter:
        df_filtered = filter_types(
            df=df_filtered,
            types=type_filter,
            exclude_empty_values=exclude_empty_values
        )

    # Language
    if language_filter:
        df_filtered = filter_language(
            df=df_filtered,
            languages=language_filter,
            exclude_empty_values=exclude_empty_values
        )

    # Centro
    if centro_filter:
        df_filtered = filter_centro(
            df=df_filtered,
            centros=centro_filter,
            exclude_empty_values=exclude_empty_values
        )

    # Campus
    if campus_filter:
        df_filtered = filter_campus(
            df=df_filtered,
            campuses=campus_filter,
            exclude_empty_values=exclude_empty_values
        )

    # Course
    if course_filter:
        df_filtered = filter_course(
            df=df_filtered,
            courses=course_filter,
            exclude_empty_values=exclude_empty_values
        )

    # Type Course
    if type_course_filter:
        df_filtered = filter_type_course(
            df=df_filtered,
            type_courses=type_course_filter,
            exclude_empty_values=exclude_empty_values
        )

    # Gender
    if gender_filter:
        df_filtered = filter_gender(
            df=df_filtered,
            genders=gender_filter,
            just_contain=just_contain,
            exclude_empty_values=exclude_empty_values
        )

    # Título
    if title_filter:
        df_filtered = filter_title_by_words(
            df=df_filtered,
            words=title_filter,
            match_all=match_all,
            exclude_empty_values=exclude_empty_values
        )

    # Subjects
    if subjects_filter:
        df_filtered = filter_subjects(
            df=df_filtered,
            subjects=subjects_filter,
            match_all=match_all,
            exclude_empty_values=exclude_empty_values
        )

    # Authors
    if authors_filter:
        df_filtered = filter_authors(
            df=df_filtered,
            author_names=authors_filter,
            match_all=match_all,
            exclude_empty_values=exclude_empty_values
        )

    # Advisors
    if advisors_filter:
        df_filtered = filter_advisors(
            df=df_filtered,
            advisor_names=advisors_filter,
            match_all=match_all,
            exclude_empty_values=exclude_empty_values
        )

    if exported_columns:
        df_filtered.drop(columns=[c for c in df_filtered.columns if c not in exported_columns],
                         inplace=True)

    if replace_empty_values:
        df_filtered.replace(to_replace=['NÃO ESPECIFICADO','','NÃO IDENTIFICADO'],
                            value=replace_empty_values,
                            inplace=True)

    return df_filtered


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
    """
    Função com objetivo igual a `get_filtered_dataset()`, mas projetada de forma diferente, 
    especificamente para a aplicação **`py_ri_ufsc_web`**.
    """
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
