import re
import unicodedata
import ftfy
from string import punctuation, printable

LISTA_PUNCTS = punctuation.replace('-', '').replace('.', '')
NORMAL_CHARACTERS = printable + 'áàâãéèêíìîóòôõúùûüç' + 'áàâãéèêíìîóòôõúùûüç'.upper() + '–' + 'ª' + '°' + 'º'

STANDARD_SPECIAL_CHARACTERS_STRING = punctuation

def normalize_text(text: str) -> str:
    return ''.join(c for c in (d for char in text for d in unicodedata.normalize('NFD', char) if unicodedata.category(d) != 'Mn'))

def remove_strange_characters_from_text(text: str) -> str:
    # weird blank space that sometimes appears
    text = text.replace('\xa0', ' ')
    characters_to_remove = set([c for c in text if c not in NORMAL_CHARACTERS])
    # print('Removing:',characters_to_remove)
    for strange_character in characters_to_remove:
        text = text.replace(strange_character, '')
    return text

def remove_extra_blank_spaces_from_text(text: str) -> str:
    return re.sub(r'[^\S\n]+', ' ', text)

def remove_special_characters_from_text(text: str,
                                        string_special_characters: str = STANDARD_SPECIAL_CHARACTERS_STRING,
                                        remove_extra_blank_spaces: bool = True,
                                        remove_hiphen_btwn_words: bool = False,
                                        tratamento_personalizado: bool = True) -> str:
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
        text = text.translate(str.maketrans(
            string_special_characters_ad_espaco, ' '*len(string_special_characters_ad_espaco)))
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
