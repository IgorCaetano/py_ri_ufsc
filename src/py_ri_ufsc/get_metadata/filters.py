import re
import pandas as pd
from . .common.for_strings import format_text

def clean_empty_rows(df: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    """
    ### Funcionalidades
    - Remove linhas de um DataFrame que contenham valores nulos (NaN) ou strings vazias em uma ou mais colunas especificadas.
    - Garante que a operação seja feita em uma cópia do DataFrame para evitar efeitos colaterais (SettingWithCopyWarning).
    - Reseta o índice do DataFrame resultante para manter a continuidade.

    ### Parâmetros
    - df (pd.DataFrame): O DataFrame a ser limpo.
    - columns (list[str]): Uma lista de nomes de colunas a serem verificadas para valores vazios.

    ### Saídas
    - pd.DataFrame: Um novo DataFrame sem as linhas que continham valores vazios nas colunas especificadas.
    """
    # Garante que os índices não estão duplicados
    df = df.copy()

    for col in columns:
        if col in df.columns:
            df = df.loc[df[col].notna() &(df[col] != '')].copy()
    
    df.reset_index(drop=True, inplace=True)
    return df


def filter_types(df: pd.DataFrame, types: list[str], exclude_empty_values: bool = True) -> pd.DataFrame:
    """
    ### Funcionalidades
    - Filtra as linhas de um DataFrame com base nos valores da coluna 'type'.
    - Mantém apenas os registros cujo tipo está presente na lista `types` fornecida.
    - Opcionalmente, pode incluir registros cujo tipo é 'NÃO ESPECIFICADO' se `exclude_empty_values` for `False`.

    ### Parâmetros
    - df (pd.DataFrame): O DataFrame a ser filtrado.
    - types (list[str]): Uma lista de strings contendo os valores de 'type' a serem mantidos.
    - exclude_empty_values (bool): Se `False`, inclui também as linhas onde o tipo é 'NÃO ESPECIFICADO'. Se `True`, filtra estritamente pela lista `types`.

    ### Saídas
    - pd.DataFrame: Um novo DataFrame contendo apenas as linhas que correspondem aos critérios de filtro.
    """
    df = df.copy()
    # if not exclude_empty_values: # Comentando porque já foi tratado anteriormente
    #     df['type'].replace({'':'NÃO IDENTIFICADO'},inplace=True)
    # df = clean_empty_rows(df=df, columns=['type'])  # Assumindo que limpa NaN substituindo por ""
    
    if not exclude_empty_values:
        mask = df['type'].isin(types) | (df['type'] == 'NÃO ESPECIFICADO')
    else:
        mask = df['type'].isin(types)
    return df[mask]

def filter_dates(df: pd.DataFrame, date_1: int, date_2: int,exclude_empty_values : bool = True) -> pd.DataFrame:
    """
    ### Funcionalidades
    - Filtra as linhas de um DataFrame com base em um intervalo de anos (inclusivo), utilizando a coluna 'year'.
    - Converte a coluna 'year' para um tipo numérico para a comparação, descartando valores que não podem ser convertidos.
    - Opcionalmente, pode preservar as linhas onde o ano não foi identificado, rotulando-as como 'NÃO IDENTIFICADO' e mantendo-as no resultado final.

    ### Parâmetros
    - df (pd.DataFrame): O DataFrame a ser filtrado.
    - date_1 (int): O ano de início do intervalo do filtro.
    - date_2 (int): O ano de fim do intervalo do filtro.
    - exclude_empty_values (bool): Se `False`, mantém as linhas com ano não identificado no resultado final. Se `True`, descarta essas linhas.

    ### Saídas
    - pd.DataFrame: Um novo DataFrame contendo apenas as linhas que estão dentro do intervalo de datas especificado (e opcionalmente as linhas sem data).
    """
    df = df.copy()
    
    if not exclude_empty_values:
        df_empty_values = df[(df['year']=='') | (df['year'].isna()) | (df['year'].isnull())]
        df_empty_values.loc[:, 'year'] = 'NÃO IDENTIFICADO'
        df = df.drop(df_empty_values.index)
    # Tenta converter para inteiro e remove valores inválidos
    df['year'] = pd.to_numeric(df['year'], errors='coerce')    
    df = clean_empty_rows(df=df,columns=['year'])  # Remove linhas que não puderam ser convertidas
    df['year'] = df['year'].astype(int)

    # Aplica filtro numérico
    filtered_df = df[(df['year'] >= date_1) & (df['year'] <= date_2)]

    if exclude_empty_values:
        return filtered_df
    else:
        return pd.concat([filtered_df,df_empty_values])

def filter_title_by_words(df: pd.DataFrame,
                          words: list[str],
                          match_all: bool = False,
                          exclude_empty_values: bool = True) -> pd.DataFrame:
    """
    ### Funcionalidades
    - Filtra as linhas de um DataFrame buscando por uma ou mais palavras-chave na coluna 'title'.
    - Realiza uma busca normalizada, ignorando acentos, capitalização e caracteres especiais tanto nas palavras-chave quanto nos títulos.
    - Permite configurar o filtro para corresponder a *todas* as palavras (`match_all=True`) ou a *qualquer uma* delas (`match_all=False`).
    - Opcionalmente, pode preservar as linhas onde o título não foi identificado.

    ### Parâmetros
    - df (pd.DataFrame): O DataFrame a ser filtrado.
    - words (list[str]): A lista de palavras-chave a serem buscadas.
    - match_all (bool): Se `True`, um título deve conter todas as palavras da lista. Se `False`, basta conter uma delas.
    - exclude_empty_values (bool): Se `False`, mantém as linhas com título não identificado no resultado final. Se `True`, descarta essas linhas.

    ### Saídas
    - pd.DataFrame: Um novo DataFrame contendo apenas as linhas cujos títulos correspondem aos critérios de busca.
    """
    df = df.copy()

    # Isola os títulos vazios se for manter
    if not exclude_empty_values:
        df_empty_values = df[(df['title'] == '') | (df['title'].isna()) | (df['title'].isnull())].copy()
        df_empty_values.loc[:, 'title'] = 'NÃO IDENTIFICADO'
        df = df.drop(df_empty_values.index) # Remove do df principal para não aplicar filtro neles
    else:
        # Remove linhas com título vazio
        df = clean_empty_rows(df=df, columns=['title'])

    # Normaliza e escapa as palavras para regex
    words_formatted = [re.escape(format_text(word, special_treatment=True).strip()) for word in words]
    pattern = '|'.join(words_formatted)

    # Define a máscara de filtro
    if match_all:
        mask = df['title'].apply(
            lambda t: all(
                re.search(w, format_text(t, special_treatment=True), flags=re.IGNORECASE)
                for w in words_formatted
            )
        )
    else:
        mask = df['title'].apply(
            lambda t: re.search(pattern, format_text(t, special_treatment=True), flags=re.IGNORECASE) is not None
        )

    filtered = df[mask]

    if exclude_empty_values:
        return filtered
    else:
        # Retorna filtrados + os títulos originalmente vazios (agora com 'NÃO IDENTIFICADO')
        return pd.concat([filtered, df_empty_values])


def filter_subjects(df: pd.DataFrame,
                    subjects: list[str],
                    match_all: bool = False,
                    exclude_empty_values : bool = True) -> pd.DataFrame:
    """
    ### Funcionalidades
    - Filtra as linhas de um DataFrame buscando por uma ou mais palavras-chave na coluna 'subjects'.
    - A coluna 'subjects' pode conter múltiplos valores separados por ponto e vírgula (';').
    - Realiza uma busca normalizada, ignorando acentos e capitalização.
    - Permite configurar o filtro para corresponder a *todas* as palavras-chave (`match_all=True`) ou a *qualquer uma* delas (`match_all=False`).
    - Opcionalmente, pode preservar as linhas onde os assuntos não foram identificados.

    ### Parâmetros
    - df (pd.DataFrame): O DataFrame a ser filtrado.
    - subjects (list[str]): A lista de assuntos (palavras-chave) a serem buscados.
    - match_all (bool): Se `True`, um registro deve conter todos os assuntos da lista. Se `False`, basta conter um deles.
    - exclude_empty_values (bool): Se `False`, mantém as linhas sem assuntos no resultado final. Se `True`, descarta essas linhas.

    ### Saídas
    - pd.DataFrame: Um novo DataFrame contendo apenas as linhas que correspondem aos critérios de busca por assunto.
    """
    df = df.copy()

    if not exclude_empty_values:
        df_empty_values = df[(df['subjects']=='') | (df['subjects'].isna()) | (df['subjects'].isnull())]
        df_empty_values.loc[:, 'subjects'] = 'NÃO IDENTIFICADO'
        df = df.drop(df_empty_values.index)
    else:
        # Remove linhas sem subjects
        df = clean_empty_rows(df=df,columns=['subjects'])

    # Normaliza os assuntos de entrada
    subjects_formatted = [format_text(s, special_treatment=True).strip() for s in subjects]

    # Função para verificar se algum assunto está presente
    def subject_match(row_subjects):
        row_subjects_split = row_subjects.split(';')
        row_subjects_formatted = [format_text(s.strip(), special_treatment=True) for s in row_subjects_split if s.strip()]
        if match_all:
            return all(any(word in subject for subject in row_subjects_formatted) for word in subjects_formatted)
        else:
            return any(any(word in subject for subject in row_subjects_formatted) for word in subjects_formatted)

    mask = df['subjects'].apply(subject_match)
    if exclude_empty_values:
        return df[mask]
    else:
        return pd.concat([df[mask],df_empty_values])

# Pega buscando "Igor Caetano" para authors = "Igor C Souza"
# Match all = True tem q conter todos os autores
def filter_authors(df: pd.DataFrame,
                   author_names: list[str],
                   match_all: bool = False,
                   exclude_empty_values: bool = True) -> pd.DataFrame:
    """
    ### Funcionalidades
    - Filtra o DataFrame por nomes de autores com uma lógica de correspondência avançada.
    - Lida com nomes no formato "Sobrenome, Nome" e nomes diretos.
    - Permite correspondência flexível, onde nomes abreviados (ex: "I C Souza") podem corresponder a nomes completos (ex: "Igor Caetano Souza").
    - Utiliza funções auxiliares para reordenar as partes do nome e realizar a correspondência ordenada.
    - Permite filtrar por múltiplos autores, exigindo a presença de *todos* (`match_all=True`) ou de *pelo menos um* (`match_all=False`).
    - Opcionalmente, pode preservar registros sem autores.

    ### Parâmetros
    - df (pd.DataFrame): O DataFrame a ser filtrado.
    - author_names (list[str]): Uma lista com os nomes dos autores a serem buscados.
    - match_all (bool): Se `True`, um registro deve conter todos os autores da lista. Se `False`, basta conter um deles.
    - exclude_empty_values (bool): Se `False`, mantém as linhas sem autores no resultado final.

    ### Saídas
    - pd.DataFrame: Um novo DataFrame contendo apenas as linhas que correspondem aos autores especificados.
    """
    df = df.copy()

    if not exclude_empty_values:
        df_empty_values = df[(df['authors'] == '') | (df['authors'].isna()) | (df['authors'].isnull())]
        df_empty_values.loc[:, 'authors'] = 'NÃO IDENTIFICADO'
        df = df.drop(df_empty_values.index)
    else:
        df = clean_empty_rows(df=df, columns=['authors']) 

    def ordered_match(input_parts: list[str], target_parts: list[str]) -> bool:
        """Verifica se os input_parts estão contidos nos target_parts em ordem, permitindo abreviações."""
        if not (input_parts and target_parts):
            return False
        if input_parts[0] != target_parts[0]:
            if not (len(target_parts[0]) == 1 and input_parts[0].startswith(target_parts[0])):
                return False
        for input_part in input_parts[1:]:
            found_input = False
            if input_part not in target_parts:
                for target_part in target_parts[1:]:
                    if len(target_part) == 1 and input_part.startswith(target_part):
                        found_input = True
                        break
            else:
                found_input = True
            if not found_input:
                return False
        return True
        
    def reorder_author_name_parts(author_name: str) -> list[str]:
        """
        Trata nomes no estilo 'Sobrenome, Nome' antes de normalizar.
        Reordena para ['nome', ..., 'sobrenome'].
        """
        if ',' in author_name:
            pre, post = author_name.split(',', 1)
            parts = post.strip().split() + [pre.strip()]
        else:
            parts = author_name.strip().split()
        return [format_text(p, special_treatment=True) for p in parts if p.strip()]

    author_name_parts_list = [reorder_author_name_parts(name) for name in author_names if name.strip()]

    def author_match(authors_raw: str) -> bool:
        authors_list = authors_raw.split(';')
        authors_processed = [reorder_author_name_parts(author) for author in authors_list]

        results = []
        for input_parts in author_name_parts_list:
            if not input_parts:
                continue
            matched = any(
                ordered_match(input_parts, author_parts)
                for author_parts in authors_processed
            )
            results.append(matched)

        return all(results) if match_all else any(results)

    mask = df['authors'].apply(author_match)

    if exclude_empty_values:
        return df[mask]
    else:
        return pd.concat([df[mask], df_empty_values])

# Pega buscando "Igor Caetano" para advisors = "Igor C Souza"
# Match all = True tem q conter todos os autores
def filter_advisors(df: pd.DataFrame,
                    advisor_names: list[str],
                    match_all: bool = False,
                    exclude_empty_values : bool = True) -> pd.DataFrame:
    """
    ### Funcionalidades
    - Filtra o DataFrame por nomes de orientadores, aplicando a mesma lógica de correspondência avançada da função `filter_authors`.
    - Lida com nomes no formato "Sobrenome, Nome" e permite correspondência com abreviações.
    - Permite filtrar por múltiplos orientadores, exigindo a presença de *todos* (`match_all=True`) ou de *pelo menos um* (`match_all=False`).
    - Opcionalmente, pode preservar registros sem orientadores.

    ### Parâmetros
    - df (pd.DataFrame): O DataFrame a ser filtrado.
    - advisor_names (list[str]): Uma lista com os nomes dos orientadores a serem buscados.
    - match_all (bool): Se `True`, um registro deve conter todos os orientadores da lista. Se `False`, basta conter um deles.
    - exclude_empty_values (bool): Se `False`, mantém as linhas sem orientadores no resultado final.

    ### Saídas
    - pd.DataFrame: Um novo DataFrame contendo apenas as linhas que correspondem aos orientadores especificados.
    """
    df = df.copy()

    if not exclude_empty_values:
        df_empty_values = df[(df['advisors'] == '') | (df['advisors'].isna()) | (df['advisors'].isnull())]
        df_empty_values.loc[:, 'advisors'] = 'NÃO IDENTIFICADO'
        df = df.drop(df_empty_values.index)
    else:
        df = clean_empty_rows(df=df, columns=['advisors']) 

    def ordered_match(input_parts: list[str], target_parts: list[str]) -> bool:
        """Verifica se os input_parts estão contidos nos target_parts em ordem, permitindo abreviações."""
        if not (input_parts and target_parts):
            return False
        if input_parts[0] != target_parts[0]:
            if not (len(target_parts[0]) == 1 and input_parts[0].startswith(target_parts[0])):
                return False
        for input_part in input_parts[1:]:
            found_input = False
            if input_part not in target_parts:
                for target_part in target_parts[1:]:
                    if len(target_part) == 1 and input_part.startswith(target_part):
                        found_input = True
                        break
            else:
                found_input = True
            if not found_input:
                return False
        return True
        
    def reorder_advisor_name_parts(advisor_name: str) -> list[str]:
        """
        Trata nomes no estilo 'Sobrenome, Nome' antes de normalizar.
        Reordena para ['nome', ..., 'sobrenome'].
        """
        if ',' in advisor_name:
            pre, post = advisor_name.split(',', 1)
            parts = post.strip().split() + [pre.strip()]
        else:
            parts = advisor_name.strip().split()
        return [format_text(p, special_treatment=True) for p in parts if p.strip()]

    advisor_name_parts_list = [reorder_advisor_name_parts(name) for name in advisor_names if name.strip()]

    def advisor_match(advisors_raw: str) -> bool:
        advisors_list = advisors_raw.split(';')
        advisors_processed = [reorder_advisor_name_parts(advisor) for advisor in advisors_list]

        results = []
        for input_parts in advisor_name_parts_list:
            if not input_parts:
                continue
            matched = any(
                ordered_match(input_parts, author_parts)
                for author_parts in advisors_processed
            )
            results.append(matched)

        return all(results) if match_all else any(results)

    mask = df['advisors'].apply(advisor_match)

    if exclude_empty_values:
        return df[mask]
    else:
        return pd.concat([df[mask], df_empty_values])

def filter_gender(df: pd.DataFrame,
                  genders: list[str],
                  just_contain: bool = True,
                  exclude_empty_values : bool = False) -> pd.DataFrame:
    """
    ### Funcionalidades
    - Filtra o DataFrame com base na coluna 'gender_name'.
    - Permite dois modos de operação:
    - 1. `just_contain=True`: Mantém registros que contenham *pelo menos um* dos gêneros especificados (ex: filtrar por 'F' manterá registros 'F' e 'F,M').
    - 2. `just_contain=False`: Mantém registros que correspondam *exatamente* a um dos valores na lista de gêneros.
    - Opcionalmente, pode preservar registros sem gênero identificado.

    ### Parâmetros
    - df (pd.DataFrame): O DataFrame a ser filtrado.
    - genders (list[str]): Uma lista de gêneros a serem buscados (ex: ['F'], ['M'], ['F', 'M']).
    - just_contain (bool): Define o modo de correspondência (conter ou ser exato).
    - exclude_empty_values (bool): Se `False`, mantém as linhas sem gênero no resultado final.

    ### Saídas
    - pd.DataFrame: Um novo DataFrame contendo apenas as linhas que correspondem ao filtro de gênero.
    """
    df = df.copy()
    if not exclude_empty_values:
        df_empty_values = df[(df['gender_name']=='') | (df['gender_name'].isna()) | (df['gender_name'].isnull())]
        df_empty_values.loc[:, 'gender_name'] = 'NÃO IDENTIFICADO'
        df = df.drop(df_empty_values.index)
    else:
        df = clean_empty_rows(df=df,columns=['gender_name'])

    if just_contain:
        def match_any(g):
            if exclude_empty_values:
                return any(gender in g.split(',') for gender in genders)
            else:
                return any(gender in g.split(',') for gender in genders+[''])
        mask = df['gender_name'].apply(match_any)
    else:
        mask = df['gender_name'].isin(genders)

    if exclude_empty_values:
        return df[mask]
    else:
        return pd.concat([df[mask],df_empty_values])

def filter_language(df: pd.DataFrame,
                    languages: list[str],
                    exclude_empty_values : bool = False) -> pd.DataFrame:
    """
    ### Funcionalidades
    - Filtra as linhas de um DataFrame com base nos valores da coluna 'language'.
    - Mantém apenas os registros cujo idioma está presente na lista `languages` fornecida.
    - Opcionalmente, pode incluir registros sem idioma definido, que são então rotulados como 'NÃO IDENTIFICADO'.

    ### Parâmetros
    - df (pd.DataFrame): O DataFrame a ser filtrado.
    - languages (list[str]): Uma lista de strings contendo os códigos de idioma a serem mantidos.
    - exclude_empty_values (bool): Se `False`, inclui também as linhas onde o idioma está ausente.

    ### Saídas
    - pd.DataFrame: Um novo DataFrame contendo apenas as linhas que correspondem ao filtro de idioma.
    """
    df = df.copy()

    # if exclude_empty_values:
    #     df = clean_empty_rows(df, columns=['language'])
    if not exclude_empty_values:
        mask = df['language'].isin(languages) | (df['language'] == "") | (df['language'].isna()) | (df['language'].isnull())
    else:
        mask = df['language'].isin(languages)
    # df = df[mask]
    if exclude_empty_values:
        return df[mask]
    else:
        df = df[mask]
        df['language'] = df['language'].replace({'': 'NÃO IDENTIFICADO'})
        return df

def filter_course(df: pd.DataFrame,
                  courses: list[str],
                  exclude_empty_values : bool = False) -> pd.DataFrame:
    """
    ### Funcionalidades
    - Filtra as linhas de um DataFrame com base nos valores da coluna 'course'.
    - Mantém apenas os registros cujo nome do curso está presente na lista `courses` fornecida.
    - Opcionalmente, pode incluir registros sem curso definido, que são então rotulados como 'NÃO IDENTIFICADO'.

    ### Parâmetros
    - df (pd.DataFrame): O DataFrame a ser filtrado.
    - courses (list[str]): Uma lista de strings contendo os nomes dos cursos a serem mantidos.
    - exclude_empty_values (bool): Se `False`, inclui também as linhas onde o curso está ausente.

    ### Saídas
    - pd.DataFrame: Um novo DataFrame contendo apenas as linhas que correspondem ao filtro de curso.
    """
    df = df.copy()
    # if exclude_empty_values:
    #     df = clean_empty_rows(df=df,columns=['course'])
    if not exclude_empty_values:
        mask = df['course'].isin(courses) | (df['course'] == "") | (df['course'].isna()) | (df['course'].isnull())
    else:
        mask = df['course'].isin(courses)
    if exclude_empty_values:
        return df[mask]
    else:
        df = df[mask]
        df['course'] = df['course'].replace({'': 'NÃO IDENTIFICADO'})
        return df

def filter_type_course(df: pd.DataFrame,
                       type_courses: list[str],
                       exclude_empty_values: bool = False) -> pd.DataFrame:
    """
    ### Funcionalidades
    - Filtra as linhas de um DataFrame com base nos valores da coluna 'type_course' (GRAD ou POS).
    - Mantém apenas os registros cujo tipo de curso está presente na lista `type_courses` fornecida.
    - Opcionalmente, pode incluir registros sem tipo de curso definido, que são então rotulados como 'NÃO IDENTIFICADO'.

    ### Parâmetros
    - df (pd.DataFrame): O DataFrame a ser filtrado.
    - type_courses (list[str]): Uma lista de strings contendo os tipos de curso a serem mantidos.
    - exclude_empty_values (bool): Se `False`, inclui também as linhas onde o tipo de curso está ausente.

    ### Saídas
    - pd.DataFrame: Um novo DataFrame contendo apenas as linhas que correspondem ao filtro de tipo de curso.
    """
    df = df.copy()
    # if exclude_empty_values:
    #     df = clean_empty_rows(df=df,columns=['type_course'])
    if not exclude_empty_values:
        mask = df['type_course'].isin(type_courses) | (df['type_course'] == "") | (df['type_course'].isna()) | (df['type_course'].isnull())
    else:
        mask = df['type_course'].isin(type_courses)
    if exclude_empty_values:
        return df[mask]
    else:
        df = df[mask]
        df['type_course'] = df['type_course'].replace({'': 'NÃO IDENTIFICADO'})
        return df

def filter_centro(df: pd.DataFrame, centros: list[str], exclude_empty_values: bool = False) -> pd.DataFrame:
    """
    ### Funcionalidades
    - Filtra as linhas de um DataFrame com base nos valores da coluna 'centro'.
    - Mantém apenas os registros cuja sigla do centro está presente na lista `centros` fornecida.
    - Opcionalmente, pode incluir registros sem centro definido, que são então rotulados como 'NÃO IDENTIFICADO'.

    ### Parâmetros
    - df (pd.DataFrame): O DataFrame a ser filtrado.
    - centros (list[str]): Uma lista de strings contendo as siglas dos centros a serem mantidos.
    - exclude_empty_values (bool): Se `False`, inclui também as linhas onde o centro está ausente.

    ### Saídas
    - pd.DataFrame: Um novo DataFrame contendo apenas as linhas que correspondem ao filtro de centro.
    """
    df = df.copy()
    # if exclude_empty_values:
    #     df = clean_empty_rows(df=df,columns=['centro'])
    if not exclude_empty_values:
        mask = df['centro'].isin(centros) | (df['centro'] == "") | (df['centro'].isna()) | (df['centro'].isnull())
    else:
        mask = df['centro'].isin(centros)
    if exclude_empty_values:
        return df[mask]
    else:
        df = df[mask]
        df['centro'] = df['centro'].replace({'': 'NÃO IDENTIFICADO'})
        return df

def filter_campus(df: pd.DataFrame,
                  campuses: list[str],
                  exclude_empty_values: bool = False) -> pd.DataFrame:
    """
    ### Funcionalidades
    - Filtra as linhas de um DataFrame com base nos valores da coluna 'campus'.
    - Mantém apenas os registros cuja sigla do campus está presente na lista `campuses` fornecida.
    - Opcionalmente, pode incluir registros sem campus definido, que são então rotulados como 'NÃO IDENTIFICADO'.

    ### Parâmetros
    - df (pd.DataFrame): O DataFrame a ser filtrado.
    - campuses (list[str]): Uma lista de strings contendo as siglas dos campi a serem mantidos.
    - exclude_empty_values (bool): Se `False`, inclui também as linhas onde o campus está ausente.

    ### Saídas
    - pd.DataFrame: Um novo DataFrame contendo apenas as linhas que correspondem ao filtro de campus.
    """
    df = df.copy()
    # if exclude_empty_values:
    #     df = clean_empty_rows(df=df,columns=['campus'])
    if not exclude_empty_values:
        mask = df['campus'].isin(campuses) | (df['campus'] == "") | (df['campus'].isna()) | (df['campus'].isnull())
    else:
        mask = df['campus'].isin(campuses)
    if exclude_empty_values:
        return df[mask]
    else:
        df = df[mask]
        df['campus'] = df['campus'].replace({'': 'NÃO IDENTIFICADO'})
        return df
