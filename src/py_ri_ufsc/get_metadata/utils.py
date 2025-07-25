import pyarrow.parquet as pq
import pyarrow.dataset as ds
import pandas as pd
import pooch
import os

from . .config import DATASET_PARQUET_FILE_PATH

def download_ri_ufsc_dataset_via_hugging_face() -> str:
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

def get_available_values_in_dataset(column_name : str,silence : bool = True) -> list[str]:
    try:
        df = pd.read_parquet(DATASET_PARQUET_FILE_PATH,columns=[column_name])
        counts = df[column_name].value_counts(dropna=True)
    except Exception as e:
        if not silence:
            print(f'Erro na função get_available_values_in_dataset() --> {e}')
        return []
    else:
        return [f"{str(item)} ({count})" for item, count in counts.items()]

def get_raw_dataset(columns_to_use : list[str]) -> pd.DataFrame:
    if columns_to_use:
        return pd.read_parquet(DATASET_PARQUET_FILE_PATH,columns=columns_to_use)
    else:
        return pd.read_parquet(DATASET_PARQUET_FILE_PATH)

def get_available_columns_in_dataset() -> list[str]:
    """
    Retorna a lista de colunas de um arquivo Parquet sem carregar os dados na memória.

    Returns:
        list[str]: Lista com os nomes das colunas
    """
    parquet_file = pq.ParquetFile(DATASET_PARQUET_FILE_PATH)
    return parquet_file.schema.names

def get_filtered_raw_dataset(columns_to_use: list[str],
                             filter_links: list[str]) -> pd.DataFrame:
    """
    Carrega eficientemente um subconjunto de colunas e linhas de um Parquet grande,
    filtrando pelas colunas desejadas e valores de 'link_site'.

    Args:
        columns_to_use (list[str]): Colunas desejadas para exportação.
        filter_links (list[str]): Lista de 'link_site' a manter.

    Returns:
        pd.DataFrame: DataFrame resultante com as colunas e linhas filtradas.
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
