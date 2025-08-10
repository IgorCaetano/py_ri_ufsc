import pandas as pd

from .utils import DIC_CAMPUS_CENTROS_COMPLETO_E_SIGLAS,DIC_CAMPUS_CURSOS_CENTROS_SIGLAS

class CursosUFSC():
    """
    ### Funcionalidades
    - Encapsula informações sobre os cursos, campi e centros da Universidade Federal de Santa Catarina (UFSC).
    - Fornece métodos para consultar listas de cursos, campi e centros com base em estruturas de dados (dicionários) pré-definidas.
    - Permite a ordenação dos resultados obtidos.

    ### Parâmetros
    - silence (bool): Parâmetro de inicialização para controlar mensagens verbosas. Atualmente não implementado nos métodos fornecidos.

    ### Saídas
    - N/A (trata-se da inicialização de um objeto).

    ### Exemplo de uso
    >>> # Instancia a classe para poder usar seus métodos
    >>> ufsc_courses = CursosUFSC()
    """
    def __init__(self,silence : bool = True):
        self.dic_campus_centros_completo_e_siglas = DIC_CAMPUS_CENTROS_COMPLETO_E_SIGLAS
        self.dic_campus_cursos_centros_siglas = DIC_CAMPUS_CURSOS_CENTROS_SIGLAS
        self.silence = silence        

    def get_cursos(self,
                   sort_by_len : bool = True,
                   reverse : bool = True) -> list[str]:
        """
        ### Funcionalidades
        - Extrai e retorna uma lista com os nomes de todos os cursos da UFSC.
        - Agrega os cursos de todos os campi em uma única lista.
        - Permite ordenar a lista resultante pelo comprimento do nome do curso.

        ### Parâmetros
        - sort_by_len (bool): Se `True`, ordena a lista pelo número de caracteres de cada item.
        - reverse (bool): Se `True` (padrão), a ordenação é feita do maior para o menor. Se `False`, do menor para o maior.

        ### Saídas
        - list[str]: Uma lista de strings, onde cada string é o nome de um curso.
        """
        cursos = []
        for campus in self.dic_campus_cursos_centros_siglas.keys():
            cursos += list(self.dic_campus_cursos_centros_siglas[campus].keys())
        if sort_by_len:
            return sorted(cursos,key=len,reverse=reverse)
        return list(cursos)
    
    def get_campus(self,
                   sort_by_len : bool = True,
                   reverse : bool = True) -> list[str]:
        """
        ### Funcionalidades
        - Retorna uma lista com os nomes de todos os campi da UFSC.
        - Permite ordenar a lista resultante pelo comprimento do nome do campus.

        ### Parâmetros
        - sort_by_len (bool): Se `True`, ordena a lista pelo número de caracteres de cada item.
        - reverse (bool): Se `True` (padrão), a ordenação é feita do maior para o menor. Se `False`, do menor para o maior.

        ### Saídas
        - list[str]: Uma lista de strings, onde cada string é o nome de um campus.
        """
        campus = [campi for campi in self.dic_campus_centros_completo_e_siglas.keys()]
        if sort_by_len:
            return sorted(campus,key=len,reverse=reverse)
        return list(campus)
    
    def get_centros(self,
                    siglas : bool = True,
                   sort_by_len : bool = True,
                   reverse : bool = True) -> list[str]:
        """
        ### Funcionalidades
        - Retorna uma lista com os centros de ensino da UFSC.
        - Permite escolher entre retornar os nomes completos dos centros ou apenas suas siglas.
        - Permite ordenar a lista resultante pelo comprimento do nome/sigla.

        ### Parâmetros
        - siglas (bool): Se `True` (padrão), retorna as siglas dos centros (ex: "CTC"). Se `False`, retorna os nomes completos (ex: "Centro Tecnológico").
        - sort_by_len (bool): Se `True`, ordena a lista pelo número de caracteres de cada item.
        - reverse (bool): Se `True` (padrão), a ordenação é feita do maior para o menor. Se `False`, do menor para o maior.

        ### Saídas
        - list[str]: Uma lista de strings, onde cada string é o nome ou a sigla de um centro.
        """
        centros = []
        if siglas:
            for campi in self.dic_campus_centros_completo_e_siglas.keys():
                centros += [self.dic_campus_centros_completo_e_siglas[campi][centro] for centro in self.dic_campus_centros_completo_e_siglas[campi].keys()]
        else:
            for campi in self.dic_campus_centros_completo_e_siglas.keys():
                centros += list(self.dic_campus_centros_completo_e_siglas[campi].keys())
        if sort_by_len:
            return sorted(centros,key=len,reverse=reverse)
        return list(centros)
