import pandas as pd

from .get_metadata.utils import (
    get_available_values_in_dataset,get_available_columns_in_dataset,get_raw_dataset,
    get_filtered_raw_dataset
)
from .get_metadata.main import get_filtered_dataset_for_main_graphs,get_filtered_dataset
from .get_metadata.tests import TestRIUFSC


class RIUFSC():
    """
    ### Funcionalidades
    - Atua como a interface principal e simplificada para interagir com o dataset do Repositório Institucional da UFSC.
    - Encapsula a complexidade das funções de download, acesso e filtragem de dados, oferecendo métodos diretos e fáceis de usar.
    - Fornece funções de ajuda e métodos para explorar os dados disponíveis (colunas e valores) de forma otimizada, sem carregar todo o dataset na memória.
    - Permite a aplicação de múltiplos filtros combinados de forma intuitiva para obter subconjuntos de dados específicos.

    ### Parâmetros
    - silence (bool): Parâmetro de inicialização. Se `False`, exibe mensagens e avisos informativos durante o uso dos métodos. O padrão é `True`.

    ### Saídas
    - N/A (trata-se da inicialização de um objeto).
    """
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
        """
        ### Funcionalidades
        - Retorna a lista de todas as colunas disponíveis no arquivo Parquet.
        - É extremamente eficiente, pois lê apenas os metadados (schema) do arquivo, sem carregar nenhum dado de fato.

        ### Parâmetros
        - Nenhum.

        ### Saídas
        - list[str]: Uma lista de strings com os nomes de todas as colunas do dataset.
        """
        return get_available_columns_in_dataset()

    def get_available_values_in_ri_ufsc_dataset(self,column_name : str,
                                                show_amount : bool = True) -> list[str]:
        """
        ### Funcionalidades
        - Lê uma única coluna de um arquivo Parquet para listar seus valores únicos disponíveis.
        - É otimizada para não carregar o dataset inteiro na memória.
        - Calcula a contagem de ocorrências para cada valor único.
        - Opcionalmente, pode formatar a saída para incluir a contagem ao lado de cada valor (ex: "Artigo (1500)").

        ### Parâmetros
        - column_name (str): O nome da coluna cujos valores únicos serão listados.
        - show_amount (bool): Se `True`, anexa a contagem a cada valor na lista de saída.
        - silence (bool): Se `False`, imprime mensagens de erro no console em caso de falha.

        ### Saídas
        - list[str]: Uma lista de strings contendo os valores únicos da coluna, opcionalmente com suas contagens.
        """
        return get_available_values_in_dataset(column_name=column_name,silence=self.silence,
                                               show_amount=show_amount)

    def get_raw_ri_ufsc_dataset(self,columns_to_use : list[str]|None = None) -> pd.DataFrame:
        """
        ### Funcionalidades
        - Carrega dados do arquivo Parquet principal para um DataFrame do pandas.
        - Permite a seleção de um subconjunto de colunas para otimizar o uso de memória, carregando apenas o necessário.
        - Se nenhuma coluna for especificada, carrega o DataFrame completo.

        ### Parâmetros
        - columns_to_use (list[str]): Uma lista com os nomes das colunas a serem carregadas. Se vazia, todas as colunas são carregadas.

        ### Saídas
        - pd.DataFrame: O DataFrame do pandas contendo os dados solicitados.
        """
        return get_raw_dataset(columns_to_use=columns_to_use)

    def get_filtered_raw_dataset_based_on_link_site_column(self,
                                                           columns_to_use : list[str],
                                                           filter_links : list[str]) -> pd.DataFrame:
        """
        ### Funcionalidades
        - Carrega de forma altamente eficiente um subconjunto de dados de um arquivo Parquet.
        - Permite filtrar os dados tanto por colunas (selecionando quais carregar) quanto por linhas (especificando valores a serem mantidos na coluna 'link_site').
        - Utiliza o `pyarrow.dataset` para aplicar os filtros antes de carregar os dados na memória, resultando em um desempenho superior para datasets grandes.

        ### Parâmetros
        - columns_to_use (list[str]): A lista de colunas desejadas no DataFrame final.
        - filter_links (list[str]): Uma lista de valores da coluna 'link_site' a serem usados como filtro de linha.

        ### Saídas
        - pd.DataFrame: Um DataFrame do pandas contendo apenas as colunas e linhas que correspondem aos filtros.
        """
        return get_filtered_raw_dataset(columns_to_use=columns_to_use,filter_links=filter_links)

    def get_df_filtered(self,
                        type_filter : list = [],
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
        return get_filtered_dataset(type_filter=type_filter,
                                    date_filter=date_filter,
                                    title_filter=title_filter,
                                    subjects_filter=subjects_filter,
                                    authors_filter=authors_filter,
                                    advisors_filter=advisors_filter,
                                    match_all=match_all,
                                    gender_filter=gender_filter,
                                    just_contain=just_contain,
                                    language_filter=language_filter,
                                    course_filter=course_filter,
                                    type_course_filter=type_course_filter,
                                    centro_filter=centro_filter,
                                    campus_filter=campus_filter,
                                    exported_columns=exported_columns,
                                    exclude_empty_values=exclude_empty_values,
                                    replace_empty_values=replace_empty_values)

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
        """
        Função com objetivo igual a `get_df_filtered()`, mas projetada de forma diferente, 
        especificamente para a aplicação **`py_ri_ufsc_web`**.
        """
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
        """
        ### Funcionalidades
        - Cria e retorna uma instância da classe `TestRIUFSC`, projetada para testes e depuração.
        - Fornece a um desenvolvedor ou usuário avançado acesso direto às funções de transformação e filtragem para validação granular.
        - Permite que um DataFrame existente seja passado para o objeto de teste, que o utilizará como base para suas operações.

        ### Parâmetros
        - df (pd.DataFrame | None): Um DataFrame opcional para ser passado para o construtor da classe `TestRIUFSC`. Se fornecido, os métodos de teste usarão este DataFrame como ponto de partida.

        ### Saídas
        - TestRIUFSC: Uma nova instância da classe `TestRIUFSC`, pronta para ser usada para testes.
        """
        if not self.silence:
            print('A partir de agora use o objeto retornado como uma classe nova, específica para realização de testes.')
        return TestRIUFSC(df=df)
