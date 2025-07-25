import pandas as pd

from . . . .common.for_strings import format_text

# https://estrutura.ufsc.br/centros-de-ensino/
# https://prograd.ufsc.br/cursos-de-graduacao-da-ufsc/
# https://propg.ufsc.br/cap-2/capdss/guia-dos-programas-de-pos-graduacao-da-ufsc/

# ? Info faltando
# ! Info inserida "a mais"

DIC_CAMPUS_CURSOS_CENTROS_SIGLAS = {'FLN':{'Propriedade Intelectual e Transferência de Tecnologia para Inovação'.upper():'CSE',
                                            'Licenciatura Intercultural Indígena do Sul da Mata Atlântica'.upper():'CFH',
                                            'Engenharia de Transportes e Gestão Territorial'.upper():'CTC',
                                            'Inglês: Estudos Linguísticos e Literários'.upper():'CCE',
                                            'Multicêntrico em Ciências Fisiológicas'.upper():'CCB',
                                            'Biologia Celular e do Desenvolvimento'.upper():'CCB',
                                            'Interdisciplinar em Ciências Humanas'.upper():'CFH',
                                            'Saúde Mental e Atenção Psicossocial'.upper():'CCS',
                                            'Biologia de Fungos, Algas e Plantas'.upper():'CCB',
                                            'Engenharia e Gestão do Conhecimento'.upper():'', # ?
                                            'Engenharia de Controle e Automação'.upper():'CTC',
                                            'Engenharia de Automação e Sistemas'.upper():'CTC',
                                            'Ciência e Tecnologia de Alimentos'.upper():'CCA',
                                            'Ciência e Engenharia de Materiais'.upper():'CTC',
                                            'Educação Científica e Tecnológica'.upper():'CED',
                                            'Planejamento e Controle de Gestão'.upper():'CSE',
                                            'Engenharia Sanitária e Ambiental'.upper():'CTC',
                                            'Gestão do Cuidado em Enfermagem'.upper():'CCS',
                                            'Sociologia e Ciência Política'.upper():'CFH',
                                            'Perícias Criminais Ambientais'.upper():'CCB',
                                            'Métodos e Gestão em Avaliação'.upper():'CTC',
                                            'Letras-Línguas Estrangeiras'.upper():'CCE',
                                            'Recursos Genéticos Vegetais'.upper():'CCA',
                                            'Administração Universitária'.upper():'CSE',
                                            'Biotecnologia e Biociências'.upper():'CCB',
                                            'Matemática Pura e Aplicada'.upper():'CFM',
                                            'Engenharia de Aquicultura'.upper():'CCA',
                                            'Assistência Farmacêutica'.upper():'CCS', 
                                            'Arquitetura e Urbanismo'.upper():'CTC', 
                                            'Engenharia de Alimentos'.upper():'CTC',
                                            'Relações Internacionais'.upper():'CSE',
                                            'Engenharia de Materiais'.upper():'CTC',
                                            'Engenharia de Produção'.upper():'CTC',
                                            'Secretariado Executivo'.upper():'CCE',
                                            'Sistemas de Informação'.upper():'CTC',
                                            'Ciências da Computação'.upper():'CTC',
                                            'Ciências dos Alimentos'.upper():'CCA',
                                            'Engenharia Eletrônica'.upper():'CTC',
                                            'Ciência da Informação'.upper():'CED',
                                            'Ciência da Computação'.upper():'CTC',
                                            'Ciência da Informação'.upper():'CED',
                                            'Informática em Saúde'.upper():'CCS', # ?
                                            'Engenharia Ambiental'.upper():'CTC',
                                            'Sociologia Política'.upper():'CFH', # !
                                            'Antropologia Social'.upper():'CFH',
                                            'Ciências Biológicas'.upper():'CCB',
                                            'Ciências Econômicas'.upper():'CSE',
                                            'Engenharia Elétrica'.upper():'CTC',
                                            'Engenharia Mecânica'.upper():'CTC',
                                            'Estudos da Tradução'.upper():'CCE',
                                            'Engenharia Química'.upper():'CTC',
                                            'Ensino de Biologia'.upper():'CCB',
                                            'Ciências Contábeis'.upper():'CSE',
                                            'Desastres Naturais'.upper():'CFH',
                                            'Engenharia Química'.upper():'CTC',
                                            'Ensino de História'.upper():'CFH',
                                            'Educação do Campo'.upper():'CED',
                                            'Ciências Médicas'.upper():'CCS',   
                                            'Ensino de Física'.upper():'CFM',
                                            'Letras-Português'.upper():'CCE',
                                            'Engenharia Civil'.upper():'CTC',
                                            'Ciências Sociais'.upper():'CFH',
                                            'Agroecossistemas'.upper():'CCA',
                                            'Biblioteconomia'.upper():'CED',
                                            'Educação Física'.upper():'CDS',
                                            'Fonoaudiologia'.upper():'CCS',
                                            'Serviço Social'.upper():'CSE',
                                            'Saúde Pública'.upper():'CCS', # !
                                            'Contabilidade'.upper():'CSE',
                                            'Administração'.upper():'CSE',
                                            'Biotecnologia'.upper():'CCB', # !
                                            'Letras-LIBRAS'.upper():'CCE',
                                            'Neurociências'.upper():'CCB',
                                            'Artes Cênicas'.upper():'CCE',
                                            'Antropologia'.upper():'CFH', 
                                            'Arquivologia'.upper():'CED',    
                                            'Oceanografia'.upper():'CFM',
                                            'Farmacologia'.upper():'CCS',
                                            'Meteorologia'.upper():'CFM',
                                            'Aquicultura'.upper():'CCA',  
                                            'Odontologia'.upper():'CCS',
                                            'Biociências'.upper():'CCB', # !
                                            'Linguística'.upper():'CCE',
                                            'Literatura'.upper():'CCE',
                                            'Matemática'.upper():'CFM',
                                            'Museologia'.upper():'CFH',
                                            'Psicologia'.upper():'CFH',
                                            'Enfermagem'.upper():'CCS',
                                            'Jornalismo'.upper():'CCE',
                                            'Bioquímica'.upper():'CCB',
                                            'Sociologia'.upper():'CFH', # !
                                            'Agronomia'.upper():'CCA',
                                            'Filosofia'.upper():'CFH',
                                            'Geografia'.upper():'CFH',
                                            'Pedagogia'.upper():'CED',
                                            'Zootecnia'.upper():'CCA',
                                            'Animação'.upper():'CCE',
                                            'Ecologia'.upper():'CCB',
                                            'Economia'.upper():'CSE',
                                            'Educação'.upper():'CED',
                                            'História'.upper():'CFH',
                                            'Geologia'.upper():'CFH',
                                            'Biologia'.upper():'CCB', # !
                                            'Farmácia'.upper():'CCS',
                                            'Medicina'.upper():'CCS',
                                            'Nutrição'.upper():'CCS',
                                            'Direito'.upper():'CCJ',
                                            'Química'.upper():'CFM',
                                            'Cinema'.upper():'CCE',
                                            'Design'.upper():'CCE',
                                            'Física'.upper():'CFM',
                                            'Letras'.upper():'CCE'},
                            'CUR':{'Medicina Veterinária Convencional e Integrativa'.upper():'CCR',
                                   'Ecossistemas Agrícolas e Naturais'.upper():'CCR',
                                   'Engenharia Florestal'.upper():'CCR',
                                   'Medicina Veterinária'.upper():'CCR',
                                   'Agronomia'.upper():'CCR'},
                            'JOI':{'Engenharia de Transportes e Logística'.upper():'CTJ',
                                   'Engenharia Ferroviária e Metroviária'.upper():'CTJ',
                                   'Bacharelado em Ciência e Tecnologia'.upper():'CTJ',
                                   'Engenharia Civil de Infraestrutura'.upper():'CTJ',                                   
                                   'Engenharia de Sistemas Eletrônicos'.upper():'CTJ',
                                   'Engenharia e Ciências Mecânicas'.upper():'CTJ',
                                   'Engenharia de Infraestrutura'.upper():'CTJ',
                                   'Engenharia Aeroespacial'.upper():'CTJ',
                                   'Engenharia Automotiva'.upper():'CTJ',
                                   'Engenharia Mecatrônica'.upper():'CTJ',
                                   'Engenharia Naval'.upper():'CTJ'},
                            'ARA':{'Tecnologias da Informação e Comunicação'.upper():'CTS',
                                   'Energia e Sustentabilidade'.upper():'CTS',
                                   'Ciências da Reabilitação'.upper():'CTS',
                                   'Engenharia de Computação'.upper():'CTS',
                                   'Engenharia de Energia'.upper():'CTS',
                                   'Ensino de Física'.upper():'CTS',
                                   'Fisioterapia'.upper():'CTS',
                                   'Medicina'.upper():'CTS'},
                            'BNU':{'Nanociência, Processos e Materiais Avançados'.upper():'CTE',
                                   'Química – Licenciatura e Bacharelado'.upper():'CTE',
                                   'Química - Licenciatura e Bacharelado'.upper():'CTE',
                                   'Engenharia de Controle e Automação'.upper():'CTE',
                                   'Química Licenciatura e Bacharelado'.upper():'CTE',
                                   'Matemática  Licenciatura'.upper():'CTE',
                                   'Engenharia de Materiais'.upper():'CTE',
                                   'Engenharia Têxtil'.upper():'CTE',
                                   'Ensino de Física'.upper():'CTE'}
}

DIC_CAMPUS_CENTROS_COMPLETO_E_SIGLAS = {'FLN':{'Centro de Ciências Agrárias':'CCA',
                                               'Centro de Ciências Biológicas':'CCB',
                                               'Centro de Comunicação e Expressão':'CCE',
                                               'Centro de Ciências da Saúde':'CCS',
                                               'Centro de Ciências Jurídicas':'CCJ',
                                               'Centro de Desportos':'CDS',
                                               'Centro de Ciências da Educação':'CED',
                                               'Centro de Filosofia e Ciências Humanas':'CFH',
                                               'Centro de Ciências Físicas e Matemáticas':'CFM',
                                               'Centro Socioeconômico':'CSE',
                                               'Centro Tecnológico':'CTC'},
                                        'JOI':{'Centro Tecnológico de Joinville':'CTJ'},
                                        'CUR':{'Centro de Ciências Rurais':'CCR'},
                                        'BNU':{'Centro Tecnológico, de Ciências exatas e Educação':'CTE'},
                                        'ARA':{'Centro de Ciências, Tecnologias e Saúde':'CTS'}}

def format_cursos(curso : str) -> str:
    return format_text(curso).replace('(acadêmico)','').replace('(profissional)','').strip().upper()

# # def get_centros(areas : list[str],campus : list[str]) -> list[str]:
#     centros = []
#     for area,campi in zip(areas,campus):
#         if campi == 'FLN':
#             if area in ['Sociais Aplicadas']:
#                 centros.append('CSE')
#             elif area in ['Humanas']:
#                 centros.append('CFH')
#             elif area in ['Agrárias']:
#                 centros.append('CCA')
#             elif area in ['Saúde','Ciências da Saúde']:
#                 centros.append('CCS')
#             elif area in ['Biológicas']:
#                 centros.append('CCB')
#             elif area in ['Exatas e da Terra','Engenharias']:
#                 centros.append('CTC')
#             elif area in ['Linguística, Letras e Artes']:
#                 centros.append('CCE')
#             elif area in ['Multidisciplinar']:
#                 centros.append('Multidisciplinar')
#             else:
#                 centros.append('')
        
#         elif campi == 'CUR':
#             # if area in ['Medicina Veterinária']:
#             #     centros.append('CCR')
#             # elif area in ['Multidisciplinar']:
#             #     centros.append('Multidisciplinar')
#             # else:
#             #     centros.append('')
#             centros.append('CCR') # Curitibanos só tem um centro
        
#         elif campi == 'BNU':
#             # if area in ['Exatas e da Terra','Engenharias']:
#             #     centros.append('CTE')
#             # elif area in ['Multidisciplinar']:
#             #     centros.append('Multidisciplinar')
#             # else:
#             #     centros.append('')
#             centros.append('CTE') # Blumenau só tem um centro

#         elif campi == 'ARA':
#             centros.append('CTS') # Araranguá só tem um centro

#         elif campi == 'JOI':
#             centros.append('CTJ') # Joinville só tem um centro
        
#         else:
#             centros.append('')
#     return centros

def get_centros(cursos : list[str],
                campus : list[str]) -> list[str]:
    centros = []
    for curso,campi in zip(cursos,campus):
        if curso.strip() and campi.strip():
            try:
                centro = DIC_CAMPUS_CURSOS_CENTROS_SIGLAS[campi][curso]                
            except Exception as e:
                centros.append('')
            else:
                centros.append(centro)
        else:
            centros.append('')
    return centros

def format_campus(campus : str) -> str:
    if 'Florianópolis' in campus:
        return 'FLN'
    elif 'Blumenau' in campus:
        return 'BNU'
    elif 'Curitibanos' in campus:
        return 'CUR'
    elif 'Joinville' in campus:
        return 'JOI'
    elif 'Araranguá' in campus:
        return 'ARA'
    return ''

def insert_centro(df : pd.DataFrame) -> pd.DataFrame:
    df['CENTRO'] = get_centros(cursos=df['CURSO'].to_list(),
                               campus=df['CAMPUS'].to_list())
    return df

