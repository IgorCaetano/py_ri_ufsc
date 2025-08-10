import re
import unicodedata
import ftfy
from string import punctuation, printable

LISTA_PUNCTS = punctuation.replace('-', '').replace('.', '')
NORMAL_CHARACTERS = printable + 'áàâãéèêíìîóòôõúùûüç' + 'áàâãéèêíìîóòôõúùûüç'.upper() + '–' + 'ª' + '°' + 'º'

STANDARD_SPECIAL_CHARACTERS_STRING = punctuation

def normalize_text(text: str) -> str:
    """
    ### Funcionalidades
    - Normaliza uma string de entrada, removendo todos os caracteres de acentuação e diacríticos.
    - Utiliza a forma de decomposição canônica (NFD) do Unicode para separar os caracteres base de seus modificadores (acentos).
    - Filtra e descarta os caracteres modificadores (categoria 'Mn' - Mark, Nonspacing).
    - Retorna a string limpa, contendo apenas os caracteres base (ex: 'ç' se torna 'c', 'ã' se torna 'a').

    ### Parâmetros
    - text (str): A string de entrada que precisa ser normalizada.

    ### Saídas
    - str: Uma nova string sem acentuação ou outros diacríticos.

    ### Exemplo de uso
    >>> entrada = "Amanhã, a programação será focada em otimização e solução de BI."
    >>> saida = normalize_text(entrada)
    >>> print(saida)
    'Amanha, a programacao sera focada em otimizacao e solucao de BI.'
    """
    return ''.join(c for c in (d for char in text for d in unicodedata.normalize('NFD', char) if unicodedata.category(d) != 'Mn'))
    

def remove_strange_characters_from_text(text: str) -> str:
    """
    ### Funcionalidades
    - Substitui o caractere de espaço "não quebrável" (non-breaking space, `\xa0`) por um espaço padrão.
    - Identifica e remove da string todos os caracteres que não estão presentes na coleção `NORMAL_CHARACTERS`.
    - O funcionamento da função depende criticamente do conteúdo da variável externa `NORMAL_CHARACTERS`.

    ### Parâmetros
    - text (str): A string de entrada que será limpa.

    ### Saídas
    - str: Uma nova string contendo apenas os caracteres permitidos em `NORMAL_CHARACTERS`.

    ### Exemplo de uso
    >>> entrada = "texto com símbolos® e um emoji 🤗"
    >>> saida = remove_strange_characters_from_text(entrada)
    >>> print(saida)
    'texto com símbolos e um emoji '
    """
    text = text.replace('\xa0', ' ') # Espaço em branco que as vezes aparece em algumas strings
    characters_to_remove = set([c for c in text if c not in NORMAL_CHARACTERS])
    for strange_character in characters_to_remove:
        text = text.replace(strange_character, '')
    return text

def remove_extra_blank_spaces_from_text(text: str) -> str:
    """
    ### Funcionalidades
    - Utiliza uma expressão regular para substituir sequências de um ou mais caracteres de espaço em branco por um único espaço.
    - Preserva os caracteres de quebra de linha e tab (`\n`,`\t`), não os substituindo.

    ### Parâmetros
    - text (str): A string de entrada que pode conter espaços em branco excessivos.

    ### Saídas
    - str: Uma nova string com os espaços em branco normalizados para um único espaço entre as palavras.

    ### Exemplo de uso
    >>> entrada = "Texto   com    muitos    espaços e  \n com quebra de linha."
    >>> saida = remove_extra_blank_spaces_from_text(entrada)
    >>> print(repr(saida)) # Usando repr() para ver os caracteres especiais
    'Texto com muitos espaços e \n com quebra de linha.'
    """
    return re.sub(r'[^\S\n]+', ' ', text)

def remove_special_characters_from_text(text: str,
                                        string_special_characters: str = STANDARD_SPECIAL_CHARACTERS_STRING,
                                        remove_extra_blank_spaces: bool = True,
                                        remove_hiphen_btwn_words: bool = False,
                                        tratamento_personalizado: bool = True) -> str:
    """
    ### Funcionalidades
    - Remove um conjunto de caracteres especiais de uma string.
    - Possui um "tratamento personalizado" (padrão) que substitui barras (`/`, `\\`) e opcionalmente hífens (`-`) por espaços para evitar a junção de palavras.
    - Permite, opcionalmente, preservar hífens que conectam palavras (ex: "segunda-feira").
    - Ao final, se desejado, remove espaços múltiplos
    - Remove espaços nas extremidades da string.

    ### Parâmetros
    - text (str): A string de entrada a ser limpa.
    - string_special_characters (str): Uma string contendo todos os caracteres a serem removidos. O padrão é a constante `STANDARD_SPECIAL_CHARACTERS_STRING`.
    - remove_extra_blank_spaces (bool): Se `True`, remove espaços extras resultantes da limpeza.
    - remove_hiphen_btwn_words (bool): Se `False` (padrão), o hífen entre palavras será preservado. Se `True`, ele será removido.
    - tratamento_personalizado (bool): Se `True` (padrão), aplica a substituição de barras por espaço. Se `False`, apenas deleta os caracteres especiais.

    ### Saídas
    - str: Uma nova string sem os caracteres especiais especificados.

    ### Exemplo de uso
    #### Exemplo 1: Comportamento padrão
    >>> entrada1 = "Relatório (v1) de input/output para segunda-feira 02/05/2025."
    >>> saida1 = remove_special_characters_from_text(entrada1)
    >>> print(saida1)
    'Relatório v1 de input output para segunda-feira 02 05 2025'

    #### Exemplo 2: Removendo também o hífen com tratamento personalizado "desligado"
    >>> entrada1 = "Relatório (v1) de input/output para segunda-feira 02/05/2025."
    >>> saida2 = remove_special_characters_from_text(entrada2,remove_hiphen_btwn_words=True,tratamento_personalizado=False)
    >>> print(saida2)
    'Relatório v1 de inputoutput para segundafeira 02052025'
    """
    if not remove_hiphen_btwn_words:
        string_special_characters = string_special_characters.replace('-', '')
        text = text.replace(' -', ' ').replace('- ', ' ')
    if not tratamento_personalizado:
        text = text.translate(str.maketrans('', '', string_special_characters))
    else:
        if remove_hiphen_btwn_words:
            string_special_characters_ad_espaco = r'\/\\\-'
        else:
            string_special_characters_ad_espaco = r'\/\\'
        text = text.translate(str.maketrans(string_special_characters_ad_espaco,' '*len(string_special_characters_ad_espaco)))
        text = text.translate(str.maketrans('', '', string_special_characters))
    if remove_extra_blank_spaces:
        text = re.sub(r'\s+', ' ', text)
    return text.strip()


def format_text(text: str,
                lower_case: bool = False,
                normalize: bool = False,
                remove_special_characters: bool = False,
                string_special_characters: str = STANDARD_SPECIAL_CHARACTERS_STRING,
                remove_extra_blank_spaces: bool = True,
                remove_strange_characters: bool = True,
                special_treatment: bool = False) -> str:
    """
    ### Funcionalidades
    - Pipeline completo e customizável para limpeza e formatação de texto.
    - Orquestra a execução de várias operações: correção de codificação (ftfy), remoção de acentos, remoção de caracteres estranhos e especiais, conversão para minúsculas e ajuste de espaços.
    - Possui um modo `special_treatment` que aplica um conjunto rigoroso de regras para gerar uma string padronizada em `snake_case`.

    ### Parâmetros
    - text (str): A string original a ser formatada.
    - lower_case (bool): Se `True`, converte todo o texto para minúsculas.
    - normalize (bool): Se `True`, remove a acentuação (ex: "olá" -> "ola").
    - remove_special_characters (bool): Se `True`, remove caracteres especiais.
    - string_special_characters (str): Define os caracteres especiais a serem removidos.
    - remove_extra_blank_spaces (bool): Se `True`, remove espaços em excesso.
    - remove_strange_characters (bool): Se `True`, corrige falhas de codificação (UTF-8) e remove caracteres não-padrão.
    - special_treatment (bool): Se `True`, ativa um preset de formatação (todas as limpezas ativadas) e converte espaços em `_` (underline) no final.

    ### Saídas
    - str: A string final após todas as transformações aplicadas.
    """
    if special_treatment:
        lower_case = True
        normalize = True
        remove_special_characters = True
        string_special_characters = string_special_characters.replace('_', '')
        remove_extra_blank_spaces = True
        remove_strange_characters = True

    if remove_strange_characters:
        text = ftfy.fix_text(text)
        text = remove_strange_characters_from_text(text)
    if remove_special_characters:
        if special_treatment:
            text = remove_special_characters_from_text(text,
                                                       string_special_characters=string_special_characters,
                                                       remove_hiphen_btwn_words=True)
        else:
            text = remove_special_characters_from_text(text,
                                                       string_special_characters=string_special_characters)
    if remove_extra_blank_spaces:
        text = remove_extra_blank_spaces_from_text(text)
    if lower_case:
        text = text.lower()
    if normalize:
        text = normalize_text(text)
    if special_treatment:
        text = text.replace(' ', '_')
    return text
