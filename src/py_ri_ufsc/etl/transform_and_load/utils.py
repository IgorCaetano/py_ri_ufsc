import pandas as pd
import os
import logging
import requests
from bs4 import BeautifulSoup
import csv
import re

from lxml import etree
from br_gender.base import br_gender_info
from py_ri_ufsc.config import COL_TO_NAME_CSV_FILE_PATH
from py_ri_ufsc.common.for_strings import format_text
from py_ri_ufsc.etl.extraction.courses_info import CursosUFSC,DIC_CAMPUS_CURSOS_CENTROS_SIGLAS,DIC_CAMPUS_CENTROS_COMPLETO_E_SIGLAS

# Defina os namespaces globalmente para serem usados em todas as funções XPath
NAMESPACES = {
    'oai': 'http://www.openarchives.org/OAI/2.0/',
    'xoai': 'http://www.lyncode.com/xoai'
}

def format_list_to_string(data_list):
    """
    ### Funcionalidades
    - Converte uma lista de itens em uma única string, com cada item separado por um ponto e vírgula (';').
    - Remove espaços em branco das extremidades de cada item antes de juntá-los.
    - Ignora itens que se tornam vazios após a remoção dos espaços.
    - Se a entrada for uma string em vez de uma lista, retorna a própria string após remover os espaços das extremidades.
    - Retorna `None` se a lista de entrada for vazia ou se todos os seus itens forem vazios.

    ### Parâmetros
    - data_list (list | str): A lista a ser convertida ou uma string.

    ### Saídas
    - str | None: A string formatada e unida por ';', ou `None` se não houver dados válidos.
    """
    if data_list and isinstance(data_list, list):
        cleaned_list = [str(item).strip() for item in data_list if str(item).strip()]
        if not cleaned_list:
            return None
        return ';'.join(cleaned_list)
    elif isinstance(data_list, str) and data_list.strip():
        return data_list.strip()
    return None

def get_date_field(element, date_type_name):
    """
    ### Funcionalidades
    - Extrai um campo de data específico de um elemento XML usando uma consulta XPath.
    - Prioriza a busca por datas que tenham um código de idioma, na seguinte ordem: 'pt_BR', 'none', 'en'.
    - Possui uma consulta XPath de fallback para encontrar a data caso ela não esteja associada a um idioma específico.
    - Depende de uma constante externa `NAMESPACES` para resolver os prefixos do XML.

    ### Parâmetros
    - element (lxml.etree._Element): O elemento XML a partir do qual a data será extraída.
    - date_type_name (str): O nome do tipo de data a ser buscado (ex: 'issued', 'available', 'accessioned').

    ### Saídas
    - str | None: A primeira data encontrada como uma string, ou `None` se nenhuma data for localizada.
    """
    for lang_code in ['pt_BR', 'none', 'en']:
        date_elements = element.xpath(
            f"./xoai:element[@name='dc']/xoai:element[@name='date']/xoai:element[@name='{date_type_name}']/xoai:element[@name='{lang_code}']/xoai:field[@name='value']/text()",
            namespaces=NAMESPACES
        )
        if date_elements:
            dates = [date.strip() for date in date_elements if date.strip()]
            return dates[0] if dates else None
    
    date_elements = element.xpath(
        f"./xoai:element[@name='dc']/xoai:element[@name='date']/xoai:element[@name='{date_type_name}']/xoai:element/xoai:field[@name='value']/text()",
        namespaces=NAMESPACES
    )
    if date_elements:
        dates = [date.strip() for date in date_elements if date.strip()]
        return dates[0] if dates else None
    return None

def get_specific_dc_field(element, dc_element_name : str, sub_elements=None):
    """
    ### Funcionalidades
    - Extrai de forma genérica um ou mais valores de um campo Dublin Core (DC) de um elemento XML.
    - Constrói a consulta XPath dinamicamente, permitindo navegar por sub-elementos.
    - Realiza múltiplas tentativas de busca com XPaths diferentes para lidar com variações na estrutura do XML, priorizando campos com códigos de idioma ('pt_BR', 'none', 'en').
    - Agrega todos os valores encontrados, remove duplicatas e os retorna como uma única string separada por ';'.
    - Depende da constante `NAMESPACES` e da função `format_list_to_string`.

    ### Parâmetros
    - element (lxml.etree._Element): O elemento XML a ser consultado.
    - dc_element_name (str): O nome do campo DC principal a ser buscado (ex: 'creator', 'subject').
    - sub_elements (list[str] | None): Uma lista opcional de nomes de sub-elementos para refinar a busca na hierarquia do XML.

    ### Saídas
    - str | None: Uma string contendo todos os valores únicos encontrados, separados por ';', ou `None` se nenhum valor for localizado.
    """
    base_xpath = f"./xoai:element[@name='dc']/xoai:element[@name='{dc_element_name}']"
    if sub_elements:
        for sub in sub_elements:
            base_xpath += f"/xoai:element[@name='{sub}']"

    collected_values = []
    for lang_code in ['pt_BR', 'none', 'en']:
        field_elements = element.xpath(
            f"{base_xpath}/xoai:element[@name='{lang_code}']/xoai:field[@name='value']/text()",
            namespaces=NAMESPACES
        )
        if field_elements:
            collected_values.extend([val.strip() for val in field_elements if val.strip()])
            if collected_values: break

    if not collected_values:
        field_elements = element.xpath(
            f"{base_xpath}/xoai:element/xoai:field[@name='value']/text()",
            namespaces=NAMESPACES
        )
        if field_elements:
            collected_values.extend([val.strip() for val in field_elements if val.strip()])

    if not collected_values:
        field_elements = element.xpath(
            f"{base_xpath}/xoai:field[@name='value']/text()",
            namespaces=NAMESPACES
        )
        if field_elements:
            collected_values.extend([val.strip() for val in field_elements if val.strip()])
            
    return format_list_to_string(list(set(collected_values))) if collected_values else None

def get_main_description_field(metadata_element):
    """
    ### Funcionalidades
    - Extrai o texto do campo de descrição principal (`<dc:description>`) de um elemento XML.
    - É projetada especificamente para ignorar o conteúdo do sub-campo de resumo (`abstract`).
    - Realiza a busca com uma ordem de prioridade de idioma: 'pt_BR', 'none', e 'en'.
    - Inclui uma busca de fallback para textos que possam estar diretamente no campo de descrição, sem um nó de idioma.
    - Consolida todos os textos encontrados em uma única string, removendo duplicatas.

    ### Parâmetros
    - metadata_element (lxml.etree._Element): O elemento XML raiz da seção de metadados a ser analisada.

    ### Saídas
    - str | None: Uma string contendo a descrição encontrada, ou `None` se nenhuma for localizada.
    """
    description_dc_element = metadata_element.xpath(
        "./xoai:element[@name='dc']/xoai:element[@name='description']",
        namespaces=NAMESPACES
    )
    if not description_dc_element:
        return None
    
    description_node = description_dc_element[0]
    description_texts = []

    for lang_code in ['pt_BR', 'none', 'en']:
        lang_elements = description_node.xpath(
            f"./xoai:element[@name='{lang_code}' and not(local-name()='element' and @name='abstract')]/xoai:field[@name='value']/text()",
            namespaces=NAMESPACES
        )
        if lang_elements:
            description_texts.extend([text.strip() for text in lang_elements if text.strip()])

    direct_field_texts = description_node.xpath("./xoai:field[@name='value']/text()", namespaces=NAMESPACES)
    description_texts.extend([text.strip() for text in direct_field_texts if text.strip()])
    
    return format_list_to_string(list(set(description_texts))) if description_texts else None

def get_contributor_field_values(element, contributor_type_name):
    """
    ### Funcionalidades
    - Extrai os nomes de contribuidores (ex: autores, orientadores) de um elemento XML.
    - Busca dentro do campo `<dc:contributor>` por um tipo específico (ex: 'author', 'advisor').
    - Prioriza a busca por valores associados a um idioma ('pt_BR', 'none', 'en').
    - Possui múltiplos XPaths de fallback para capturar valores em estruturas XML variadas.
    - Retorna uma lista de valores únicos, sem duplicatas.

    ### Parâmetros
    - element (lxml.etree._Element): O elemento XML a ser consultado.
    - contributor_type_name (str): O tipo de contribuidor a ser extraído (ex: 'author', 'advisor', 'advisor-co').

    ### Saídas
    - list[str]: Uma lista de strings, onde cada string é um nome de contribuidor encontrado. Retorna uma lista vazia se nenhum for encontrado.
    """
    base_contributor_xpath = f"./xoai:element[@name='dc']/xoai:element[@name='contributor']/xoai:element[@name='{contributor_type_name}']"
    specific_elements = element.xpath(base_contributor_xpath, namespaces=NAMESPACES)
    values_list = []
    for el in specific_elements:
        found_in_lang_specific = False
        for lang_code in ['pt_BR', 'none', 'en']:
            lang_specific_values = el.xpath(
                f"./xoai:element[@name='{lang_code}']/xoai:field[@name='value']/text()",
                namespaces=NAMESPACES
            )
            if lang_specific_values:
                values_list.extend([v.strip() for v in lang_specific_values if v.strip()])
                found_in_lang_specific = True
        if not found_in_lang_specific:
            direct_values = el.xpath("./xoai:field[@name='value']/text()", namespaces=NAMESPACES)
            if direct_values:
                values_list.extend([v.strip() for v in direct_values if v.strip()])
            else:
                # Fallback para encontrar qualquer campo de valor, caso a estrutura seja inesperada
                generic_values = el.xpath(".//xoai:field[@name='value']/text()", namespaces=NAMESPACES)
                if generic_values:
                    values_list.extend([v.strip() for v in generic_values if v.strip()])
    return list(set(values_list)) if values_list else []

def filter_link_site_values(list_of_values : list[str]) -> list[str]:
    """
    ### Funcionalidades
    - Filtra uma lista de strings, onde cada string pode conter um ou mais links separados por ';'.
    - Para cada item da lista, seleciona um único link de acordo com uma regra de prioridade.
    - Prioriza o link que contém o domínio 'repositorio.ufsc.br'.
    - Se nenhum link com o domínio preferencial for encontrado, seleciona o último link da sequência.
    - Mantém a correspondência de um para um entre a lista de entrada e a de saída.

    ### Parâmetros
    - list_of_values (list[str]): A lista de strings contendo os links a serem filtrados.

    ### Saídas
    - list[str]: Uma nova lista contendo apenas um link selecionado para cada item da lista original.
    """
    filtered_values = []
    for item in list_of_values:
        if item:
            links = item.split(';')
            # Procura o link com domínio específico
            preferred = next((link for link in links if 'repositorio.ufsc.br' in link), None)
            # Se encontrou, usa o preferido; se não, usa o último da lista
            filtered_values.append(preferred if preferred else links[-1])
        else:
            filtered_values.append('')
    return filtered_values

def get_text_xpath(element, xpath_expr):
    """
    ### Funcionalidades
    - Executa uma expressão XPath em um elemento XML e retorna o conteúdo de texto do primeiro resultado.
    - Lida de forma segura com casos em que o elemento de entrada é `None`.
    - Remove espaços em branco do início e do fim do texto encontrado.

    ### Parâmetros
    - element (lxml.etree._Element | None): O elemento XML a ser consultado.
    - xpath_expr (str): A expressão XPath a ser executada.

    ### Saídas
    - str | None: O texto do primeiro nó encontrado, ou `None` se nenhum resultado for encontrado ou o elemento for inválido.
    """
    if element is None:
        return None
    results = element.xpath(xpath_expr, namespaces=NAMESPACES)
    if results:
        return results[0].strip() if results[0] else None
    return None

def extract_identifier(header, _):
    """
    ### Funcionalidades
    - Extrai o identificador único do registro (OAI identifier) a partir do cabeçalho (`<header>`) de um item.
    - Utiliza a função `get_text_xpath` para realizar a busca.

    ### Parâmetros
    - header (lxml.etree._Element): O elemento XML do cabeçalho do registro.
    - _ : Parâmetro não utilizado, presente para manter uma assinatura de função consistente com outras funções de extração.

    ### Saídas
    - str | None: O texto do identificador encontrado, ou `None`.
    """
    return get_text_xpath(header, './oai:identifier/text()')

def extract_datestamp(header, _):
    """
    ### Funcionalidades
    - Extrai a data da última modificação (`datestamp`) do registro a partir do seu cabeçalho (`<header>`).
    - Utiliza a função `get_text_xpath` para a extração.

    ### Parâmetros
    - header (lxml.etree._Element): O elemento XML do cabeçalho do registro.
    - _ : Parâmetro não utilizado para manter a consistência da assinatura da função.

    ### Saídas
    - str | None: A data encontrada no formato de texto, ou `None`.
    """
    return get_text_xpath(header, './oai:datestamp/text()')

def extract_set_spec(header, _):
    """
    ### Funcionalidades
    - Extrai o identificador da coleção (`setSpec`) a que o registro pertence.
    - Itera sobre todos os `setSpec` disponíveis e retorna o primeiro que começa com o prefixo "col_".

    ### Parâmetros
    - header (lxml.etree._Element): O elemento XML do cabeçalho do registro.
    - _ : Parâmetro não utilizado.

    ### Saídas
    - str | None: O identificador da coleção, ou `None` se nenhum correspondente for encontrado.
    """
    specs = header.xpath('./oai:setSpec/text()', namespaces=NAMESPACES)
    for spec in specs:
        if spec.strip().startswith("col_"):
            return spec.strip()
    return None

def extract_authors(_, metadata):
    """
    ### Funcionalidades
    - Extrai os nomes dos autores (`author`) a partir da seção de metadados.
    - Utiliza a função `get_contributor_field_values` para a busca e `format_list_to_string` para a formatação final.

    ### Parâmetros
    - _ : Parâmetro não utilizado.
    - metadata (lxml.etree._Element): O elemento XML contendo os metadados do registro.

    ### Saídas
    - str | None: Uma string com os nomes dos autores separados por ';', ou `None`.
    """
    return format_list_to_string(get_contributor_field_values(metadata, "author"))

def extract_advisors(_, metadata):
    """
    ### Funcionalidades
    - Extrai os nomes dos orientadores (`advisor`) a partir da seção de metadados.
    - Utiliza `get_contributor_field_values` e `format_list_to_string` para buscar e formatar os dados.

    ### Parâmetros
    - _ : Parâmetro não utilizado.
    - metadata (lxml.etree._Element): O elemento XML de metadados.

    ### Saídas
    - str | None: Uma string com os nomes dos orientadores separados por ';', ou `None`.
    """
    return format_list_to_string(get_contributor_field_values(metadata, "advisor"))

def extract_co_advisors(_, metadata):
    """
    ### Funcionalidades
    - Extrai os nomes dos co-orientadores (`advisor-co`) a partir da seção de metadados.
    - Utiliza `get_contributor_field_values` e `format_list_to_string` para a operação.

    ### Parâmetros
    - _ : Parâmetro não utilizado.
    - metadata (lxml.etree._Element): O elemento XML de metadados.

    ### Saídas
    - str | None: Uma string com os nomes dos co-orientadores separados por ';', ou `None`.
    """
    return format_list_to_string(get_contributor_field_values(metadata, "advisor-co"))

def extract_link_doc(_, metadata):
    """
    ### Funcionalidades
    - Extrai o link direto para o arquivo PDF associado ao registro.
    - Navega pela estrutura de `bundles` e `bitstreams` para encontrar a URL do arquivo com o formato 'application/pdf'.

    ### Parâmetros
    - _ : Parâmetro não utilizado.
    - metadata (lxml.etree._Element): O elemento XML de metadados.

    ### Saídas
    - str | None: Uma string com os links dos PDFs encontrados, separados por ';', ou `None`.
    """
    if metadata is None:
        return None
    links = metadata.xpath(
        ".//xoai:element[@name='bundles']/xoai:element[@name='bundle']/xoai:element[@name='bitstreams']"
        "/xoai:element[@name='bitstream' and xoai:field[@name='format']='application/pdf']"
        "/xoai:field[@name='url']/text()",
        namespaces=NAMESPACES
    )
    return format_list_to_string(list(set(link.strip() for link in links if link.strip())))

def extract_language(_, metadata):
    """
    ### Funcionalidades
    - Extrai o código de idioma (padrão ISO) do registro.
    - Utiliza a função genérica `get_specific_dc_field` para buscar no campo `dc:language:iso`.

    ### Parâmetros
    - _ : Parâmetro não utilizado.
    - metadata (lxml.etree._Element): O elemento XML de metadados.

    ### Saídas
    - str | None: O código do idioma (ex: 'pt_BR'), ou `None`.
    """
    return get_specific_dc_field(metadata, "language", sub_elements=["iso"])

def extract_link_site(_, metadata):
    """
    ### Funcionalidades
    - Extrai a URI (link para a página do item no repositório) do registro.
    - Utiliza a função genérica `get_specific_dc_field` para buscar no campo `dc:identifier:uri`.

    ### Parâmetros
    - _ : Parâmetro não utilizado.
    - metadata (lxml.etree._Element): O elemento XML de metadados.

    ### Saídas
    - str | None: A URL para a página do item, ou `None`.
    """
    return get_specific_dc_field(metadata, "identifier", sub_elements=["uri"])

def extract_subjects(_, metadata):
    """
    ### Funcionalidades
    - Extrai as palavras-chave e assuntos (`subject`) do registro.
    - Busca por todos os sub-elementos dentro de `dc:subject` para capturar diferentes formatos de palavras-chave.
    - Consolida todos os valores encontrados em uma única string separada por ';'.

    ### Parâmetros
    - _ : Parâmetro não utilizado.
    - metadata (lxml.etree._Element): O elemento XML de metadados.

    ### Saídas
    - str | None: Uma string com todas as palavras-chave separadas por ';', ou `None`.
    """
    subjects = metadata.xpath(
        "./xoai:element[@name='dc']/xoai:element[@name='subject']/*",
        namespaces=NAMESPACES
    )
    all_subjects = []
    for subj in subjects:
        values = subj.xpath(".//xoai:field[@name='value']/text()", namespaces=NAMESPACES)
        all_subjects.extend([v.strip() for v in values if v.strip()])
    return format_list_to_string(list(set(all_subjects)))

def extract_abstract(_, metadata):
    """
    ### Funcionalidades
    - Extrai o resumo (`abstract`) do registro.
    - Tenta múltiplas expressões XPath em uma ordem de prioridade para encontrar o resumo, priorizando idiomas ('pt_BR', 'none', 'en').
    - Retorna o primeiro resumo encontrado.

    ### Parâmetros
    - _ : Parâmetro não utilizado.
    - metadata (lxml.etree._Element): O elemento XML de metadados.

    ### Saídas
    - str | None: O texto do resumo, ou `None` se não for encontrado.
    """
    abstract_paths = [
        "./xoai:element[@name='dc']/xoai:element[@name='description']/xoai:element[@name='abstract']"
        "/xoai:element[@name='pt_BR']/xoai:field[@name='value']/text()",
        "./xoai:element[@name='dc']/xoai:element[@name='description']/xoai:element[@name='abstract']"
        "/xoai:element[@name='none']/xoai:field[@name='value']/text()",
        "./xoai:element[@name='dc']/xoai:element[@name='description']/xoai:element[@name='abstract']"
        "/xoai:element[@name='en']/xoai:field[@name='value']/text()",
        "./xoai:element[@name='dc']/xoai:element[@name='description']"
        "/xoai:element[@name='abstract']/xoai:field[@name='value']/text()"
    ]
    for path in abstract_paths:
        result = metadata.xpath(path, namespaces=NAMESPACES)
        if result:
            text = [r.strip() for r in result if r.strip()]
            if text:
                return text[0]
    return None

def extract_generic_field(_, metadata, field_name):  # para type, title, publisher, description
    """
    ### Funcionalidades
    - Atua como um invólucro (wrapper) para a função `get_specific_dc_field`.
    - Extrai o valor de um campo Dublin Core (DC) genérico, como 'type', 'title', 'publisher', etc.

    ### Parâmetros
    - _ : Parâmetro não utilizado.
    - metadata (lxml.etree._Element): O elemento XML de metadados.
    - field_name (str): O nome do campo DC a ser extraído.

    ### Saídas
    - str | None: O valor do campo encontrado, ou `None`.
    """
    return get_specific_dc_field(metadata, field_name)

def extract_date_field(_, metadata, field_name):  # para issued, available, accessioned
    """
    ### Funcionalidades
    - Atua como um invólucro (wrapper) para a função `get_date_field`.
    - Extrai o valor de um campo de data específico, como 'issued', 'available', etc.

    ### Parâmetros
    - _ : Parâmetro não utilizado.
    - metadata (lxml.etree._Element): O elemento XML de metadados.
    - field_name (str): O nome do campo de data a ser extraído.

    ### Saídas
    - str | None: O valor da data encontrada, ou `None`.
    """
    return get_date_field(metadata, field_name)

# Mapeamento dos campos para as funções de extração
FIELD_EXTRACTORS = {
    'identifier_header': extract_identifier,
    'datestamp_header': extract_datestamp,
    'setSpec': extract_set_spec,
    'authors': extract_authors,
    'advisors': extract_advisors,
    'co_advisors': extract_co_advisors,
    'link_doc': extract_link_doc,
    'language': extract_language,
    'link_site': extract_link_site,
    'subjects': extract_subjects,
    'abstract': extract_abstract,
    'title': lambda h, m: extract_generic_field(h, m, "title"),
    'type': lambda h, m: extract_generic_field(h, m, "type"),
    'publisher': lambda h, m: extract_generic_field(h, m, "publisher"),
    'description': lambda h, m: extract_generic_field(h, m, "description"),
    'issued_date': lambda h, m: extract_date_field(h, m, "issued"),
    'available_date': lambda h, m: extract_date_field(h, m, "available"),
    'accessioned_date': lambda h, m: extract_date_field(h, m, "accessioned"),
}


def extract_data_from_xml_file(xml_file_path : str,
                               desired_fields : list[str] = [],
                               logger : logging.Logger=None):
    """
    ### Funcionalidades
    - Orquestra a extração completa de dados de um arquivo XML no formato OAI-PMH.
    - Itera sobre cada registro (`<record>`) no arquivo.
    - Ignora registros que estão marcados como 'deletado' ou que não possuem um cabeçalho (`<header>`).
    - Utiliza um dicionário de mapeamento `FIELD_EXTRACTORS` para aplicar a função de extração correta para cada campo desejado.
    - Permite a extração seletiva de campos através do parâmetro `desired_fields`.
    - Inclui tratamento de erros para falhas de leitura ou de sintaxe do XML.
    - Suporta o registro de logs de progresso, avisos e erros através de um objeto logger opcional.

    ### Parâmetros
    - xml_file_path (str): O caminho completo para o arquivo XML a ser processado.
    - desired_fields (list[str]): Uma lista opcional com os nomes dos campos a serem extraídos. Se vazia, todos os campos definidos em `FIELD_EXTRACTORS` serão extraídos.
    - logger (logging.Logger): Uma instância opcional de um logger para registrar o andamento do processo.

    ### Saídas
    - list[dict]: Uma lista de dicionários, onde cada dicionário representa um registro do XML com os campos extraídos.
    """
    if logger:
        logger.info(f"Iniciando extração de dados do arquivo XML: {xml_file_path}")

    try:
        tree = etree.parse(xml_file_path)
        root = tree.getroot()
        if logger:
            logger.info("Arquivo XML analisado com sucesso.")
    except etree.XMLSyntaxError as e:
        if logger:
            logger.error(f"Erro de sintaxe XML no arquivo {xml_file_path}: {e}")
        return []
    except IOError as e:
        if logger:
            logger.error(f"Erro ao ler o arquivo XML {xml_file_path}: {e}")
        return []

    records_data = []
    total_records = 0
    skipped_records = 0

    records = root.xpath('//oai:record', namespaces=NAMESPACES)
    if logger:
        logger.info(f"Número de registros encontrados: {len(records)}")

    for idx, record in enumerate(records, start=1):
        total_records += 1
        header = record.xpath('./oai:header', namespaces=NAMESPACES)
        if not header:
            if logger:
                logger.warning(f"Registro {idx} sem cabeçalho. Ignorado.")
            skipped_records += 1
            continue

        if header[0].get('status') == 'deleted':
            if logger:
                logger.info(f"Registro {idx} marcado como deletado. Ignorado.")
            skipped_records += 1
            continue

        header = header[0]
        metadata_xoai = record.xpath('./oai:metadata/xoai:metadata', namespaces=NAMESPACES)
        metadata_xoai = metadata_xoai[0] if metadata_xoai else None

        record_info = {}
        record_info["source_xml_file"] = os.path.basename(xml_file_path)

        for field, extractor in FIELD_EXTRACTORS.items():
            if (not desired_fields) or (field in desired_fields):
                try:
                    record_info[field] = extractor(header, metadata_xoai)
                except Exception as e:
                    if logger:
                        logger.warning(f"Erro ao extrair campo '{field}' do registro {idx}: {e}")
                    record_info[field] = None

        records_data.append(record_info)

    if logger:
        logger.info(
            f"Extração concluída. Total: {total_records}, "
            f"Processados: {total_records - skipped_records}, "
            f"Ignorados: {skipped_records}"
        )

    return records_data


def get_col_to_name_csv_file():
    """
    ### Funcionalidades
    - Lê um arquivo CSV para criar um dicionário de mapeamento.
    - Mapeia o identificador de uma coleção (primeira coluna) ao seu nome/localização (segunda coluna).
    - O caminho do arquivo é determinado pela constante global `COL_TO_NAME_CSV_FILE_PATH`.
    - Pula a linha do cabeçalho do arquivo CSV.
    - Retorna um dicionário vazio se o arquivo não existir.

    ### Parâmetros
    - Nenhum.

    ### Saídas
    - dict[str, str]: Um dicionário mapeando o ID da coleção ao seu nome.
    """
    if os.path.exists(COL_TO_NAME_CSV_FILE_PATH):
        with open(COL_TO_NAME_CSV_FILE_PATH, "r", encoding="utf-8") as f:
            reader = csv.reader(f)
            next(reader)  # pular cabeçalho
            return {linha[0]: linha[1] for linha in reader}
    else:
        return {}
    
dic_col_to_name = get_col_to_name_csv_file()

def save_col_to_name_csv_file(dic_col_to_name : dict[str,str]):
    """
    ### Funcionalidades
    - Salva um dicionário de mapeamento em um arquivo no formato CSV.
    - Grava um cabeçalho com as colunas "col" e "location".
    - Itera sobre os itens do dicionário de entrada e grava cada par chave-valor como uma linha no arquivo.
    - O caminho do arquivo de destino é determinado pela constante global `COL_TO_NAME_CSV_FILE_PATH`.

    ### Parâmetros
    - dic_col_to_name (dict[str, str]): O dicionário contendo o mapeamento a ser salvo.

    ### Saídas
    - Nenhuma (a função escreve em um arquivo).
    """
    with open(COL_TO_NAME_CSV_FILE_PATH, "w", newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(["col", "location"])  # cabeçalho (opcional)
        for col, location in dic_col_to_name.items():
            writer.writerow([col, location])

def extract_year(date_str):
    """
    ### Funcionalidades
    - Extrai o ano de uma string de data.
    - Utiliza uma expressão regular para localizar os primeiros quatro dígitos contínuos no início da string.
    - É capaz de lidar com valores nulos ou NaN (do pandas), retornando `None` nesses casos.
    - Retorna uma string vazia se nenhum padrão de ano for encontrado na string de entrada.

    ### Parâmetros
    - date_str (str | None): A string que contém a data a ser analisada.

    ### Saídas
    - str | None: Uma string contendo o ano de quatro dígitos, uma string vazia ou `None`.
    """
    if pd.isnull(date_str):
        return None
    match = re.match(r'(\d{4})', str(date_str))
    if match:
        return match.group(1)
    return ''

def format_type(work_type : str) -> str:
    """
    ### Funcionalidades
    - Padroniza e limpa uma grande variedade de strings que descrevem tipos de trabalhos acadêmicos.
    - Utiliza um dicionário de mapeamento para corrigir erros de digitação, variações de formatação e capitalização.
    - Agrupa diferentes descrições sob um termo padrão (ex: várias formas de "Tese (Doutorado)" se tornam "TESE DOUTORADO").
    - Se o tipo de trabalho não estiver no dicionário de mapeamento, retorna o tipo original.
    - Garante que a saída final esteja sempre em letras maiúsculas e sem espaços nas extremidades.

    ### Parâmetros
    - work_type (str): A string original descrevendo o tipo de trabalho.

    ### Saídas
    - str: A string do tipo de trabalho padronizada e em maiúsculas.
    """
    dic_types = {
        '':'Não Especificado',
        '(Dissertação (mestrado)':'Dissertação Mestrado',
        '(HTML & PDF & DOC)':'HTML-PDF-DOC',
        'Article':'Artigo',
        'D':'D',
        'Disertação (Mestrado)':'Dissertação Mestrado',
        'Disseratação (Mestrado)':'Dissertação Mestrado',
        'Dissertacão (Mestrado)':'Dissertação Mestrado',
        'Dissertaão (Mestrado)':'Dissertação Mestrado',
        'Dissertaçao (Mestrado)':'Dissertação Mestrado',
        'Dissertaçaõ (Mestrado)':'Dissertação Mestrado',
        'Dissertaçào (Mestrado)':'Dissertação Mestrado',
        'Dissertação':'Dissertação',
        'Dissertação  (Mestraddo)':'Dissertação Mestrado',
        'Dissertação  (Mestrado)':'Dissertação Mestrado',
        'Dissertação ( mestrado )':'Dissertação Mestrado',
        'Dissertação ( mestrado)':'Dissertação Mestrado',
        'Dissertação (Administração)':'Dissertação',
        'Dissertação (Dissertação)':'Dissertação',
        'Dissertação (Doutorado)':'Dissertação Doutorado',
        'Dissertação (Mesrtado)':'Dissertação Mestrado',
        'Dissertação (Mesrtrado)':'Dissertação Mestrado',
        'Disertação (Mestrado)':'Dissertação Mestrado',
        'Dissertação (Mestado)':'Dissertação Mestrado',
        'Dissertação (Mestraddo)':'Dissertação Mestrado',
        'Dissertação (Mestrado )':'Dissertação Mestrado',
        'Dissertação (Mestrado acadêmico)':'Dissertação Mestrado',
        'Dissertação (Mestrado profissional)':'Dissertação Mestrado Profissional',
        'Dissertação (Mestrado)':'Dissertação Mestrado',
        'Dissertação (Mestrrado)':'Dissertação Mestrado',
        'Dissertação (Metrado)':'Dissertação Mestrado',
        'Dissertação (mestrado)':'Dissertação Mestrado',
        'Dissertação [mesterado)':'Dissertação Mestrado',
        'Dissertação [mestrado)':'Dissertação Mestrado',
        'Dissertação mestrado)':'Dissertação Mestrado',
        'Dissertação {mestrado)':'Dissertação Mestrado',
        'Dissertação( mestrado)':'Dissertação Mestrado',
        'Dissertação(Mestrado)':'Dissertação Mestrado',
        'Dissertação(Mestrdo)':'Dissertação Mestrado',
        'Dissertaçãom (Mestrado)':'Dissertação Mestrado',
        'Dissertaçção (Mestrado)':'Dissertação Mestrado',
        'Dissetação (Mestrado)':'Dissertação Mestrado',
        'Disssertação (Mestrado)':'Dissertação Mestrado',
        'Editorial design and revision by Beatriz Stephanie Ribeiro':'Editorial design and revision by Beatriz Stephanie Ribeiro', 
        'Monografia (Especialização em Planejamento e Gestão em Defesa Civil)':'Monografia',
        'Monografia de especialização':'Monografia',
        'Other: Editorial design and revision by Beatriz Stephanie Ribeiro':'Outros',
        'Relatorio (Pós-doutorado)':'Relatorio Pós-Doutorado',
        'Relatório (Pós-Doutorado)':'Relatorio Pós-Doutorado',
        'Relatório Técnico (Mestrado profissional)':'Relatório Técnico Mestrado Profissional',
        'Relatório de Estágio Extr':'Relatório Estágio Extr',
        'TCC (graduação Arquitetura e Urbanismo)':'TCC',
        'TCC (graduação em Agronomia )':'TCC',
        'TCC (graduação em Agronomia)':'TCC',
        'TCC (graduação em Arquitetura e Urbanismo )':'TCC',
        'TCC (graduação em Arquitetura e Urbanismo)':'TCC',
        'TCC (graduação em Arquitetura e Urbansimo)':'TCC',
        'TCC (graduação em Biblioteconomia)':'TCC',
        'TCC (graduação em Emfermagem)':'TCC',
        'TCC (graduação em Enfermagem )':'TCC',
        'TCC (graduação em Enfermagem)':'TCC',
        'TCC (graduação em Engenharia de Aquicultura )':'TCC',
        'TCC (graduação em Engenharia de Aquicultura)':'TCC',
        'TCC (graduação em Engenharia de Aqüicultura)':'TCC',
        'TCC (graduação em Serviço Social)':'TCC',
        'TCC (graduação)':'TCC',
        'TCC (graduaçãoem Agronomia)':'TCC',
        'TCC1 (graduação)':'TCC',
        'TCC2 (Graduação em Arquitetura e Urbanismo)':'TCC',
        'TCCP (especialização)':'TCCP Especialização',
        'TCCes':'TCC',
        'TCCgrad':'TCC',
        'TCCresid':'TCC',
        'TESE (Doutor)':'Tese Doutorado',
        'TESE (Doutorado)':'Tese Doutorado',
        'Tese  (Doutorado)':'Tese Doutorado',
        'Tese (Dissertação)':'Tese;Dissertação',
        'Tese (Dotutorado)':'Tese Doutorado',
        'Tese (Dourado)':'Tese Doutorado',
        'Tese (Dourorado)':'Tese Doutorado',
        'Tese (Doutarado)':'Tese Doutorado',
        'Tese (Doutorado profissional)':'Tese Doutorado Profissional',
        'Tese (Doutorado)':'Tese Doutorado',
        'Tese (Doutordo)':'Tese Doutorado',
        'Tese (Doutotado)':'Tese Doutorado',
        'Tese (Doutrado)':'Tese Doutorado',
        'Tese (Dutorado)':'Tese Doutorado',
        'Tese (Livre Docência)':'Tese Livre Docência',
        'Tese (Livre docencia)':'Tese Livre Docência',
        'Tese (Livre-docencia)':'Tese Livre Docência',
        'Tese (Mestrado)':'Tese Mestrado',
        'Tese (doutorado)':'Tese Doutorado',
        'Tese - (Doutorado)':'Tese Doutorado',
        'Tese Doutorado)':'Tese Doutorado',
        'Tese [doutorado)':'Tese Doutorado',
        'Tese elaborada em regime de cotutela entre o Programa de Pós Graduação em Engenharia de Alimentos da Universidade Federal de Santa Catarina e a Escola de Doutorado de Ciências da Engenharia (SPI Oniris)':'Tese',
        'Tese {doutorado)':'Tese Doutorado',
        'Tese(Doutorado)':'Tese Doutorado',
        'Trabalho de Conclusao de Curso':'TCC',
        'Trabalho de Conclusão (Graduação)':'TCC',
        'Trabalho de Conclusão de Curso':'TCC',
        'Trabalho de Conclusão de Curso  (graduação em Engenharia de Aquicultura )':'TCC',
        'article':'Artigo',
        'dissertacao':'Dissertação',
        'e-Book':'e-book',
        'eBook':'e-book',
        'filme':'Filme', 
        'image':'Imagem',
        'imagem':'Imagem',
        'other':'Outros',
        'relatorio':'Relatório',
        'report':'Relatório',
        'tese':'Tese',
        'tese (Doutorado)':'Tese Doutorado',
    }
    if work_type in dic_types.keys():
        return dic_types[work_type].upper().strip()
    return work_type.upper().strip()

def get_text_trail(url : str,
                   logger : logging.Logger|None = None,
                   timeout : int|float = 65) -> str:
    """
    ### Funcionalidades
    - Realiza uma requisição HTTP GET para a URL fornecida a fim de obter seu conteúdo HTML.
    - Analisa (parse) o HTML para encontrar a trilha de navegação (breadcrumb trail) dentro de uma `div` com id `ds-header`.
    - Constrói uma string que representa a hierarquia de localização, unindo os itens da trilha com " -> ".
    - Filtra itens de navegação genéricos como "Página Inicial" ou "Ver Item" do resultado final.
    - Possui tratamento de erros robusto para falhas de requisição (timeout, erros HTTP) e de análise do HTML.

    ### Parâmetros
    - url (str): A URL da página a ser analisada.
    - logger (logging.Logger | None): Uma instância opcional de um logger para registrar o andamento e os erros.
    - timeout (int | float): O tempo máximo em segundos para aguardar a resposta da requisição.

    ### Saídas
    - str: A string da trilha de localização completa, ou uma string vazia em caso de erro.
    """
    try:
        response = requests.get(url,timeout=timeout)
        response.raise_for_status()
    except requests.exceptions.Timeout:
        if logger:
            logger.error("Erro: A requisição excedeu o tempo limite de 65 segundos.",exc_info=True)
        return ''
    except requests.exceptions.HTTPError as errh:
        if logger:
            logger.error(f"Erro HTTP: {errh}",exc_info=True)
        return ''
    except requests.exceptions.RequestException as err:
        if logger:
            logger.error(f"Erro na requisição: {err}",exc_info=True)
        return ''
    except Exception as e:
        if logger:
            logger.error(f'Erro desconhecido ocorreu na hora de processar requisição --> {e.__class__.__name__}: {str(e)}',exc_info=True)
        return ''
    else:
        soup = BeautifulSoup(response.text, "html.parser")
        try:
            header_div = soup.find("div", id="ds-header")
            if not header_div:
                if logger:
                    logger.warning(f'Não foi possível encontrar header no HTML')
                return ''

            trail_items = header_div.find_all("li")
            if len(trail_items) < 3:
                if logger:
                    logger.warning(f'Não foi possível encontrar a trilha de localização no HTML')
                return ''

            # We expect the full path to be something like this:
            # "Teses e Dissertações -> Programa de Pós-Graduação em Engenharia de Automação e Sistemas"
            # Or even:
            # "Acervos -> Campus Florianópolis -> PROPESQ (Pró-Reitoria de Pesquisa) -> Programa de Iniciação Científica e Tecnológica da UFSC -> Seminário de Iniciação Científica e Tecnológica da UFSC -> 2023 -> Iniciação Científica - PIBIC e Programa Voluntário -> Ciências Exatas, da Terra e Engenharias -> Departamento de Automação e Sistemas"
            str_full_location = ' -> '.join([trail_item.get_text(strip=True) for trail_item in trail_items if trail_item.get_text(strip=True) not in ['Repositório Institucional da UFSC',
                                                                                                                                                      'DSpace Home',
                                                                                                                                                      'Ver item',
                                                                                                                                                      'View Item']])
            return str_full_location

        except Exception as e:
            if logger:
                logger.error(f'Erro desconhecido na hora de processar resposta da requisição --> {e.__class__.__name__}: {str(e)}',exc_info=True)
            return ''
        
def get_origin_info_from_col(col : str,
                             logger : logging.Logger|None = None) -> dict[str]:
    """
    ### Funcionalidades
    - Constrói uma URL do Repositório da UFSC a partir de um identificador de coleção (ex: "col_123456789_75030").
    - Utiliza a função `get_text_trail` para realizar o web scraping da URL gerada e obter a trilha de localização.
    - Retorna a trilha de localização encontrada.

    ### Parâmetros
    - col (str): O identificador da coleção no formato esperado "col_numero1_numero2".
    - logger (logging.Logger | None): Uma instância opcional de um logger para passar para a função de scraping.

    ### Saídas
    - str: A string da trilha de localização completa, ou uma string vazia em caso de erro.
    """
    col_numbers = col.split('_')
    col_numbers.remove('col')
    first_number = col_numbers[0]
    second_number = col_numbers[1]

    link = f'https://repositorio.ufsc.br/handle/{first_number}/{second_number}'

    str_full_location = get_text_trail(link,logger)

    if logger:
        logger.info(f'Link para coletar info {link}')
        if str_full_location:
            logger.info(f'Localização completa encontrada para {col}: {str_full_location}')

    return str_full_location

def get_academic_work_id_locator(dic_xml_record : dict) -> list[str]:
    """
    ### Funcionalidades
    - Extrai o identificador de coleção (`setSpec`) de um dicionário que representa um registro XML.
    - Navega pela estrutura do dicionário para encontrar o campo `header` e, dentro dele, o campo `setSpec`.
    - Filtra e retorna apenas os identificadores que correspondem ao padrão "col_" seguido de números.
    - Lida com o caso de `setSpec` ser uma lista de strings ou uma única string.
    - Lança um `TypeError` se a entrada não for um dicionário.

    ### Parâmetros
    - dic_xml_record (dict): O dicionário contendo os dados de um registro extraído do XML.

    ### Saídas
    - list[str]: Uma lista contendo os identificadores de coleção válidos encontrados.
    """
    if isinstance(dic_xml_record,dict):
        header = dic_xml_record.get('header')
        if header:
            setSpec = header.get('setSpec')
            if setSpec:
                if isinstance(setSpec,list):
                    return [item.strip() for item in setSpec if re.search(r'col\_\d+\_\d+',item)]
                elif isinstance(setSpec,str):
                    return [setSpec.strip()] if re.search(r'col\_\d+\_\d+',setSpec) else []
                else:
                    return []
        return []
    else:
        raise TypeError(f'Input type is not dict, as expected. Current input type is {type(dic_xml_record).__name__}.')

def get_academic_work_location(id_loc : str, logger : logging.Logger|None = None) -> str:
    """
    ### Funcionalidades
    - Obtém a trilha de localização completa (breadcrumb) para um dado identificador de coleção.
    - Atua como um mecanismo de cache: primeiro verifica se a localização já existe em um dicionário global (`dic_col_to_name`).
    - Se a localização não estiver no cache, chama a função `get_origin_info_from_col` para buscá-la via web scraping.
    - Após uma busca bem-sucedida, atualiza o dicionário de cache e o salva em um arquivo CSV para uso futuro.
    - Retorna a localização encontrada (do cache ou da busca) ou uma string vazia em caso de falha.

    ### Parâmetros
    - id_loc (str): O identificador da coleção (ex: "col_123456789_75030").
    - logger (logging.Logger | None): Uma instância opcional de um logger para registrar o processo.

    ### Saídas
    - str: A trilha de localização completa ou uma string vazia.
    """
    global dic_col_to_name
    if id_loc not in dic_col_to_name.keys():
        if logger:
            logger.info(f'Coletando localização por nome do id "{id_loc}"')
        full_location = get_origin_info_from_col(id_loc,logger)
        if full_location:
            dic_col_to_name[id_loc] = full_location
            save_col_to_name_csv_file(dic_col_to_name)
            return full_location        
    else:
        # if logger:
        #     logger.info(f'Coletando informação de localização pelo dicionário armazenado com id "{id_loc}"')
        full_location = dic_col_to_name[id_loc]
        return full_location
    if logger:
        logger.warning(f'Não foi possível identificar localização completa para id {str(id_loc)}')
    return ''

def get_academic_work_first_community(full_location : str) -> str:
    """
    ### Funcionalidades
    - Extrai o primeiro elemento de uma string de trilha de localização (breadcrumb).
    - Divide a string pelo separador "->" e retorna o primeiro item.

    ### Parâmetros
    - full_location (str): A string da trilha de localização completa.

    ### Saídas
    - str: O primeiro nível da hierarquia de localização.
    """
    return full_location.split('->')[0].strip()

def get_academic_work_last_collection(full_location : str) -> str:
    """
    ### Funcionalidades
    - Extrai o último elemento de uma string de trilha de localização (breadcrumb).
    - Divide a string pelo separador "->" e retorna o último item.

    ### Parâmetros
    - full_location (str): A string da trilha de localização completa.

    ### Saídas
    - str: O nível mais específico (último) da hierarquia de localização.
    """
    return full_location.split('->')[-1].strip()

def insert_location_into_df(df : pd.DataFrame,logger : logging.Logger|None = None) -> pd.DataFrame:
    """
    ### Funcionalidades
    - Enriquece um DataFrame do pandas adicionando colunas de localização.
    - Itera sobre a coluna 'setSpec' para obter a localização completa de cada registro usando `get_academic_work_location`.
    - Adiciona três novas colunas: 'full_locations', 'first_com' (primeiro nível da hierarquia) e 'last_col' (último nível).

    ### Parâmetros
    - df (pd.DataFrame): O DataFrame a ser modificado, que deve conter a coluna 'setSpec'.
    - logger (logging.Logger | None): Uma instância opcional de um logger.

    ### Saídas
    - pd.DataFrame: O DataFrame original com as novas colunas de localização adicionadas.
    """
    setSpecs = df['setSpec'].to_list()
    df['full_locations'] = [get_academic_work_location(value,logger=logger) if value else '' for value in setSpecs]    
    df['first_com'] = [get_academic_work_first_community(value) if value else '' for value in df['full_locations']]
    df['last_col'] = [get_academic_work_last_collection(value) if value else '' for value in df['full_locations']]

    return df

def split_full_location(full_location : str) -> list[str]:
    """
    ### Funcionalidades
    - Divide uma string de trilha de localização em uma lista de seus componentes.
    - Utiliza "->" como delimitador e remove espaços em branco de cada componente.
    - Filtra componentes que são muito curtos (menos de 4 caracteres).

    ### Parâmetros
    - full_location (str): A string da trilha de localização.

    ### Saídas
    - list[str]: Uma lista com os componentes da localização.
    """
    splitted_full_location = [loc.strip() for loc in full_location.split('->') if len(loc.strip())>3]
    return splitted_full_location

def treat_locations(full_location : str, reverse : bool = True) -> list[str]:
    """
    ### Funcionalidades
    - Pré-processa e padroniza uma string de localização para facilitar a busca por cursos.
    - Remove prefixos comuns como "Curso de" ou "Programa de Pós-Graduação em".
    - Formata cada componente da localização usando `format_text` com tratamento especial.
    - Opcionalmente, inverte a ordem dos componentes para priorizar a busca nos níveis mais específicos.

    ### Parâmetros
    - full_location (str): A string da trilha de localização.
    - reverse (bool): Se `True`, a lista de componentes resultante é invertida.

    ### Saídas
    - list[str]: Uma lista de componentes de localização tratados e formatados.
    """
    full_location = re.sub(r'Curso de|Programa de Pós-Graduação em','',full_location,flags=re.IGNORECASE).strip()
    location_elements = [format_text(loc,special_treatment=True).strip() for loc in split_full_location(full_location)]    
    if reverse:
        location_elements.reverse() # Trabalharemos com prioridade para as últimas localizações (ler de trás para frente)
    return location_elements

def get_curso_from_full_location(full_location : str,courses : list[str]|None = None) -> str:
    """
    ### Funcionalidades
    - Tenta identificar um nome de curso oficial a partir de uma string de localização.
    - Processa a string de localização e a compara com uma lista de nomes de cursos oficiais da UFSC.
    - A comparação busca por uma correspondência exata entre um componente da localização e um nome de curso, após ambos serem formatados.
    - Retorna o primeiro nome de curso oficial que corresponder.

    ### Parâmetros
    - full_location (str): A string da trilha de localização.
    - courses (list[str] | None): A lista de nomes de cursos oficiais para comparação.

    ### Saídas
    - str: O nome do curso encontrado, ou uma string vazia.
    """
    # Só coletamos correspondências totais (==) em algum elemento entre os "->" com os cursos catalogados pela UFSC
    # Teses e Dissertações -> Programa de Pós-Graduação em Oceanografia se torna uma lista com ["Teses e Dissertações", "Programa de Pós-Graduação em Oceanografia"]
    # Depois o último elemento da lista tem "Programa de Pós-Graduação em" removido, ficando só com o nome do curso exatamente.
    # Na hora da comparação ambos os elementos são formatados.
    location_elements = treat_locations(full_location) # Trabalharemos com prioridade para as últimas localizações (ler de trás para frente)    
    for element in location_elements:            
        for curso_ufsc in [c for c in courses if len(c) <= len(element)]:
            curso_ufsc_formatted = format_text(curso_ufsc,special_treatment=True)
            if curso_ufsc_formatted == element:
                return curso_ufsc
    return ''

def get_list_of_curso_from_full_location(list_of_courses : list[str],
                                         list_of_full_locations : list[str],
                                         ufsc_courses) -> list[str]:
    """
    ### Funcionalidades
    - Processa uma lista de cursos, preenchendo os que estão faltando.
    - Para cada curso vazio na lista de entrada, tenta identificá-lo usando a string de localização correspondente.
    - Mantém os cursos que já foram identificados.

    ### Parâmetros
    - list_of_courses (list[str]): A lista de cursos, que pode conter strings vazias.
    - list_of_full_locations (list[str]): A lista paralela de trilhas de localização.
    - ufsc_courses (list[str]): A lista de referência com todos os nomes de cursos oficiais da UFSC.

    ### Saídas
    - list[str]: A lista de cursos atualizada e mais completa.
    """
    courses = []
    for course,full_location in zip(list_of_courses,list_of_full_locations):
        if course.strip() == '':
            courses.append(get_curso_from_full_location(full_location=full_location,courses=ufsc_courses))
        else:
            courses.append(course)
    return courses

def split_description(description : str) -> list[str]:
    """
    ### Funcionalidades
    - Divide uma string de descrição em uma lista de partes ou frases significativas.
    - Utiliza múltiplos delimitadores (hífen entre espaços, vírgula, ponto) para a divisão.
    - Filtra partes resultantes que são muito curtas.

    ### Parâmetros
    - description (str): A string de descrição a ser dividida.

    ### Saídas
    - list[str]: Uma lista de strings com as partes da descrição.
    """
    splitted_description = [desc.strip() for desc in re.split(r'\s\-\s|\,|\.',description) if len(desc.strip())>3]
    return splitted_description

def treat_descriptions(description : str, reverse : bool = True) -> list[str]:
    """
    ### Funcionalidades
    - Pré-processa e padroniza uma string de descrição para facilitar a busca por cursos.
    - Remove prefixos comuns, formata cada parte e, opcionalmente, inverte a ordem.
    - Análoga à função `treat_locations`, mas aplicada a campos de descrição.

    ### Parâmetros
    - description (str): A string de descrição.
    - reverse (bool): Se `True`, a lista de componentes resultante é invertida.

    ### Saídas
    - list[str]: Uma lista de componentes da descrição tratados e formatados.
    """
    description = re.sub(r'Curso de|Programa de Pós-Graduação em','',description,flags=re.IGNORECASE).strip()   
    description_elements = [format_text(element,special_treatment=True).strip() for element in split_description(description)]
    if reverse:
        description_elements.reverse()
    return description_elements

def get_curso_from_description(description : str, courses : list[str]|None = None) -> str:
    """
    ### Funcionalidades
    - Tenta identificar um nome de curso oficial a partir do texto de uma descrição.
    - Processa a string de descrição e a compara com uma lista de nomes de cursos oficiais.
    - Retorna a primeira correspondência exata encontrada.
    - Análoga à função `get_curso_from_full_location`, mas usa o campo de descrição como fonte.

    ### Parâmetros
    - description (str): A string de descrição.
    - courses (list[str] | None): A lista de nomes de cursos oficiais para comparação.

    ### Saídas
    - str: O nome do curso encontrado, ou uma string vazia.
    """
    description_elements = treat_descriptions(description)
    for element in description_elements:
        for curso_ufsc in [c for c in courses if len(c) <= len(element)]:
            curso_ufsc_formatted = format_text(curso_ufsc,special_treatment=True)
            if curso_ufsc_formatted == element:
                return curso_ufsc
    return ''

def insert_curso_into_df(df : pd.DataFrame) -> pd.DataFrame:
    """
    ### Funcionalidades
    - Adiciona uma coluna 'course' a um DataFrame, tentando identificar o curso de cada registro.
    - Realiza um processo de duas etapas para máxima eficácia:
    - 1. Tenta identificar o curso a partir da coluna 'description'.
    - 2. Para os registros ainda sem curso, tenta identificá-lo a partir da coluna 'full_locations'.
    - Garante que a coluna 'course' final esteja em letras maiúsculas.

    ### Parâmetros
    - df (pd.DataFrame): O DataFrame a ser enriquecido. Deve conter as colunas 'description' e 'full_locations'.

    ### Saídas
    - pd.DataFrame: O DataFrame original com a nova coluna 'course' adicionada e populada.
    """
    try:
        ufsc_courses = CursosUFSC().get_cursos()
    except Exception as e:
        ufsc_courses = None
    df['course'] = [get_curso_from_description(value,ufsc_courses) if value else '' for value in df['description'].to_list()]
    df['course'] = get_list_of_curso_from_full_location(list_of_courses=df['course'].to_list(),
                                                        list_of_full_locations=df['full_locations'].to_list(),
                                                        ufsc_courses=ufsc_courses)
    df['course'] = df['course'].str.upper()
    return df


def force_type_curso_from_description(list_type_cursos : list[str],
                                      list_descriptions : list[str]) -> list[str]:
    """
    ### Funcionalidades
    - Tenta inferir o nível de um curso ('GRAD' ou 'POS') para itens que não têm um tipo definido.
    - Itera sobre duas listas paralelas: uma com tipos de curso e outra com descrições.
    - Se um tipo de curso estiver vazio, analisa a descrição correspondente em busca de palavras-chave (ex: 'tese', 'tcc').
    - Atribui 'POS' para descrições que sugerem pós-graduação e 'GRAD' para as que sugerem graduação.
    - Mantém o tipo de curso original se ele já estiver preenchido.

    ### Parâmetros
    - list_type_cursos (list[str]): Uma lista com os tipos de curso, podendo conter strings vazias.
    - list_descriptions (list[str]): Uma lista paralela com as descrições dos trabalhos.

    ### Saídas
    - list[str]: Uma nova lista de tipos de curso, com os valores vazios potencialmente preenchidos.
    """
    forced_list_type_courses = []
    for type_course,description in zip(list_type_cursos,list_descriptions):
        description = description.strip()
        if type_course == '' and description: # Se não tiver tipo_curso, mas tiver uma descrição
            if re.search(r'^tese|^dissertação',description,re.IGNORECASE):
                forced_list_type_courses.append('POS')
            elif re.search(r'^tcc|^trabalho_conclusao_curso|^trabalho_de_conclusao_de_curso|^trabalho_conclusao_de_curso|^pfc|^projeto_fim_de_curso|^projeto_de_fim_de_curso',description,re.IGNORECASE):
                forced_list_type_courses.append('GRAD')
            else:
                forced_list_type_courses.append('')
        else:
            forced_list_type_courses.append(type_course)
    return forced_list_type_courses

def insert_type_curso_based_on_description_into_df(df : pd.DataFrame) -> pd.DataFrame:
    """
    ### Funcionalidades
    - Enriquece um DataFrame tentando preencher a coluna 'type_course' com base na coluna 'description'.
    - Garante que a coluna 'type_course' exista no DataFrame, criando-a se necessário.
    - Utiliza a função `force_type_curso_from_description` para inferir o nível do curso ('GRAD' ou 'POS') para os registros que ainda não o possuem.

    ### Parâmetros
    - df (pd.DataFrame): O DataFrame a ser modificado. Deve conter a coluna 'description'.

    ### Saídas
    - pd.DataFrame: O DataFrame com a coluna 'type_course' atualizada.
    """
    if 'type_course' not in df.keys():
        df['type_course'] = ''    
    # Tentar coletar tipo de curso por full_location e por curso não parece ser boa opção
    # Complexidade no full_loc não garante precisão e existem cursos que tem tanto na GRAD quanto na POS
    # df['type_course'] = force_type_curso_from_full_location(list_type_cursos=list_type_courses,list_full_locations=df['full_locations'].to_list())
    # df['type_course'] = force_type_curso_from_courses(list_type_cursos=df['type_course'].to_list(),list_courses=df['course'].to_list())
    df['type_course'] = force_type_curso_from_description(list_type_cursos=df['type_course'].to_list(),
                                                          list_descriptions=df['description'].to_list())
    return df

def insert_type_course_based_on_type_into_df(df: pd.DataFrame, logger: logging.Logger = None) -> pd.DataFrame:
    """
    ### Funcionalidades
    - Adiciona ou sobrescreve a coluna 'type_course' com base no conteúdo da coluna 'type'.
    - Utiliza expressões regulares para classificar cada registro como 'POS' (pós-graduação) ou 'GRAD' (graduação).
    - A classificação é feita buscando por palavras-chave como 'tese', 'dissertação', 'tcc', etc., na coluna 'type'.
    - Inicializa a coluna com valores vazios e depois preenche conforme as regras.

    ### Parâmetros
    - df (pd.DataFrame): O DataFrame a ser modificado. Deve conter a coluna 'type'.
    - logger (logging.Logger): Uma instância opcional de um logger para registrar a conclusão da operação.

    ### Saídas
    - pd.DataFrame: O DataFrame com a coluna 'type_course' adicionada/atualizada.
    """
    # Inicializa com string vazia
    df['type_course'] = ""

    # Expressões regulares corrigidas com grupos de NÃO captura
    regex_pos = re.compile(
        r'^tese(?:s)?\b|^dissertacao\b|^dissertacoes\b|_mestrado\b|_doutorado\b|mestrado|doutorado|tese|dissertacao|dissertação',
        flags=re.IGNORECASE)

    regex_grad = re.compile(
        r'^tcc\b|^tcc\_|^tccp\b|^tccp\_',
        flags=re.IGNORECASE)

    # Aplica POS
    df.loc[
        df['type'].fillna('').str.lower().str.contains(regex_pos),
        'type_course'
    ] = 'POS'

    # Aplica GRAD
    df.loc[
        df['type'].fillna('').str.lower().str.contains(regex_grad),
        'type_course'
    ] = 'GRAD'

    if logger:
        logger.info(f"Coluna 'type_course' adicionada com valores únicos: {df['type_course'].unique().tolist()}")

    return df


def get_campus_from_description(list_campus : list[str],
                                list_descriptions : list[str]) -> list[str]:
    """
    ### Funcionalidades
    - Tenta inferir a sigla do campus ('FLN', 'JOI', etc.) para registros que não possuem um campus definido.
    - Opera sobre listas paralelas de campi e descrições.
    - Utiliza uma série de regras de busca na descrição: primeiro procura por menções diretas ao nome do campus (ex: 'campus_florianopolis').
    - Como fallback, verifica se o nome de algum centro de ensino conhecido está presente na descrição para inferir o campus correspondente.
    - Mantém o valor original do campus se ele já estiver preenchido.

    ### Parâmetros
    - list_campus (list[str]): Uma lista com as siglas dos campi, podendo conter strings vazias.
    - list_descriptions (list[str]): Uma lista paralela com as descrições dos trabalhos.

    ### Saídas
    - list[str]: Uma nova lista de siglas de campi, com os valores vazios potencialmente preenchidos.
    """
    forced_list_campus = []
    
    dic_centros_campus = {'FLN':[format_text(centro,special_treatment=True) for centro in DIC_CAMPUS_CENTROS_COMPLETO_E_SIGLAS['FLN'].keys()],
                          'JOI':[format_text(centro,special_treatment=True) for centro in DIC_CAMPUS_CENTROS_COMPLETO_E_SIGLAS['JOI'].keys()],
                          'CUR':[format_text(centro,special_treatment=True) for centro in DIC_CAMPUS_CENTROS_COMPLETO_E_SIGLAS['CUR'].keys()],
                          'BNU':[format_text(centro,special_treatment=True) for centro in DIC_CAMPUS_CENTROS_COMPLETO_E_SIGLAS['BNU'].keys()],
                          'ARA':[format_text(centro,special_treatment=True) for centro in DIC_CAMPUS_CENTROS_COMPLETO_E_SIGLAS['ARA'].keys()]}

    for campus,description in zip(list_campus,list_descriptions):
        if campus == '' and description.strip():
            formatted_description = format_text(description,special_treatment=True)
            if 'campus_florianopolis' in formatted_description:
                forced_list_campus.append('FLN')
            elif 'campus_ararangua' in formatted_description:
                forced_list_campus.append('ARA')
            elif 'campus_blumenau' in formatted_description:
                forced_list_campus.append('BNU')
            elif 'campus_curitibanos' in formatted_description:
                forced_list_campus.append('CUR')
            elif 'campus_joinville' in formatted_description:
                forced_list_campus.append('JOI')
            elif re.search(r'florianopolis\_\d{4}$',formatted_description):
                forced_list_campus.append('FLN')
            else:
                campus_status = False
                for campus_dic in dic_centros_campus.keys():
                    for formatted_centro in dic_centros_campus[campus_dic]:
                        if formatted_centro in formatted_description:
                            campus_status = True
                            forced_list_campus.append(campus_dic)
                            break
                    if campus_status:
                        break
                if not campus_status:
                    forced_list_campus.append('')
        else:
            forced_list_campus.append(campus)
    return forced_list_campus

def insert_campus_from_description_into_df(df : pd.DataFrame) -> pd.DataFrame:
    """
    ### Funcionalidades
    - Adiciona ou preenche a coluna 'campus' em um DataFrame.
    - Utiliza a função `get_campus_from_description` para inferir o campus a partir da coluna 'description'.
    - Inicializa a coluna 'campus' com valores vazios antes de aplicar a lógica de inferência.

    ### Parâmetros
    - df (pd.DataFrame): O DataFrame a ser modificado, que deve conter a coluna 'description'.

    ### Saídas
    - pd.DataFrame: O DataFrame com a coluna 'campus' adicionada ou atualizada.
    """
    # Não podemos usar insert_campus_from_cursos_ufsc() porque há cursos com o mesmo tipo que são oferecidos em diferentes campus
    # Como Agronomia (GRAD) em FLN e CUR / Eng. Controle e Automação (GRAD) FLN e BNU / Materiais (GRAD) / Medicina (GRAD), etc
    # df = insert_campus_from_cursos_ufsc(df)
    df['campus'] = ''
    df['campus'] = get_campus_from_description(list_campus=df['campus'].to_list(),list_descriptions=df['description'].to_list())

    return df


def get_list_of_centro_from_description(list_centros : list[str],
                                list_descriptions : list[str]) -> list[str]:
    """
    ### Funcionalidades
    - Tenta inferir a sigla do centro de ensino para registros que não possuem um centro definido.
    - Utiliza um dicionário de mapeamento com nomes de centros formatados e suas respectivas siglas.
    - Se um centro estiver vazio, busca na descrição correspondente por menções a nomes de centros conhecidos.
    - Mantém o valor original do centro se ele já estiver preenchido.

    ### Parâmetros
    - list_centros (list[str]): Uma lista com as siglas dos centros, podendo conter strings vazias.
    - list_descriptions (list[str]): Uma lista paralela com as descrições dos trabalhos.

    ### Saídas
    - list[str]: Uma nova lista de siglas de centros, com os valores vazios potencialmente preenchidos.
    """
    forced_list_centros = []
    dic_formatted_centros = {format_text('Centro Tecnológico, de Ciências exatas e Educação',special_treatment=True).strip():'CTE',
                             format_text('Centro de Ciências Físicas e Matemáticas',special_treatment=True).strip():'CFM',
                             format_text('Centro de Ciências, Tecnologias e Saúde',special_treatment=True).strip():'CTS',
                             format_text('Centro de Filosofia e Ciências Humanas',special_treatment=True).strip():'CFH',
                             format_text('Centro de Comunicação e Expressão',special_treatment=True).strip():'CCE',
                             format_text('Centro Tecnológico de Joinville',special_treatment=True).strip():'CTJ',
                             format_text('Centro de Ciências da Educação',special_treatment=True).strip():'CED',
                             format_text('Centro de Ciências Biológicas',special_treatment=True).strip():'CCB',
                             format_text('Centro de Ciências Jurídicas',special_treatment=True).strip():'CCJ',
                             format_text('Centro de Ciências Agrárias',special_treatment=True).strip():'CCA',
                             format_text('Centro de Ciências da Saúde',special_treatment=True).strip():'CCS',
                             format_text('Centro de Ciências Rurais',special_treatment=True).strip():'CCR',
                             format_text('Centro Socio-econômico',special_treatment=True).strip():'CSE', # Primeira variação do CSE
                             format_text('Centro Socioeconômico',special_treatment=True).strip():'CSE', # Segunda variação do CSE
                             format_text('Centro de Desportos',special_treatment=True).strip():'CDS',                             
                             format_text('Centro Tecnológico',special_treatment=True).strip():'CTC'}
    for centro,description in zip(list_centros,list_descriptions):
        if centro == '' and description.strip():
            formatted_description = format_text(description,special_treatment=True).replace('centro_de_','centro_').strip()
            centro_status = False
            for formatted_centro in dic_formatted_centros.keys():
                if formatted_centro.replace('centro_de_','centro_') in formatted_description:
                    forced_list_centros.append(dic_formatted_centros[formatted_centro])
                    centro_status = True
                    break
            if not centro_status:
                forced_list_centros.append('')
        else:
            forced_list_centros.append(centro)
    return forced_list_centros

def get_list_of_centro_from_campus(list_centros : list[str],
                            list_campus : list[str]) -> list[str]:
    """
    ### Funcionalidades
    - Tenta inferir a sigla do centro de ensino com base no campus.
    - Esta lógica se aplica apenas a campi que possuem um único centro de ensino.
    - Se um registro pertence a um desses campi e não tem um centro definido, o centro único é atribuído a ele.
    - Mantém o valor original do centro em todos os outros casos.

    ### Parâmetros
    - list_centros (list[str]): Uma lista com as siglas dos centros, podendo conter strings vazias.
    - list_campus (list[str]): Uma lista paralela com as siglas dos campi.

    ### Saídas
    - list[str]: Uma nova lista de siglas de centros, com valores preenchidos para campi de centro único.
    """
    forced_centros = []
    campus_with_just_one_centro = [campi for campi in DIC_CAMPUS_CENTROS_COMPLETO_E_SIGLAS if len(DIC_CAMPUS_CENTROS_COMPLETO_E_SIGLAS[campi].keys()) == 1]
    for centro, campi in zip(list_centros,list_campus):
        if centro == '' and campi in campus_with_just_one_centro:
            centro_full_name = list(DIC_CAMPUS_CENTROS_COMPLETO_E_SIGLAS[campi].keys())[0]
            forced_centros.append(DIC_CAMPUS_CENTROS_COMPLETO_E_SIGLAS[campi][centro_full_name])
        else:
            forced_centros.append(centro)
    return forced_centros

def insert_centro_into_df(df : pd.DataFrame) -> pd.DataFrame:
    """
    ### Funcionalidades
    - Adiciona ou preenche a coluna 'centro' em um DataFrame usando uma abordagem em duas etapas.
    - Primeiro, tenta inferir o centro a partir do campus, para os casos de campi com centro único.
    - Em seguida, para os registros ainda sem centro, tenta inferi-lo a partir da coluna 'description'.
    - Inicializa a coluna 'centro' com valores vazios antes de aplicar as lógicas de inferência.

    ### Parâmetros
    - df (pd.DataFrame): O DataFrame a ser modificado. Deve conter as colunas 'campus' e 'description'.

    ### Saídas
    - pd.DataFrame: O DataFrame com a coluna 'centro' adicionada ou atualizada.
    """
    # Não podemos usar insert_centro_from_cursos_ufsc() porque há cursos com o mesmo tipo que são oferecidos em diferentes centros
    # Como Eng. Controle e Automação no CTC (FLN) e CTE (BNU)
    # df = insert_centro_from_cursos_ufsc(df)
    df['centro'] = ''
    df['centro'] = get_list_of_centro_from_campus(list_centros=df['centro'].to_list(),
                                           list_campus=df['campus'].to_list())
    df['centro'] = get_list_of_centro_from_description(list_centros=df['centro'].to_list(),
                                               list_descriptions=df['description'].to_list())
    return df


def get_centro_from_campus_and_course(list_centros : list[str],
                                      list_campus : list[str],
                                      list_courses : list[str]) -> list[str]:    
    """
    ### Funcionalidades
    - Tenta inferir a sigla do centro de ensino para registros que não possuem um centro definido, mas possuem campus e curso.
    - Utiliza o dicionário global `DIC_CAMPUS_CURSOS_CENTROS_SIGLAS` como fonte de dados para a consulta direta.
    - Opera sobre listas paralelas de centros, campi e cursos.
    - Retorna a sigla do centro encontrada ou uma string vazia em caso de falha na busca.

    ### Parâmetros
    - list_centros (list[str]): Uma lista com as siglas dos centros, podendo conter strings vazias.
    - list_campus (list[str]): Uma lista paralela com as siglas dos campi.
    - list_courses (list[str]): Uma lista paralela com os nomes dos cursos.

    ### Saídas
    - list[str]: Uma nova lista de siglas de centros, com os valores vazios potencialmente preenchidos.
    """
    forced_list_centros = []
    for centro,campus,curso in zip(list_centros,list_campus,list_courses):
        if centro == '':
            if campus.strip() and curso.strip():
                try:
                    desired_centro = DIC_CAMPUS_CURSOS_CENTROS_SIGLAS[campus][curso]
                    forced_list_centros.append(desired_centro)
                except Exception as e:
                    forced_list_centros.append('')
            else:
                forced_list_centros.append('')
        else:
            forced_list_centros.append('')
    return forced_list_centros

def insert_centro_from_campus_and_course_into_df(df : pd.DataFrame) -> pd.DataFrame:
    """
    ### Funcionalidades
    - Atualiza a coluna 'centro' em um DataFrame com base nas colunas 'campus' e 'course'.
    - Utiliza a função `get_centro_from_campus_and_course` para realizar a busca e preenchimento dos dados.

    ### Parâmetros
    - df (pd.DataFrame): O DataFrame a ser modificado. Deve conter as colunas 'centro', 'campus' e 'course'.

    ### Saídas
    - pd.DataFrame: O DataFrame com a coluna 'centro' atualizada.
    """
    df['centro'] = get_centro_from_campus_and_course(list_centros=df['centro'].to_list(),
                                                     list_campus=df['campus'].to_list(),
                                                     list_courses=df['course'].to_list())

def get_gender_by_name(name: str) -> str:
    """
    ### Funcionalidades
    - Infere o gênero ('M' para masculino, 'F' para feminino) a partir de um único nome.
    - Isola o primeiro nome de uma string de nome completo.
    - Utiliza uma biblioteca externa (`br_gender_info`) para realizar a predição.
    - Retorna uma string vazia se o gênero não puder ser determinado.

    ### Parâmetros
    - name (str): O nome a ser analisado.

    ### Saídas
    - str: 'M', 'F' ou uma string vazia.
    """
    if name:
        name = name.split()[0]
        genero = br_gender_info.get_gender(name)
        if genero == 'Male':
            return 'M'
        elif genero == 'Female':
            return 'F'
    return ''

def get_author_first_name(author_name : str) -> str:
    """
    ### Funcionalidades
    - Extrai o primeiro nome de uma string de autor, assumindo o formato "Sobrenome, Nome".
    - Localiza a vírgula, extrai a parte subsequente e retorna a primeira palavra dessa parte.

    ### Parâmetros
    - author_name (str): O nome completo do autor.

    ### Saídas
    - str: O primeiro nome do autor ou uma string vazia.
    """
    if ',' in author_name:
        comma_index = author_name.index(',')
        if comma_index + 1 < len(author_name):
            author_name = author_name[comma_index+1:].strip()
            if author_name:
                return author_name.split()[0]
    return ''

def get_authors_first_names(authors : str) -> list[str]:
    """
    ### Funcionalidades
    - Extrai uma lista de primeiros nomes a partir de uma string que contém múltiplos autores.
    - Assume que os nomes dos autores são separados por ponto e vírgula (';').
    - Aplica a função `get_author_first_name` a cada autor individualmente.

    ### Parâmetros
    - authors (str): A string contendo os nomes dos autores separados por ';'.

    ### Saídas
    - list[str]: Uma lista com os primeiros nomes de todos os autores.
    """
    authors_first_names = []
    splitted_authors = authors.split(';')
    for author in splitted_authors:
        author_first_name = get_author_first_name(author)
        if author_first_name:
            authors_first_names.append(author_first_name)
    return authors_first_names

def get_authors_gender_by_name(authors : str) -> str:
    """
    ### Funcionalidades
    - Determina o gênero agregado para uma string de autores.
    - Extrai os primeiros nomes e infere o gênero de cada um.
    - Consolida os resultados em uma única string: 'F' se todos forem femininos, 'M' se todos masculinos, e 'F,M' se houver ambos.

    ### Parâmetros
    - authors (str): A string contendo os nomes dos autores separados por ';'.

    ### Saídas
    - str: Uma string representando o(s) gênero(s) encontrado(s) ('F', 'M', 'F,M') ou uma string vazia.
    """
    authors_first_names = get_authors_first_names(authors)
    if authors_first_names:
        genders = ''
        for author_first_name in authors_first_names:
            author_gender_name = get_gender_by_name(author_first_name)
            if author_gender_name not in genders:
                if genders:
                    genders += f',{author_gender_name}'
                else:
                    genders = author_gender_name
        if 'F' in genders and 'M' in genders: # Deixar valor padrão quando tiver os 2 gêneros
            genders = 'F,M'
        return genders
    return ''

def get_gender_by_name_list_for_df(list_authors_names : list[str]) -> list[str]:
    """
    ### Funcionalidades
    - Aplica a função de inferência de gênero a uma lista de strings de autores.
    - Serve como uma função auxiliar para processamento em lote, ideal para DataFrames.

    ### Parâmetros
    - list_authors_names (list[str]): Uma lista onde cada item é uma string de autores.

    ### Saídas
    - list[str]: Uma lista com a string de gênero correspondente para cada item da lista de entrada.
    """
    return [get_authors_gender_by_name(authors_name) for authors_name in list_authors_names]

def insert_gender_by_name_into_df(df : pd.DataFrame) -> pd.DataFrame:
    """
    ### Funcionalidades
    - Adiciona a coluna 'gender_name' a um DataFrame.
    - Popula a nova coluna inferindo o gênero a partir da coluna 'authors'.

    ### Parâmetros
    - df (pd.DataFrame): O DataFrame a ser modificado, que deve conter a coluna 'authors'.

    ### Saídas
    - pd.DataFrame: O DataFrame original com a nova coluna 'gender_name'.
    """
    df['gender_name'] = get_gender_by_name_list_for_df(list_authors_names=df['authors'].to_list())
    return df

def get_list_of_campus_from_centro(list_of_centros : list[str],
                                   list_of_campus : list[str]) -> list[str]:
    """
    ### Funcionalidades
    - Tenta inferir o campus para registros que não o possuem, baseando-se na sigla do centro.
    - Itera sobre o dicionário `DIC_CAMPUS_CENTROS_COMPLETO_E_SIGLAS` para encontrar a qual campus um determinado centro pertence.
    - Mantém o valor original do campus se ele já estiver preenchido.

    ### Parâmetros
    - list_of_centros (list[str]): Uma lista com as siglas dos centros.
    - list_of_campus (list[str]): Uma lista paralela com as siglas dos campi, podendo conter strings vazias.

    ### Saídas
    - list[str]: Uma nova lista de siglas de campi, com os valores vazios potencialmente preenchidos.
    """
    forced_campus = []
    for campi, centro in zip(list_of_campus,list_of_centros):
        if campi == '' and centro.strip():
            status_campi = False
            for desired_campi in DIC_CAMPUS_CENTROS_COMPLETO_E_SIGLAS.keys():
                if centro in [DIC_CAMPUS_CENTROS_COMPLETO_E_SIGLAS[desired_campi][centro_full_name] for centro_full_name in DIC_CAMPUS_CENTROS_COMPLETO_E_SIGLAS[desired_campi].keys()]:
                    forced_campus.append(desired_campi)
                    status_campi = True
                    break
            if not status_campi:
                forced_campus.append('')
        else:
            forced_campus.append(campi)
    return forced_campus

def adjust_campus_from_centro(df : pd.DataFrame) -> pd.DataFrame:   
    """
    ### Funcionalidades
    - Realiza um passo final de ajuste na coluna 'campus'.
    - Utiliza a função `get_list_of_campus_from_centro` para preencher valores de campus faltantes com base na coluna 'centro'.

    ### Parâmetros
    - df (pd.DataFrame): O DataFrame a ser ajustado. Deve conter as colunas 'centro' e 'campus'.

    ### Saídas
    - pd.DataFrame: O DataFrame com a coluna 'campus' ajustada.
    """ 
    df['campus'] = get_list_of_campus_from_centro(list_of_centros=df['centro'].to_list(),
                                                  list_of_campus=df['campus'].to_list())
    return df

def insert_new_columns_into_df(df : pd.DataFrame,
                               logger:logging.Logger|None=None) -> pd.DataFrame:
    """
    ### Funcionalidades
    - Orquestra a execução de um pipeline completo de enriquecimento de dados em um DataFrame.
    - Executa uma sequência de funções para preencher valores nulos, formatar colunas e inferir novos dados, como gênero, localização, curso e centro de ensino.
    - Aplica as transformações em uma ordem lógica para garantir que as dependências entre os dados sejam resolvidas corretamente (ex: a localização é inferida antes do curso).
    - Inclui tratamento de erros para capturar e registrar falhas em qualquer etapa do pipeline, retornando o DataFrame no estado em que estava antes do erro.

    ### Parâmetros
    - df (pd.DataFrame): O DataFrame inicial, contendo os dados brutos extraídos.
    - logger (logging.Logger | None): Uma instância opcional de um logger para registrar o andamento e possíveis erros.

    ### Saídas
    - pd.DataFrame: O DataFrame totalmente processado e enriquecido com as novas colunas.
    """
    try:
        txt_log_error = 'Problema na inserção de colunas no dataframe com função fillna()'
        df.fillna('',inplace=True)
        txt_log_error = 'Problema na inserção de colunas no dataframe com função astype()'
        df = df.astype(str)

        txt_log_error = 'Problema na inserção de colunas no dataframe com formatação da coluna type com função format_type()'
        df['type'] = df['type'].apply(format_type)

        txt_log_error = 'Problema na inserção de colunas no dataframe com função insert_gender_by_name_into_df()'
        df = insert_gender_by_name_into_df(df)
        
        txt_log_error = 'Problema na inserção de colunas no dataframe com função insert_location_into_df()'
        df = insert_location_into_df(df,logger=logger)

        txt_log_error = 'Problema na inserção de colunas no dataframe com função insert_curso_into_df()'
        df = insert_curso_into_df(df)
        
        txt_log_error = 'Problema na inserção de colunas no dataframe com função insert_type_course_based_on_type_into_df()'
        df = insert_type_course_based_on_type_into_df(df,logger=logger)
        
        txt_log_error = 'Problema na inserção de colunas no dataframe com função insert_type_curso_based_on_description_into_df()'
        df = insert_type_curso_based_on_description_into_df(df)
        
        txt_log_error = 'Problema na inserção de colunas no dataframe com função insert_campus_from_description_into_df()'
        df = insert_campus_from_description_into_df(df)
        
        txt_log_error = 'Problema na inserção de colunas no dataframe com função insert_centro_from_description_into_df()'
        df = insert_centro_into_df(df)

        txt_log_error = 'Problema na inserção de colunas no dataframe com função adjust_campus_from_centro()'
        df = adjust_campus_from_centro(df)
        
        txt_log_error = 'Problema na inserção de colunas no dataframe com construção da coluna year com função extract_year()'
        df['year'] = df['issued_date'].apply(extract_year)
    except Exception as e:
        if logger:
            logger.error(f'{txt_log_error} --> "{e}"',exc_info=True)
    return df

def order_df_columns(df : pd.DataFrame) -> pd.DataFrame:
    """
    ### Funcionalidades
    - Reordena as colunas de um DataFrame para uma sequência predefinida e mais legível.
    - Prioriza um conjunto específico de colunas na ordem desejada.
    - Mantém todas as outras colunas (novas ou inesperadas) no final do DataFrame, sem perdê-las.

    ### Parâmetros
    - df (pd.DataFrame): O DataFrame cujas colunas serão reordenadas.

    ### Saídas
    - pd.DataFrame: Uma nova visualização do DataFrame com as colunas na ordem especificada.
    """    
    column_order = [
        'identifier_header', 'datestamp_header', 'setSpec', 'title', 'authors', 'advisors', 'co_advisors',
        'issued_date', 'available_date', 'accessioned_date',
        'language', 'subjects', 'type', 'publisher', 'description',
        'abstract', 'link_site', 'link_doc', 'source_xml_file'
    ]
    existing_ordered_cols = [col for col in column_order if col in df.columns]
    remaining_cols = [col for col in df.columns if col not in existing_ordered_cols]
    final_columns = existing_ordered_cols + remaining_cols
    df = df[final_columns]
    return df

def transform_df(df : pd.DataFrame,logger:logging.Logger|None=None) -> pd.DataFrame:
    """
    ### Funcionalidades
    - Atua como o ponto de entrada principal para todo o processo de transformação de um DataFrame.
    - Encapsula a lógica de enriquecimento e ordenação de colunas.
    - Primeiro, chama `insert_new_columns_into_df` para adicionar e inferir todos os novos dados.
    - Em seguida, chama `order_df_columns` para organizar o DataFrame final.
    - Suporta o registro de logs para marcar a finalização de cada etapa principal.

    ### Parâmetros
    - df (pd.DataFrame): O DataFrame bruto a ser transformado.
    - logger (logging.Logger | None): Uma instância opcional de um logger.

    ### Saídas
    - pd.DataFrame: O DataFrame final, totalmente transformado, enriquecido e ordenado.
    """
    df = insert_new_columns_into_df(df,logger)
    if logger:
        logger.info('Tentativa de inserção de colunas finalizada')

    df = order_df_columns(df)    
    if logger:
        logger.info('Tentativa de ordenação de colunas finalizada')

    return df
