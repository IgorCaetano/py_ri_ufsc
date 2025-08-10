import os
import logging
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

from .utils import extract_data_from_xml_file,filter_link_site_values,transform_df

def transform_and_load_extracted_data_from_ri_api(dir_path_xml_files : str,
                                                  output_parquet_path: str,
                                                  replace_existing_files: bool = True,
                                                  remove_extracted_files_after_done: bool = False,
                                                  logger: logging.Logger | None = None) -> bool:
    """
    ### Funcionalidades
    - Orquestra o pipeline completo de ETL: extrai dados de múltiplos arquivos XML, transforma-os e carrega o resultado em um único arquivo Parquet.
    - Itera sobre todos os arquivos `.xml` em um diretório de entrada.
    - Para cada arquivo, extrai os dados brutos, os transforma em um DataFrame e aplica todo o pipeline de enriquecimento através da função `transform_df`.
    - Escreve os dados processados de forma incremental (chunk a chunk) no arquivo Parquet de saída, otimizando o uso de memória.
    - Gerencia a substituição de arquivos de saída existentes e a limpeza opcional dos arquivos XML de origem após o processamento.
    - Retorna um status booleano indicando o sucesso ou a falha da operação.

    ### Parâmetros
    - dir_path_xml_files (str): O caminho para o diretório que contém os arquivos XML a serem processados.
    - output_parquet_path (str): O caminho completo onde o arquivo Parquet final será salvo.
    - replace_existing_files (bool): Se `True`, um arquivo Parquet existente no caminho de saída será removido e substituído. Se `False`, a função não fará nada se o arquivo já existir.
    - remove_extracted_files_after_done (bool): Se `True`, os arquivos XML originais serão deletados do diretório de origem após a conclusão bem-sucedida do processo.
    - logger (logging.Logger | None): Uma instância opcional de um logger para registrar o andamento, avisos e erros do processo.

    ### Saídas
    - bool: `True` se o processo for concluído com sucesso e o arquivo Parquet for gerado, `False` caso contrário.
    """
    process_status = True

    if not replace_existing_files and os.path.exists(output_parquet_path):
        if logger:
            logger.warning(f'Pulando transformação, pois replace_existing_files={str(replace_existing_files)} e já existe um arquivo "{output_parquet_path}".')
        return process_status
    else:
        if os.path.exists(output_parquet_path):
            os.remove(output_parquet_path)
        xml_file_paths = [os.path.join(dir_path_xml_files, f)
                            for f in os.listdir(dir_path_xml_files)
                            if f.endswith('.xml')]
        if not xml_file_paths:
            if logger:
                logger.warning(f"Nenhum arquivo .xml encontrado no diretório: {dir_path_xml_files}")
            return False
        else:
            if logger:
                logger.info(f"Encontrados {len(xml_file_paths)} arquivos XML para processar.")

            writer = None  # Será inicializado no primeiro chunk válido

            try:
                for xml_file_path in xml_file_paths:
                    if logger:
                        logger.info(f"Processando arquivo: {xml_file_path}...")

                    file_records = extract_data_from_xml_file(xml_file_path,logger=logger)

                    if not file_records:
                        if logger:
                            logger.warning(f"Nenhum registro extraído de {os.path.basename(xml_file_path)}.")
                    else:
                        df = pd.DataFrame(file_records)
                        df['link_site'] = filter_link_site_values(df['link_site'].to_list())
                        df['source_xml_file'] = os.path.basename(xml_file_path)
                        
                        df = transform_df(df,logger)

                        table = pa.Table.from_pandas(df)

                        if writer is None:                            
                            writer = pq.ParquetWriter(output_parquet_path, table.schema)
                            if logger:
                                logger.info('Criação do arquivo parquet de dados transformados iniciada e primeiros dados inseridos')

                        writer.write_table(table)

                        if logger:
                            logger.info(f"{len(df)} registros gravados no arquivo parquet com dados transformados a partir de {os.path.basename(xml_file_path)}.")

                if writer:
                    writer.close()
                    if logger:
                        logger.info(f'Arquivo Parquet transformado e armazenado com sucesso em: "{output_parquet_path}"')
                    process_status = True
                else:
                    if logger:
                        logger.warning('Nenhum dado foi extraído de nenhum XML. Nenhum arquivo Parquet foi gerado.')
                    process_status = False

            except Exception as e:
                if logger:
                    logger.error(f"Erro durante o processamento: {e}", exc_info=True)
                process_status = False

            finally:
                if remove_extracted_files_after_done:
                    for file_path in xml_file_paths:
                        try:
                            os.remove(file_path)
                            if logger:
                                logger.info(f"Arquivo removido: {file_path}")
                        except Exception as e:
                            if logger:
                                logger.error(f'Erro ao remover "{file_path}": {e}', exc_info=True)
                return process_status
