import pandas as pd

from .utils import DIC_CAMPUS_CENTROS_COMPLETO_E_SIGLAS,DIC_CAMPUS_CURSOS_CENTROS_SIGLAS

class CursosUFSC():
    def __init__(self,silence : bool = True):
        self.dic_campus_centros_completo_e_siglas = DIC_CAMPUS_CENTROS_COMPLETO_E_SIGLAS
        self.dic_campus_cursos_centros_siglas = DIC_CAMPUS_CURSOS_CENTROS_SIGLAS
        self.silence = silence        

    def get_cursos(self,
                   sort_by_len : bool = True,
                   reverse : bool = True) -> list[str]:
        cursos = []
        for campus in self.dic_campus_cursos_centros_siglas.keys():
            cursos += list(self.dic_campus_cursos_centros_siglas[campus].keys())
        if sort_by_len:
            return sorted(cursos,key=len,reverse=reverse)
        return list(cursos)
    
    def get_campus(self,
                   sort_by_len : bool = True,
                   reverse : bool = True) -> list[str]:        
        campus = [campi for campi in self.dic_campus_centros_completo_e_siglas.keys()]
        if sort_by_len:
            return sorted(campus,key=len,reverse=reverse)
        return list(campus)
    
    def get_centros(self,
                    siglas : bool = True,
                   sort_by_len : bool = True,
                   reverse : bool = True) -> list[str]:
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
