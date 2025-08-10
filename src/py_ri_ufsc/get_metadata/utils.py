import pyarrow.parquet as pq
import pyarrow.dataset as ds
import pandas as pd
import pooch
import os

from . .config import DATASET_PARQUET_FILE_PATH

def download_ri_ufsc_dataset_via_hugging_face() -> str:
    """
    ### Funcionalidades
    - Baixa o arquivo de dataset principal (em formato Parquet) do seu repositório no Hugging Face Hub.
    - Utiliza a biblioteca `pooch` para gerenciar o download, que inclui uma barra de progresso para o usuário.
    - Salva o arquivo em um caminho local predefinido, determinado pela constante `DATASET_PARQUET_FILE_PATH`.
    - O `pooch` gerencia o cache, então o download só é realizado se o arquivo não existir localmente ou estiver desatualizado (se um hash fosse fornecido).
    - Exibe mensagens informativas no console para guiar o usuário durante o processo.

    ### Parâmetros
    - Nenhum.

    ### Saídas
    - str: O caminho local completo para o arquivo de dataset baixado.
    """
    print('\n\nEstamos baixando o dataset para que ele possa ser utilizado neste ambiente :)')
    print('Essa etapa de download só acontecerá uma vez no ambiente de execução atual...\n\n')
    
    url = "https://huggingface.co/datasets/igorcaetanods/ri_ufsc_dataset_2024/resolve/main/dataset.parquet" # URL direta para o arquivo no Hugging Face Hub

    filename = "dataset.parquet" # Nome local do arquivo (que será salvo na pasta aqui do pacote)

    path = pooch.retrieve(
        url=url,
        known_hash=None,
        fname=filename,
        path=os.path.dirname(DATASET_PARQUET_FILE_PATH),
        progressbar=True,
    )
    
    print('\nPronto, pode prosseguir para a utilização do dataset!\n\n')
    return path

def get_available_values_in_dataset(column_name : str,show_amount : bool = True,silence : bool = True) -> list[str]:
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
    try:
        df = pd.read_parquet(DATASET_PARQUET_FILE_PATH,columns=[column_name])
        counts = df[column_name].value_counts(dropna=True)
    except Exception as e:
        if not silence:
            print(f'Erro na função get_available_values_in_dataset() --> {e}')
        return []
    else:
        if show_amount:
            return [f"{str(item)} ({count})" for item, count in counts.items()]
        else:
            return [str(item) for item,count in counts.items()]

def get_raw_dataset(columns_to_use : list[str]) -> pd.DataFrame:
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
    if columns_to_use:
        return pd.read_parquet(DATASET_PARQUET_FILE_PATH,columns=columns_to_use)
    else:
        return pd.read_parquet(DATASET_PARQUET_FILE_PATH)

def get_available_columns_in_dataset() -> list[str]:
    """
    ### Funcionalidades
    - Retorna a lista de todas as colunas disponíveis no arquivo Parquet.
    - É extremamente eficiente, pois lê apenas os metadados (schema) do arquivo, sem carregar nenhum dado de fato.

    ### Parâmetros
    - Nenhum.

    ### Saídas
    - list[str]: Uma lista de strings com os nomes de todas as colunas do dataset.
    """
    parquet_file = pq.ParquetFile(DATASET_PARQUET_FILE_PATH)
    return parquet_file.schema.names

def get_filtered_raw_dataset(columns_to_use: list[str],
                             filter_links: list[str]) -> pd.DataFrame:
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
    # Garante que link_site está nas colunas lidas, pois é usado como filtro
    columns = list(set(columns_to_use + ['link_site']))

    # Define o dataset Parquet (pode ser particionado ou único)
    dataset = ds.dataset(DATASET_PARQUET_FILE_PATH, format="parquet")

    # Cria expressão de filtro para a coluna link_site
    filter_expr = ds.field("link_site").isin(filter_links)

    # Scanner eficiente: carrega só as colunas e linhas desejadas
    table = dataset.to_table(columns=columns, filter=filter_expr)

    df = table.to_pandas()

    # Remove 'link_site' se não estiver entre as colunas solicitadas
    if 'link_site' not in columns_to_use:
        df.drop(columns=['link_site'], inplace=True)

    return df


# def generate_export_dataset_file(columns_to_use : list[str],output_type : str = 'PARQUET'):
    
#     # Criando um uuid (uuid.uuid4() aleatório e único) e tornado-o mais curto em base64 (de 36 para 22 caracteres)
#     process_id = base64.urlsafe_b64encode(uuid.uuid4().bytes).rstrip(b'=').decode('ascii')

#     file_path_to_save = os.path.join(UI_DOWNLOADS,process_id)

#     df = get_raw_dataset(columns_to_use=columns_to_use)    
#     if output_type == 'PARQUET':        
#         df.to_parquet(file_path_to_save+'.parquet')# Botar caminho pra baixar o parquet e dps disponibilizar download
#     elif output_type == 'JSON':
#         df.to_json(file_path_to_save+'.json')
#     elif output_type == 'XLSX':
#         df.to_excel(file_path_to_save+'.xlsx',index=False)
#     elif output_type == 'CSV':
#         df.to_csv(file_path_to_save+'.csv',index=False)
    
#     return file_path_to_save
