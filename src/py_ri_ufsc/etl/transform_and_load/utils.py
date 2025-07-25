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
    """Converte uma lista de strings em uma única string separada por ';', ou retorna None."""
    if data_list and isinstance(data_list, list):
        cleaned_list = [str(item).strip() for item in data_list if str(item).strip()]
        if not cleaned_list:
            return None
        return ';'.join(cleaned_list)
    elif isinstance(data_list, str) and data_list.strip():
        return data_list.strip()
    return None

def get_date_field(element, date_type_name):
    """Extrai um tipo específico de data (issued, available, accessioned)."""
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

def get_specific_dc_field(element, dc_element_name, sub_elements=None):
    """
    Extrai um campo específico do DC, com capacidade de navegar por sub_elements,
    priorizando pt_BR, none, en, ou o primeiro valor encontrado.
    Retorna uma string unida por ';' se múltiplos valores forem encontrados, ou uma única string.
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
    Extrai o texto de descrição principal, excluindo o conteúdo do abstract.
    Prioriza pt_BR, depois none, depois en, ou texto direto.
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
    """Extrai valores de campos de contribuidores (author, advisor, advisor-co)."""
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
    Retorna o primeiro valor de texto que encontrar usando a expressão XPath,
    ou None se não encontrar nada.
    """
    if element is None:
        return None
    results = element.xpath(xpath_expr, namespaces=NAMESPACES)
    if results:
        return results[0].strip() if results[0] else None
    return None

def extract_identifier(header, _): 
    return get_text_xpath(header, './oai:identifier/text()')

def extract_datestamp(header, _): 
    return get_text_xpath(header, './oai:datestamp/text()')

def extract_set_spec(header, _):
    specs = header.xpath('./oai:setSpec/text()', namespaces=NAMESPACES)
    for spec in specs:
        if spec.strip().startswith("col_"):
            return spec.strip()
    return None

def extract_authors(_, metadata): 
    return format_list_to_string(get_contributor_field_values(metadata, "author"))

def extract_advisors(_, metadata): 
    return format_list_to_string(get_contributor_field_values(metadata, "advisor"))

def extract_co_advisors(_, metadata): 
    return format_list_to_string(get_contributor_field_values(metadata, "advisor-co"))

def extract_link_doc(_, metadata):
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
    return get_specific_dc_field(metadata, "language", sub_elements=["iso"])

def extract_link_site(_, metadata):
    return get_specific_dc_field(metadata, "identifier", sub_elements=["uri"])

def extract_subjects(_, metadata):
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
    return get_specific_dc_field(metadata, field_name)

def extract_date_field(_, metadata, field_name):  # para issued, available, accessioned
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
    Extrai dados estruturados de um arquivo XML, retornando uma lista de dicionários.

    Parâmetros:
        - xml_file_path: caminho do arquivo XML
        - desired_fields: lista de nomes dos campos desejados (colunas do dicionário)
        - logger: instância de logger (opcional). Se None, não loga nada.
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
    if os.path.exists(COL_TO_NAME_CSV_FILE_PATH):
        with open(COL_TO_NAME_CSV_FILE_PATH, "r", encoding="utf-8") as f:
            reader = csv.reader(f)
            next(reader)  # pular cabeçalho
            return {linha[0]: linha[1] for linha in reader}
    else:
        return {}
    
dic_col_to_name = get_col_to_name_csv_file()

def save_col_to_name_csv_file(dic_col_to_name : dict[str,str]):
    with open(COL_TO_NAME_CSV_FILE_PATH, "w", newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(["col", "location"])  # cabeçalho (opcional)
        for col, location in dic_col_to_name.items():
            writer.writerow([col, location])

def extract_year(date_str):
    if pd.isnull(date_str):
        return None
    match = re.match(r'(\d{4})', str(date_str))
    if match:
        return match.group(1)
    return ''

def format_type(work_type : str) -> str:
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
    
    # Esperamos que col seja algo como "col_123456789_75030" ...

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
    return full_location.split('->')[0].strip()

def get_academic_work_last_collection(full_location : str) -> str:
    return full_location.split('->')[-1].strip()

def insert_location_into_df(df : pd.DataFrame,logger : logging.Logger|None = None) -> pd.DataFrame:
    setSpecs = df['setSpec'].to_list()
    df['full_locations'] = [get_academic_work_location(value,logger=logger) if value else '' for value in setSpecs]    
    df['first_com'] = [get_academic_work_first_community(value) if value else '' for value in df['full_locations']]
    df['last_col'] = [get_academic_work_last_collection(value) if value else '' for value in df['full_locations']]

    return df

def split_full_location(full_location : str) -> list[str]:
    splitted_full_location = [loc.strip() for loc in full_location.split('->') if len(loc.strip())>3]
    return splitted_full_location

def treat_locations(full_location : str, reverse : bool = True) -> list[str]:
    full_location = re.sub(r'Curso de|Programa de Pós-Graduação em','',full_location,flags=re.IGNORECASE).strip()
    location_elements = [format_text(loc,special_treatment=True).strip() for loc in split_full_location(full_location)]    
    if reverse:
        location_elements.reverse() # Trabalharemos com prioridade para as últimas localizações (ler de trás para frente)
    return location_elements

def get_curso_from_full_location(full_location : str,courses : list[str]|None = None) -> str:
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
    courses = []
    for course,full_location in zip(list_of_courses,list_of_full_locations):
        if course.strip() == '':
            courses.append(get_curso_from_full_location(full_location=full_location,courses=ufsc_courses))
        else:
            courses.append(course)
    return courses

def split_description(description : str) -> list[str]:
    splitted_description = [desc.strip() for desc in re.split(r'\s\-\s|\,|\.',description) if len(desc.strip())>3]
    return splitted_description

def treat_descriptions(description : str, reverse : bool = True) -> list[str]:
    description = re.sub(r'Curso de|Programa de Pós-Graduação em','',description,flags=re.IGNORECASE).strip()   
    description_elements = [format_text(element,special_treatment=True).strip() for element in split_description(description)]
    if reverse:
        description_elements.reverse()
    return description_elements

def get_curso_from_description(description : str, courses : list[str]|None = None) -> str:
    description_elements = treat_descriptions(description)
    for element in description_elements:
        for curso_ufsc in [c for c in courses if len(c) <= len(element)]:
            curso_ufsc_formatted = format_text(curso_ufsc,special_treatment=True)
            if curso_ufsc_formatted == element:
                return curso_ufsc
    return ''

def insert_curso_into_df(df : pd.DataFrame) -> pd.DataFrame:
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
    Adiciona coluna 'type_course' com valores 'POS', 'GRAD' ou string vazia ("")
    com base no conteúdo da coluna 'type'.
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
    # Não podemos usar insert_campus_from_cursos_ufsc() porque há cursos com o mesmo tipo que são oferecidos em diferentes campus
    # Como Agronomia (GRAD) em FLN e CUR / Eng. Controle e Automação (GRAD) FLN e BNU / Materiais (GRAD) / Medicina (GRAD), etc
    # df = insert_campus_from_cursos_ufsc(df)
    df['campus'] = ''
    df['campus'] = get_campus_from_description(list_campus=df['campus'].to_list(),list_descriptions=df['description'].to_list())

    return df


def get_list_of_centro_from_description(list_centros : list[str],
                                list_descriptions : list[str]) -> list[str]:
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
    df['centro'] = get_centro_from_campus_and_course(list_centros=df['centro'].to_list(),
                                                     list_campus=df['campus'].to_list(),
                                                     list_courses=df['course'].to_list())

def get_gender_by_name(name: str) -> str:
    if name:
        name = name.split()[0]
        genero = br_gender_info.get_gender(name)
        if genero == 'Male':
            return 'M'
        elif genero == 'Female':
            return 'F'
    return ''

def get_author_first_name(author_name : str) -> str:
    if ',' in author_name:
        comma_index = author_name.index(',')
        if comma_index + 1 < len(author_name):
            author_name = author_name[comma_index+1:].strip()
            if author_name:
                return author_name.split()[0]
    return ''

def get_authors_first_names(authors : str) -> list[str]:
    authors_first_names = []
    splitted_authors = authors.split(';')
    for author in splitted_authors:
        author_first_name = get_author_first_name(author)
        if author_first_name:
            authors_first_names.append(author_first_name)
    return authors_first_names

def get_authors_gender_by_name(authors : str) -> str:
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
    return [get_authors_gender_by_name(authors_name) for authors_name in list_authors_names]

def insert_gender_by_name_into_df(df : pd.DataFrame) -> pd.DataFrame:
    df['gender_name'] = get_gender_by_name_list_for_df(list_authors_names=df['authors'].to_list())
    return df

def get_list_of_campus_from_centro(list_of_centros : list[str],
                                   list_of_campus : list[str]) -> list[str]:
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
    df['campus'] = get_list_of_campus_from_centro(list_of_centros=df['centro'].to_list(),
                                                  list_of_campus=df['campus'].to_list())
    return df

def insert_new_columns_into_df(df : pd.DataFrame,
                               logger:logging.Logger|None=None) -> pd.DataFrame:
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
    # Ordenando colunas conforme desejado
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
    df = insert_new_columns_into_df(df,logger)
    if logger:
        logger.info('Tentativa de inserção de colunas finalizada')

    df = order_df_columns(df)    
    if logger:
        logger.info('Tentativa de ordenação de colunas finalizada')

    return df
