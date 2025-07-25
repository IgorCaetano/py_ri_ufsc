import pandas as pd
import random

# from typing import Any
from . .etl.extraction.courses_info import CursosUFSC
# from . .common.for_strings import format_text
from . .etl.transform_and_load.utils import (
    insert_gender_by_name_into_df,insert_location_into_df,
    get_curso_from_description,get_curso_from_full_location,
    insert_type_course_based_on_type_into_df,insert_type_curso_based_on_description_into_df,
    insert_campus_from_description_into_df,get_list_of_centro_from_campus,
    get_list_of_centro_from_description, insert_centro_into_df,adjust_campus_from_centro
)
from .filters import (
    filter_types,filter_dates,filter_title_by_words,filter_subjects,
    filter_authors,filter_advisors,filter_gender,filter_language,
    filter_course,filter_type_course,filter_centro,filter_campus
)
# from . .ui_graphs import (
#     plot_gender_pie,plot_language_pie,plot_line_by_year,plot_line_by_year_and_gender,
#     plot_top_courses_by_year_and_subject,plot_top_subjects
# )


DIC_USE_YEARS = {"use":True,"values":list(range(1960,2025+1))+['']}
DIC_USE_AUTHORS = {"use":True,"values":["Silva, João", "Oliveira, Maria", "Souza, Ana", "Ferreira, Pedro",
                                        "Costa, Luana D. da", "Santos, Bruno F. dos", "Lima, Paula", "Almeida, Diego"]}
DIC_USE_ADVISORS = {"use":True,"values":['',"Pereira, Marcos A.", "Mendes, Juliana A. Souza de", "Barbosa, Carla", "Rocha, Felipe Júnior"]}
DIC_USE_GENDERS = {"use":True,"values":['F','M','F,M','']}
DIC_USE_TITLES = {"use":True,"values":['',"Análise de dados educacionais", "Estudo sobre inteligência artificial",
                                        "Impacto da pandemia na saúde pública", "Gestão financeira em pequenas empresas",
                                        "Direitos humanos e constituição", "Uso de energias renováveis",
                                        "Tecnologias assistivas na educação", "Aspectos legais da telemedicina",
                                        "Controle de qualidade em laboratórios", "Sustentabilidade na construção civil"]}
DIC_USE_COURSES = {"use":True,"values":['',"Engenharia Elétrica", "Administração", "Medicina", "Direito", "Pedagogia"]}
DIC_USE_TYPE_COURSES = {"use":True,"values":['','POS','GRAD']}
DIC_USE_TYPES = {"use":True,"values":['DISSERTAÇÃO MESTRADO','NÃO ESPECIFICADO','TCC','MONOGRAFIA','ARTIGO',
 'BOOK','OUTROS','TESE DOUTORADO','ARCHIVAL COLLECTION','VIDEO','SOUND',
 'DISSERTAÇÃO MESTRADO PROFISSIONAL','RELATÓRIO','CONFERENCE PROCEEDINGS','TESE DOUTORADO PROFISSIONAL',
 'CAP. DE LIVRO', 'TESE LIVRE DOCÊNCIA', 'WORKING PAPER','TCCP ESPECIALIZAÇÃO', 'RELATORIO PÓS-DOUTORADO', 'LIVRO', 'TESE', 'DISSERTAÇÃO',
 'RELATÓRIO ESTÁGIO EXTR', 'PLANILHA', 'TRABALHO CIENT.', 'TRANSCRIPTION', 'MAGAZINE ARTICLE', 'PORTARIA/CCB/2013', 'OFICIAL',
 'TESE MESTRADO', 'REVISTA', 'DISSERTAÇÃO DOUTORADO','ANAIS', 'DOSSIE','E-BOOK', 'RELATÓRIO TÉCNICO', 'PLANO_DE_AULA', 'DOCUMENTO',
 'PROJETO DE PESQUISA', 'TESE;DISSERTAÇÃO','APRESENTAÇÃO','RELATÓRIO TÉCNICO MESTRADO PROFISSIONAL']}
DIC_USE_DESCRIPTIONS = {"use":True,"values":['Dissertação (mestrado) - Universidade Federal de Santa Catarina, Centro Sócio Econômico, Programa de Pós-Graduação em Economia, Florianópolis, 2018.',
                        '',
                        'TCC (graduação) - Universidade Federal de Santa Catarina, Campus Curitibanos, Engenharia Florestal.',
                        'Dissertação (mestrado) - Universidade Federal de Santa Catarina, Centro de Filosofia e Ciências Humanas, Programa de Pós-Graduação em Antropologia Social, Florianópolis, 2013',
                        'Dissertação (mestrado) - Universidade Federal de Santa Catarina, Centro de Ciências Biológicas.',
                        'TCC Engenharia Civil de Infraestrutura - Universidade Federal de Santa Catarina. Campus Joinville. Engenharia de Infraestrutura.',
                        'Dissertação (mestrado) - Universidade Federal de Santa Catarina, Campus Joinville, Programa de Pós-Graduação em Engenharia e Ciências Mecânicas, Joinville, 2018.',
                        'Dissertação (mestrado profissional) - Universidade Federal de Santa Catarina, Campus Blumenau, Programa de Pós-Graduação em Matemática, Blumenau, 2023.',
                        'TCC(graduação) - Universidade Federal de Santa Catarina. Campus Curitibanos. Medicina Veterinária.',
                        'TCC (graduação) - Universidade Federal de Santa Catarina. Campus Joinville. Engenharia de Transportes e Logística.',
                        'TCC (graduação) - Universidade Federal de Santa Catarina. Campus Blumenau. Engenharia de Materiais',
                        'TCC(graduação) - Universidade Federal de Santa Catarina. Campus Curitibanos. Engenharia Florestal.',
                        'E-book confeccionado a partir das vivências do projeto de extensão/pesquisa "Desenvolv-Ninos: estimulando o desenvolvimento dos pequeninos" da Universidade Federal de Santa Catarina- Campus Araranguá.',
                        'TCC (graduação) - Universidade Federal de Santa Catarina, Campus Joinville, Engenharia Mecatrônica.',
                        'TCC (graduação) - Universidade Federal de Santa Catarina. Campus Joinville. Engenharia Naval.',
                        'TCC (graduação) - Universidade Federal de Santa Catarina. Campus Joinville. Engenharia de Infraestrutura.',
                        'Este livro possui dimensões 220mm x150mm, com 180 páginas encadernadas,costurado. O exemplar original pertence ao acervo do Laboratório de Estudos e Pesquisa Científica (LEPAC), da Universidade Federal da Paraíba – Campus I – João Pessoa/PB',
                        'TCC (graduação) - Universidade Federal de Santa Catarina. Centro de Ciências Rurais. Campus de Curitibanos. Agronomia.',
                        'TCC (graduação) - Universidade Federal de Santa Catarina. Campus Joinville. Engenharia Automotiva.',
                        'TCC (graduação) - Universidade Federal de Santa Catarina, Campus Blumenau, Engenharia de Controle e Automação.',
                        'TCC (graduação) - Universidade Federal de Santa Catarina. Campus Araranguá. Tecnologias da informação e comunicação',
                        'TCC (graduação) - Universidade Federal de Santa Catarina, Campus Curitibanos, Medicina Veterinária.',
                        'Os documentos encontram-se alocados no Arquivo e Memória Institucional (ARQMI) do Centro Federal de Educação Tecnológica de Minas Gerais - Campus I. Para mais informações acessar o endereço: https://www.arquivo.cefetmg.br/informacoes-gerais-oarqmi/ \n\nTambém, informações a respeito do documento encontram-se disponíveis no documento Fundo Escola de Aprendizes Artífices de Minas Gerais, que corresponde a um inventário de documentos oficiais relacionados à escola https://www.arquivo.cefetmg.br/wp-content/uploads/sites/104/2021/04/INVENTARIO-Fundo-1-compactado-1.pdf',
                        'Dissertação (mestrado profissional) - Universidade Federal de Santa Catarina, Campus Blumenau, Programa de Pós-Graduação em Nanociência, Processos e Materiais Avançados, Blumenau, 2022.',
                        'Dissertação (mestrado) - Universidade Federal de Santa Catarina, Campus Araranguá, Programa de Pós-Graduação em Energia e Sustentabilidade, Araranguá, 2021.',
                        'Este livro possui dimensões 185mm x135mm, com 369 páginas encadernadas costuradas. O exemplar original pertence ao  acervo do Laboratório de Estudos e Pesquisa Científica (LEPAC),  da Universidade Federal da Paraíba – Campus I – João Pessoa/PB',
                        'TCC (graduação)- Universidade Federal de Santa Catarina. Campus Curitibanos. Agronomia.',
                        'TCC (graduação) - Universidade Federal de Santa Catarina, Campus Joinville, Engenharia Naval.',
                        'TCC (graduação) - Universidade Federal de Santa Catarina, Campus Joinville, Engenharia Aeroespacial',
                        '',
                        'Dissertação (mestrado) - Universidade Federal de Santa Catarina, Centro de Filosofia e Ciências Humanas, Programa de Pós-Graduação em Antropologia Social, Florianópolis, 2013',
                        'Dissertação (mestrado) - Universidade Federal de Santa Catarina, Centro de Ciências Biológicas.',
                        'TCC (graduação) - Universidade Federal de Santa Catarina. Centro Tecnológico. Arquitetura',
                        'TCC (graduação) - Universidade Federal de Santa Catarina, Centro Tecnológico, Engenharia de Materiais.',
                        'Dissertação (mestrado) - Universidade Federal de Santa Catarina, Centro de Ciências da Saúde, Programa de Pós-Graduação em Saúde Coletiva, Florianópolis, 2013.',
                        'TCC(especialização) - Universidade Federal de Santa Catarina. Centro de Ciências da Saúde. Programa de Pós-graduação em Enfermagem. Linhas de Cuidado em Atenção Psicossocial',
                        'Este artigo encontra-se disponível no seguinte link: https://bell.unochapeco.edu.br/revistas/index.php/pedagogica/article/view/6872',
                        'Referente concessão de adicional de insalubridade a Cilene Lino de Oliveira.',
                        'TCC (graduação) - Universidade Federal de Santa Catarina, Campus Curitibanos, Engenharia Florestal.',
                        'TCC(graduação) - Universidade Federal de Santa Catarina. Centro Tecnológico. Engenharia de Controle e Automação.',
                        'Livro com 272 páginas. Disponível no seguinte link: https://gallica.bnf.fr/ark:/12148/bpt6k6549736b?rk=42918;4',
                        'Este arquivo encontra-se disponível fisicamente no acervo da Câmara Municipal de Ipiaú-BA.',
                        'TCC(graduação) - Universidade Federal de Santa Catarina.  Centro de Comunicação e Expressão. Design.',
                        'TCC (graduação) - Universidade Federal de Santa Catarina, Centro Sócio Econômico, Curso de Administração.',
                        "Organizado por Amassuru, el libro cuenta con el apoyo del Data + Feminism Lab (MIT), Women's and Gender Studies (MIT), el proyecto Datos Contra el Feminicidio, el Núcleo de Estudos de Gênero na Política Externa e Internacional (UFSC) y FES Colombia.",
                        'TCC(especialização) - Universidade Federal de Santa Catarina. Centro de Ciências da Educação. Departamento de Metodologia de Ensino. Educação na Cultura Digital.',
                        'TCC (graduação) - Universidade Federal de Santa Catarina. Centro Ciências Físicas e Matemáticas. Oceanografia',
                        'TCC(graduação) - Universidade Federal de Santa Catarina. Centro Tecnológico. Engenharia Sanitária e Ambiental.',
                        'TCC(Graduação) - Universidade Federal de Santa Catarina. Centro de Ciências da Saúde. Medicina.',
                        'Dissertação (mestrado) - Universidade Federal de Santa Catarina, Centro de Filosofia e Ciências Humanas. Programa de Pós-Graduação em Sociologia Política.',
                        'TCC (graduação) - Universidade Federal de Santa Catarina, Centro Sócio Econômico, Curso de Serviço Social.',
                        'Tese (doutorado) - Universidade Federal de Santa Catarina, Centro de Ciências Biológicas, Programa de Pós-Graduação em Neurociências, Florianópolis, 2018.',
                        '']}
DIC_USE_SUBJECTS = {"use":True,"values":["educação;tecnologia", "inteligência artificial;aprendizado de máquina",
                                        "saúde pública;covid-19", "finanças;empreendedorismo",
                                        "direitos humanos;constituição", "meio ambiente;sustentabilidade",
                                        "acessibilidade;inclusão", "tecnologia;medicina",
                                        "qualidade;ciência", "engenharia;sustentabilidade"]}
DIC_USE_SETSPECS = {"use":True,"values":['col_123456789_170541', 'col_123456789_79531', 'col_123456789_856', 'col_123456789_75030', 'col_123456789_140034', 'col_123456789_82371', 'col_123456789_7443', 'col_123456789_7448',
                                        'col_123456789_133779', 'col_123456789_154090', 'col_123456789_93473', 'col_123456789_163293', 'col_123456789_162909', 'col_123456789_7436', 'col_123456789_116633', 'col_123456789_231924',
                                        'col_123456789_156547', 'col_123456789_99518', 'col_123456789_100436', 'col_123456789_7447', 'col_123456789_1772', 'col_123456789_138303', 'col_123456789_234336', 'col_123456789_98963',
                                        'col_123456789_7515', 'col_123456789_112819', 'col_123456789_195580', 'col_123456789_154949', 'col_123456789_7480', 'col_123456789_182374', 'col_123456789_263527', 'col_123456789_166330',
                                        'col_123456789_126454', 'col_123456789_7493', 'col_123456789_124305', 'col_123456789_7439', 'col_123456789_75127', 'col_123456789_7483', 'col_123456789_81311', 'col_123456789_135862',
                                        'col_123456789_231692', 'col_123456789_174124', 'col_123456789_74648', 'col_123456789_214164', 'col_123456789_140254', 'col_123456789_138780', 'col_123456789_162913', 'col_123456789_153754',
                                        'col_123456789_252492',  'col_123456789_172197', 'col_123456789_201413',  'col_123456789_103512', 'col_123456789_114969', 'col_123456789_122482', 'col_123456789_195787', 'col_123456789_204789',
                                        'col_123456789_183391', 'col_123456789_242001', 'col_123456789_240457', 'col_123456789_220094','col_123456789_164995', 'col_123456789_170165', 'col_123456789_155827', 'col_123456789_221862',
                                        'col_123456789_163385', 'col_123456789_140878', 'col_123456789_1856','col_123456789_193039', 'col_123456789_105306','col_123456789_1671', 'col_123456789_147199', 'col_123456789_78570',
                                        'col_123456789_104649', 'col_123456789_182067', 'col_123456789_143920', 'col_123456789_249470', 'col_123456789_175009', 'col_123456789_231544', 'col_123456789_178873', 'col_123456789_116498',
                                        'col_123456789_202700', 'col_123456789_184908', 'col_123456789_7446', 'col_123456789_154478', 'col_123456789_181886', 'col_123456789_152387', 'col_123456789_212',
                                        'col_123456789_7445', 'col_123456789_167525', 'col_123456789_126469', 'col_123456789_142102', 'col_123456789_178045', 'col_123456789_141302', 'col_123456789_230024',
                                        'col_123456789_200694', 'col_123456789_257112', 'col_123456789_74758', 'col_123456789_257093', 'col_123456789_1204', 'col_123456789_139094', 'col_123456789_104475', 'col_123456789_160253',
                                        'col_123456789_196575', 'col_123456789_170112', 'col_123456789_152618', 'col_123456789_139925', 'col_123456789_133398', 'col_123456789_234158', 'col_123456789_182674',
                                        'col_123456789_126560', 'col_123456789_98965', 'col_123456789_238254', 'col_123456789_158993', 'col_123456789_7441', 'col_123456789_143294', 'col_123456789_137525',
                                        'col_123456789_155672', 'col_123456789_263150', 'col_123456789_194415', 'col_123456789_156387', 'col_123456789_163273', 'col_123456789_244944', 'col_123456789_259520',
                                        'col_123456789_209487', 'col_123456789_231920', 'col_123456789_169994', 'col_123456789_188618', 'col_123456789_183731', 'col_123456789_261024', 'col_123456789_195245',
                                        'col_123456789_141695', 'col_123456789_249427', 'col_123456789_123321', 'col_123456789_175746', 'col_123456789_158966', 'col_123456789_160304']}
DIC_USE_FULL_LOCATIONS = {"use":True,"values":['',"Acervos -> Campus Florianópolis -> CED (Centro de Ciências da Educação) -> História da Educação Matemática (l'Histoire de l'éducation mathématique) -> _Documentos Oficiais e Normativos....- BA",
 'Trabalhos Acadêmicos -> Trabalhos de Conclusão de Curso de Graduação -> TCC Design',
 'Acervos -> Campus Florianópolis -> CSE (Centro Socioeconômico) -> INPEAU (Instituto de Pesquisas e Estudos em Administração Universitária) -> Anais dos Colóquios Internacionais sobre Gestão Universitária -> XIII Colóquio Internacional sobre Gestão Universitária nas Américas',
 'Acervos -> Campus Florianópolis -> CFH (Centro de Filosofia e Ciências Humanas) -> Programa de Pós-Graduação em Antropologia Social da UFSC (PPGAS) -> Portarias',
  'Acervos -> Campus Florianópolis -> PROPESQ (Pró-Reitoria de Pesquisa) -> Programa de Iniciação Científica e Tecnológica da UFSC -> Seminário de Iniciação Científica e Tecnológica da UFSC -> 2021 -> Iniciação Científica - PIBIC e Programa Voluntário -> Ciências Exatas, da Terra e Engenharias -> Araranguá - Departamento de Computação (DEC)',
 'Trabalhos Acadêmicos -> Trabalhos de Conclusão de Curso de Graduação -> TCC Administração',
 'Acervos -> Campus Joinville -> Pós-Graduação Joinville -> Programa de Pós-Graduação em Engenharia e Ciências Mecânicas (Pós-ECM) -> Portarias (Pós-ECM) -> Coordenação -> Portarias 2018',
 'Acervos -> Campus Florianópolis -> CSE (Centro Socioeconômico) -> Departamento de Economia e Relações Internacionais -> Publicações técnico-científicas -> Livros',
 'Trabalhos Acadêmicos -> Trabalhos de Conclusão de Curso de Especialização -> Centro de Ciências da Educação (CED) -> TCC Especialização - Educação na Cultura Digital',
 'Acervos -> Campus Florianópolis -> PROPLAN (Pró-Reitoria de Planejamento) -> Departamento de Planejamento e Gestão da Informação - DPGI -> Cursos de Graduação',
 'Trabalhos Acadêmicos -> Trabalhos de Conclusão de Curso de Graduação -> TCC Oceanografia',
 'Trabalhos Acadêmicos -> Trabalhos de Conclusão de Curso de Graduação -> TCC Engenharia Sanitária e Ambiental',
 'Trabalhos Acadêmicos -> Trabalhos de Conclusão de Curso de Graduação -> TCC Medicina',
 'Teses e Dissertações -> Programa de Pós-Graduação em Sociologia Política',
 'Trabalhos Acadêmicos -> Trabalhos de Conclusão de Curso de Graduação -> TCC Serviço Social',
 'Teses e Dissertações -> Programa de Pós-Graduação em Neurociências',
 'Acervos -> Campus Florianópolis -> CSE (Centro Socioeconômico) -> INPEAU (Instituto de Pesquisas e Estudos em Administração Universitária) -> Anais dos Colóquios Internacionais sobre Gestão Universitária -> XV Colóquio Internacional de Gestão Universitária',
 'Acervos -> Campus Florianópolis -> CCE (Centro de Comunicação e Expressão) -> Secretaria do Centro de Comunicação e Expressão - CCE -> Portarias (CCE) -> Portarias (CCE) - 2004',
 'Teses e Dissertações -> Programa de Pós-Graduação em Ensino de Física (Mestrado Profissional)',
 'Teses e Dissertações -> Teses e dissertações do Centro Tecnológico',
 'Teses e Dissertações -> Programa de Pós-Graduação em Educação',
 'Trabalhos Acadêmicos -> Trabalhos de Conclusão de Curso de Graduação -> TCC Ciências Biológicas',
 'Acervos -> Campus Araranguá -> Centro de Ciências, Tecnologias e Saúde (CTS) do Campus Araranguá -> Departamento de Ciências da Saúde (DCS) -> Publicações técnico-científicas (DCS)',
 'Trabalhos Acadêmicos -> Trabalhos de Conclusão de Curso de Especialização -> Multidisciplinar -> TCC Especialização - Curso de Especialização em Permacultura',
 '',
 'Teses e Dissertações -> Programa de Pós-Graduação em Aquicultura',
 'Acervos -> Campus Florianópolis -> CED (Centro de Ciências da Educação) -> Coordenadoria de Apoio Administrativo -> Atos administrativos -> Portarias -> 2016',
 'Acervos -> Campus Florianópolis -> CCS (Centro de Ciências da Saúde) -> Departamento de Saúde Pública -> Telessaúde SC -> Telessaúde SC (vídeos)',
 'Teses e Dissertações -> Programa de Pós-Graduação em Engenharia de Produção',
 'Acervos -> Campus Florianópolis -> CSE (Centro Socioeconômico) -> INPEAU (Instituto de Pesquisas e Estudos em Administração Universitária) -> Anais dos Colóquios Internacionais sobre Gestão Universitária -> XIX Colóquio Internacional de Gestão Universitária',
 'Acervos -> Campus Florianópolis -> PROPESQ (Pró-Reitoria de Pesquisa) -> Programa de Iniciação Científica e Tecnológica da UFSC -> Seminário de Iniciação Científica e Tecnológica da UFSC -> 2022 -> Iniciação Científica - PIBIC e Programa Voluntário -> Ciências Exatas, da Terra e Engenharias -> Departamento de Engenharia Civil',
 'Trabalhos Acadêmicos -> Trabalhos de Conclusão de Curso de Graduação -> TCC Jornalismo',
 'Acervos -> Campus Florianópolis -> CSE (Centro Socioeconômico) -> Secretaria Administrativa do CSE -> Portarias CSE -> Portarias CSE 2023',
 'Teses e Dissertações -> Programa de Pós-Graduação em História',
 'Acervos -> Campus Florianópolis -> PROPESQ (Pró-Reitoria de Pesquisa) -> Programa de Iniciação Científica e Tecnológica da UFSC -> Divulgação Científica para a Comunidade -> Ciências da Vida -> Ciências da Vida (Vídeos)',
 'Acervos -> Campus Florianópolis -> Grupos e Núcleos Interdisciplinares -> Virtuhab/Labrestauro/MATEC -> MIX SUSTENTÁVEL -> Mix Sustentável',
 "Acervos -> Campus Florianópolis -> CED (Centro de Ciências da Educação) -> História da Educação Matemática (l'Histoire de l'éducation mathématique) -> CADERNOS ESCOLARES",
  'Acervos -> Campus Florianópolis -> PROPESQ (Pró-Reitoria de Pesquisa) -> Programa de Iniciação Científica e Tecnológica da UFSC -> Seminário de Iniciação Científica e Tecnológica da UFSC -> 2021 -> Iniciação Científica - PIBIC e Programa Voluntário -> Ciências Exatas, da Terra e Engenharias -> Araranguá - Departamento de Computação (DEC)',
 'Teses e Dissertações -> Teses e dissertações do Centro Sócio-Econômico',
 'Acervos -> Campus Florianópolis -> Biblioteca Universitária -> Materiais Iconográficos -> Tempo Editorial -> 600 Tecnologia (Ciências Aplicadas) -> Forte de Santo Antônio de Ratones',
 'Teses e Dissertações -> Programa de Pós-Graduação em Farmácia',
 'Acervos -> Campus Florianópolis -> CCE (Centro de Comunicação e Expressão) -> Jornalismo -> Rádio Ponto -> Acervo -> Radiojornalismo',
 'Trabalhos Acadêmicos -> Trabalhos de Conclusão de Curso de Graduação -> TCC Ciências Contábeis']}
DIC_USE_CAMPUS = {"use":True,"values":['','FLN','JOI','BNU','ARA','CUR']}
DIC_USE_CENTROS = {"use":True,"values":['','CCA','CCB','CCE','CCS','CCJ',
                                         'CDS','CED','CFH','CFM','CSE',
                                         'CTC','CTJ','CCR','CTE','CTS']}
DIC_USE_LANGUAGES = {"use":True,"values":['por','spa','fra','ita','eng','']}

def generate_mock_df(lines_amount : int = 10,
                     years : dict = {"use":False,"values":[]},
                     authors : dict = {"use":False,"values":[]},
                     advisors : dict = {"use":False,"values":[]},
                     titles : dict = {"use":False,"values":[]},
                     courses : dict = {"use":False,"values":[]},
                     type_courses : dict = {"use":False,"values":[]},
                     types : dict = {"use":False,"values":[]},
                     subjects : dict = {"use":False,"values":[]},
                     descriptions : dict = {"use":False,"values":[]},
                     setSpecs : dict = {"use":False,"values":[],},
                     full_locations : dict = {"use":False,"valeus":[]},
                     campus : dict = {"use":False,"values":[]},
                     centros : dict = {"use":False,"values":[]},
                     genders : dict = {"use":False,"values":[]},
                     languages : dict = {"use":False,"values":[]}
        ) -> pd.DataFrame:
    data = []
    for _ in range(lines_amount):
        row = {}

        # Year
        if years.get("use", False) and years.get("values"):
            row["year"] = random.choice(years['values'])
        # else:
        #     row["year"] = ""

        # setSpec
        if setSpecs.get("use", False) and setSpecs.get("values"):
            row["setSpec"] = random.choice(setSpecs['values'])

        # full_location
        if full_locations.get("use", False) and full_locations.get("values"):
            row["full_locations"] = random.choice(full_locations['values'])
        
        # campus
        if campus.get("use", False) and campus.get("values"):
            row["campus"] = random.choice(campus['values'])

        # centros
        if centros.get("use", False) and centros.get("values"):
            row["centro"] = random.choice(centros['values'])

        # genders
        if genders.get("use", False) and genders.get("values"):
            row["gender_name"] = random.choice(genders['values'])

        # languages
        if languages.get("use", False) and languages.get("values"):
            row["language"] = random.choice(languages['values'])

        # Title
        if titles.get("use", False) and titles.get("values"):
            row["title"] = random.choice(titles["values"])
        # else:
        #     row["title"] = ""

        # Subjects - seleciona de 2 a 5 assuntos aleatórios e junta com ';'
        if subjects.get("use", False) and subjects.get("values"):
            # Quebra todos os assuntos existentes por ';' e extrai os termos individuais
            all_subject_terms = list(set(
                s.strip()
                for val in subjects["values"]
                for s in val.split(";")
            ))
            # Sorteia de 2 a 5 termos e junta com ';'
            selected_subjects = random.sample(all_subject_terms, k=random.randint(2, 5))
            row["subjects"] = ";".join(selected_subjects)
        # else:
        #     row["subjects"] = ""

        # Descriptions
        if descriptions.get("use", False) and descriptions.get("values"):
            row["description"] = random.choice(descriptions["values"])
        # else:
        #     row["description"] = ""

        # Authors
        if authors.get("use", False) and authors.get("values"):
            row["authors"] = ";".join(random.sample(authors["values"], k=random.randint(1, 5 if len(authors["values"]) >= 5 else len(authors["values"]))))
        # else:
        #     row["authors"] = ""

        # Advisors
        if advisors.get("use", False) and advisors.get("values"):
            num_advisors = random.choices([1, 2], weights=[0.75, 0.25])[0]  # 75% chance de 1, 25% de 2
            row["advisors"] = ";".join(random.sample(advisors["values"], k=num_advisors))
        # else:
        #     row["advisors"] = ""

        # Course
        if courses.get("use", False) and courses.get("values"):
            row["course"] = random.choice(courses["values"])
        # else:
        #     row["course"] = ""

        # Type
        if types.get("use", False) and types.get("values"):
            row["type"] = random.choice(types["values"])
        # else:
        #     row["type"] = ""

        # Type Course (extra, opcional)
        if type_courses.get("use", False) and type_courses.get("values"):
            row["type_course"] = random.choice(type_courses["values"])
        # else:
        #     row["type_course"] = ""

        data.append(row)

    return pd.DataFrame(data)

# def add_value_counts(df: pd.DataFrame, column: str, 
#                      drop_duplicates: bool = True, 
#                      sort_descending: bool = True) -> pd.DataFrame:
#     """
#     Adiciona uma coluna 'count' ao DataFrame com a contagem de ocorrências dos valores da coluna especificada.

#     Parâmetros:
#     - df: DataFrame de entrada
#     - column: Nome da coluna a ser analisada
#     - drop_duplicates: Se True, retorna apenas uma linha por valor único da coluna analisada
#     - sort_descending: Se True, ordena o DataFrame pela contagem em ordem decrescente

#     Retorna:
#     - Um novo DataFrame com a coluna 'count' adicionada
#     """
#     df_copy = df.copy()
#     df_copy['count'] = df_copy.groupby(column)[column].transform('count')

#     if drop_duplicates:
#         df_copy = df_copy[[column, 'count']].drop_duplicates()

#     if sort_descending:
#         df_copy = df_copy.sort_values(by='count', ascending=False).reset_index(drop=True)

#     return df_copy

# STOPWORDS_PT = {
#     'de', 'da', 'do', 'das', 'dos', 'e', 'a', 'o', 'as', 'os',
#     'em', 'para', 'com', 'por', 'na', 'no', 'nas', 'nos',
#     'um', 'uma', 'uns', 'umas', 'sobre', 'entre', 'ao', 'aos',
#     'sim','não'
# }

# STOPWORDS_UFSC = [format_text(item,special_treatment=True) for item in DIC_USE_COURSES['values']] + \
# ['ufsc','universidade_federal_de_santa_catarina','santa_catarina','clipping'] # clipping é para imagens, a priori, da própria universidade

class TestRIUFSC():
    def __init__(self,
                 df : pd.DataFrame|None = None):
        self.df = df
        self.ufsc_courses = CursosUFSC().get_cursos()
    
    ####### Testes para ETL (etapa de Transformação - enriquecimento dos dados com novas colunas) ############################

    def test_gender_by_name(self,
                            df : pd.DataFrame|None = None,
                            mock_df_lines_amount : int = 10,
                            mock_authors : dict = DIC_USE_AUTHORS) -> pd.DataFrame:
        if (df is not None) and isinstance(df,pd.DataFrame):
            if 'authors' not in df.keys():
                raise KeyError('Necessário coluna "authors" no dataframe passado como parâmetro')
            return insert_gender_by_name_into_df(df)
        elif self.df is not None and isinstance(self.df,pd.DataFrame):
            if 'authors' not in self.df.keys():
                raise KeyError('Necessário coluna "authors" no dataframe passado como parâmetro')
            return insert_gender_by_name_into_df(self.df)
        else:
            return insert_gender_by_name_into_df(generate_mock_df(lines_amount=mock_df_lines_amount,
                                                                  authors=mock_authors))
    
    def test_insert_location_by_setspec(self,
                                        df : pd.DataFrame|None = None,
                                        mock_df_lines_amount : int = 10,
                                        mock_setSpecs : dict = DIC_USE_SETSPECS) -> pd.DataFrame:
        if (df is not None) and isinstance(df,pd.DataFrame):
            if 'setSpec' not in df.keys():
                raise KeyError('Necessário coluna "setSpec" no dataframe passado como parâmetro')
            return insert_location_into_df(df)
        elif self.df is not None and isinstance(self.df,pd.DataFrame):
            if 'setSpec' not in self.df.keys():
                raise KeyError('Necessário coluna "setSpec" no dataframe passado como parâmetro')
            return insert_location_into_df(self.df)
        else:
            return insert_location_into_df(generate_mock_df(lines_amount=mock_df_lines_amount,
                                                            setSpecs=mock_setSpecs))
        
    def test_insert_course(self,
                           df : pd.DataFrame|None = None,
                           mock_df_lines_amount : int = 10,
                           mock_setSpecs : dict = DIC_USE_SETSPECS) -> pd.DataFrame:
        if (df is not None) and isinstance(df,pd.DataFrame):
            return insert_location_into_df(df)
        elif self.df is not None and isinstance(self.df,pd.DataFrame):
            return insert_location_into_df(self.df)
        else:
            return insert_location_into_df(generate_mock_df(lines_amount=mock_df_lines_amount,
                                                            setSpecs=mock_setSpecs))
        
    def test_get_course_from_description(self,
                                         df : pd.DataFrame|None = None,
                                         mock_df_lines_amount : int = 10,
                                         mock_descriptions : dict = DIC_USE_DESCRIPTIONS,
                                         return_list : bool = False) -> pd.DataFrame|list[str]:
        
        if (df is not None) and isinstance(df,pd.DataFrame):
            if 'description' not in df.keys():
                raise KeyError('Necessário coluna "description" no dataframe passado como parâmetro')
            descriptions = df['description'].to_list()
        elif self.df is not None and isinstance(self.df,pd.DataFrame):
            if 'description' not in self.df.keys():
                raise KeyError('Necessário coluna "description" no dataframe passado como parâmetro')
            descriptions = self.df['description'].to_list()
        else:
            descriptions = generate_mock_df(lines_amount=mock_df_lines_amount,
                                            descriptions=mock_descriptions)['description'].to_list()
        courses = [get_curso_from_description(description=desc,
                                              courses=self.ufsc_courses) for desc in descriptions]
        if not return_list:
            return pd.DataFrame({'description':descriptions,'course':courses})
        else:
            return courses
    
    def test_get_course_from_full_location(self,
                                           df : pd.DataFrame|None = None,
                                           mock_df_lines_amount : int = 10,
                                           mock_full_locations : dict = DIC_USE_FULL_LOCATIONS,
                                           return_list : bool = False) -> pd.DataFrame|list[str]:
        if (df is not None) and isinstance(df,pd.DataFrame):
            if 'full_locations' not in df.keys():
                raise KeyError('Necessário coluna "full_locations" no dataframe passado como parâmetro')
            full_locations = df['full_locations'].to_list()
        elif self.df is not None and isinstance(self.df,pd.DataFrame):
            if 'full_locations' not in self.df.keys():
                raise KeyError('Necessário coluna "full_locations" no dataframe passado como parâmetro')
            full_locations = self.df['full_locations'].to_list()
        else:
            full_locations = generate_mock_df(lines_amount=mock_df_lines_amount,
                                            full_locations=mock_full_locations)['full_locations'].to_list()
        courses = [get_curso_from_full_location(full_location=full_location,
                                              courses=self.ufsc_courses) for full_location in full_locations]
        if not return_list:
            return pd.DataFrame({'full_locations':full_locations,'course':courses})    
        else:
            return courses

    def test_insert_type_course_from_type(self,
                                          df : pd.DataFrame|None = None,
                                          mock_df_lines_amount : int = 10,
                                          mock_types : dict = DIC_USE_TYPES) -> pd.DataFrame:
        if (df is not None) and isinstance(df,pd.DataFrame):
            if 'type' not in df.keys():
                raise KeyError('Necessário coluna "type" no dataframe passado como parâmetro')
            return insert_type_course_based_on_type_into_df(df)
        elif self.df is not None and isinstance(self.df,pd.DataFrame):
            if 'type' not in self.df.keys():
                raise KeyError('Necessário coluna "type" no dataframe passado como parâmetro')
            return insert_type_course_based_on_type_into_df(self.df)
        else:
            return insert_type_course_based_on_type_into_df(generate_mock_df(lines_amount=mock_df_lines_amount,
                                                                             types=mock_types))

    def test_insert_type_course_from_description(self,
                                          df : pd.DataFrame|None = None,
                                          mock_df_lines_amount : int = 10,
                                          mock_descriptions : dict = DIC_USE_DESCRIPTIONS) -> pd.DataFrame:
        if (df is not None) and isinstance(df,pd.DataFrame):
            if 'description' not in df.keys():
                raise KeyError('Necessário coluna "description" no dataframe passado como parâmetro')
            return insert_type_curso_based_on_description_into_df(df)
        elif self.df is not None and isinstance(self.df,pd.DataFrame):
            return insert_type_curso_based_on_description_into_df(self.df)
        else:
            return insert_type_curso_based_on_description_into_df(generate_mock_df(lines_amount=mock_df_lines_amount,
                                                                                   descriptions=mock_descriptions))

    def test_insert_campus_into_df_from_description(self,
                                                    df : pd.DataFrame|None = None,
                                                    mock_df_lines_amount : int = 10,
                                                    mock_descriptions : dict = DIC_USE_DESCRIPTIONS) -> pd.DataFrame:
        if (df is not None) and isinstance(df,pd.DataFrame):
            if 'description' not in df.keys():
                raise KeyError('Necessário coluna "description" no dataframe passado como parâmetro')
            return insert_campus_from_description_into_df(df)
        elif self.df is not None and isinstance(self.df,pd.DataFrame):
            if 'description' not in self.df.keys():
                raise KeyError('Necessário coluna "description" no dataframe passado como parâmetro')
            return insert_campus_from_description_into_df(self.df)
        else:
            return insert_campus_from_description_into_df(generate_mock_df(lines_amount=mock_df_lines_amount,
                                                                           descriptions=mock_descriptions))

    def test_get_list_of_centro_from_campus(self,
                                            df : pd.DataFrame|None = None,
                                            mock_df_lines_amount : int = 10,
                                            mock_campus : dict = DIC_USE_CAMPUS,
                                            return_list : bool = False) -> pd.DataFrame|list[str]:
        if (df is not None) and isinstance(df,pd.DataFrame):
            if 'campus' not in df.keys():
                raise KeyError('Necessário coluna "campus" no dataframe passado como parâmetro')
            campus = df['campus'].to_list()
        elif self.df is not None and isinstance(self.df,pd.DataFrame):
            if 'campus' not in self.df.keys():
                raise KeyError('Necessário coluna "campus" no dataframe passado como parâmetro')
            campus = self.df['campus'].to_list()
        else:
            campus = generate_mock_df(lines_amount=mock_df_lines_amount,
                                      campus=mock_campus)['campus'].to_list()
        centros = get_list_of_centro_from_campus(list_centros=['' for c in campus],list_campus=campus)
        if not return_list:
            return pd.DataFrame({'campus':campus,'centro':centros})
        else:
            return centros

    def test_get_list_of_centro_from_description(self,
                                    df : pd.DataFrame|None = None,
                                    mock_df_lines_amount : int = 10,
                                    mock_descriptions : dict = DIC_USE_DESCRIPTIONS,
                                    return_list : bool = False) -> pd.DataFrame|list[str]:
        if (df is not None) and isinstance(df,pd.DataFrame):
            if 'description' not in df.keys():
                raise KeyError('Necessário coluna "description" no dataframe passado como parâmetro')
            descriptions = df['description'].to_list()
        elif self.df is not None and isinstance(self.df,pd.DataFrame):
            if 'description' not in self.df.keys():
                raise KeyError('Necessário coluna "description" no dataframe passado como parâmetro')
            descriptions = self.df['description'].to_list()
        else:
            descriptions = generate_mock_df(lines_amount=mock_df_lines_amount,
                                      descriptions=mock_descriptions)['description'].to_list()
        centros = get_list_of_centro_from_description(list_centros=['' for c in descriptions],list_descriptions=descriptions)
        if not return_list:
            return pd.DataFrame({'description':descriptions,'centro':centros})
        else:
            return centros

    def test_insert_centro_into_df(self,
                                   df : pd.DataFrame|None = None,
                                   mock_df_lines_amount : int = 10,
                                   mock_campus : dict = DIC_USE_CAMPUS,
                                   mock_descriptions : dict = DIC_USE_DESCRIPTIONS) -> pd.DataFrame:
        if (df is not None) and isinstance(df,pd.DataFrame):
            if 'description' not in df.keys():
                raise KeyError('Necessário coluna "description" no dataframe passado como parâmetro')
            if 'campus' not in df.keys():
                raise KeyError('Necessário coluna "campus" no dataframe passado como parâmetro')
            return insert_centro_into_df(df)
        elif self.df is not None and isinstance(self.df,pd.DataFrame):
            if 'description' not in self.df.keys():
                raise KeyError('Necessário coluna "description" no dataframe passado como parâmetro')
            if 'campus' not in self.df.keys():
                raise KeyError('Necessário coluna "campus" no dataframe passado como parâmetro')
            return insert_centro_into_df(self.df)
        else:
            return insert_centro_into_df(generate_mock_df(lines_amount=mock_df_lines_amount,
                                                          campus=mock_campus,
                                                          descriptions=mock_descriptions))

    def test_adjust_campus_from_centro(self,
                                       df : pd.DataFrame|None = None,
                                       mock_df_lines_amount : int = 10,
                                       mock_centros : dict = DIC_USE_CENTROS) -> pd.DataFrame:
        if (df is not None) and isinstance(df,pd.DataFrame):
            if 'centro' not in df.keys():
                raise KeyError('Necessário coluna "centro" no dataframe passado como parâmetro')
            if 'campus' not in df.keys():
                raise KeyError('Necessário coluna "campus" no dataframe passado como parâmetro')
            return adjust_campus_from_centro(df)
        elif self.df is not None and isinstance(self.df,pd.DataFrame):
            if 'centro' not in self.df.keys():
                raise KeyError('Necessário coluna "centro" no dataframe passado como parâmetro')
            if 'campus' not in self.df.keys():
                raise KeyError('Necessário coluna "campus" no dataframe passado como parâmetro')
            return adjust_campus_from_centro(self.df)
        else:
            return adjust_campus_from_centro(generate_mock_df(lines_amount=mock_df_lines_amount,
                                                              campus={"use":True,"values":['']},
                                                              centros=mock_centros))
        
    ####### Testes para filtros da interface web utilizar (e fornecer via bib Python) ############################

    def test_filter_types(self,
                          types_to_filter : list[str],
                          exclude_empty_values: bool,
                          df : pd.DataFrame|None = None,
                          mock_df_lines_amount : int = 10,
                          mock_types : dict = DIC_USE_TYPES) -> tuple[pd.DataFrame,pd.DataFrame]:
        if (df is not None) and isinstance(df,pd.DataFrame):
            if 'type' not in df.keys():
                raise KeyError('Necessário coluna "type" no dataframe passado como parâmetro')
            return df,filter_types(df,types_to_filter,exclude_empty_values)
        elif self.df is not None and isinstance(self.df,pd.DataFrame):
            if 'type' not in self.df.keys():
                raise KeyError('Necessário coluna "type" no dataframe passado como parâmetro')
            return self.df,filter_types(self.df,types_to_filter,exclude_empty_values)
        else:
            df_mock = generate_mock_df(lines_amount=mock_df_lines_amount,
                                       types=mock_types)
            return df_mock,filter_types(df_mock,types_to_filter,exclude_empty_values)

    def test_filter_dates(self,
                          year_start : int,
                          year_end : int,
                          exclude_empty_values : bool,
                          df : pd.DataFrame|None = None,
                          mock_df_lines_amount : int = 10,
                          mock_years : dict = DIC_USE_YEARS) -> tuple[pd.DataFrame,pd.DataFrame]:
        if (df is not None) and isinstance(df,pd.DataFrame):
            if 'year' not in df.keys():
                raise KeyError('Necessário coluna "year" no dataframe passado como parâmetro')
            return df,filter_dates(df,year_start,year_end,exclude_empty_values)
        elif self.df is not None and isinstance(self.df,pd.DataFrame):
            if 'year' not in self.df.keys():
                raise KeyError('Necessário coluna "year" no dataframe passado como parâmetro')
            return self.df,filter_dates(self.df,year_start,year_end,exclude_empty_values)
        else:
            df_mock = generate_mock_df(lines_amount=mock_df_lines_amount,
                                       years=mock_years)
            return df_mock,filter_dates(df_mock,year_start,year_end,exclude_empty_values)
        
    def test_filter_title_by_words(self,
                                    words : list[str],
                                    match_all : bool,
                                    exclude_empty_values : bool,
                                    df : pd.DataFrame|None = None,
                                    mock_df_lines_amount : int = 10,
                                    mock_titles : dict = DIC_USE_TITLES) -> tuple[pd.DataFrame,pd.DataFrame]:
        if (df is not None) and isinstance(df,pd.DataFrame):
            if 'title' not in df.keys():
                raise KeyError('Necessário coluna "title" no dataframe passado como parâmetro')
            return df,filter_title_by_words(df,words,match_all,exclude_empty_values)
        elif self.df is not None and isinstance(self.df,pd.DataFrame):
            if 'title' not in self.df.keys():
                raise KeyError('Necessário coluna "title" no dataframe passado como parâmetro')
            return self.df,filter_title_by_words(self.df,words,match_all,exclude_empty_values)
        else:
            df_mock = generate_mock_df(lines_amount=mock_df_lines_amount,
                                       titles=mock_titles)
            return df_mock,filter_title_by_words(df_mock,words,match_all,exclude_empty_values)

    def test_filter_subjects(self,
                             subjects : list[str],
                             match_all : bool,
                             exclude_empty_values : bool,
                             df : pd.DataFrame|None = None,
                             mock_df_lines_amount : int = 10,
                             mock_subjects : dict = DIC_USE_SUBJECTS) -> tuple[pd.DataFrame,pd.DataFrame]:
        if (df is not None) and isinstance(df,pd.DataFrame):
            if 'subjects' not in df.keys():
                raise KeyError('Necessário coluna "subjects" no dataframe passado como parâmetro')
            return df,filter_subjects(df,subjects,match_all,exclude_empty_values)
        elif self.df is not None and isinstance(self.df,pd.DataFrame):
            if 'subjects' not in self.df.keys():
                raise KeyError('Necessário coluna "subjects" no dataframe passado como parâmetro')
            return self.df,filter_subjects(self.df,subjects,match_all,exclude_empty_values)
        else:
            df_mock = generate_mock_df(lines_amount=mock_df_lines_amount,
                                       subjects=mock_subjects)
            return df_mock,filter_subjects(df_mock,subjects,match_all,exclude_empty_values)

    def test_filter_authors(self,
                            authors_names : list[str],
                            match_all : bool,
                            exclude_empty_values : bool,
                            df : pd.DataFrame|None = None,
                            mock_df_lines_amount : int = 10,
                            mock_authors : dict = DIC_USE_AUTHORS) -> tuple[pd.DataFrame,pd.DataFrame]:
        if (df is not None) and isinstance(df,pd.DataFrame):
            if 'authors' not in df.keys():
                raise KeyError('Necessário coluna "authors" no dataframe passado como parâmetro')
            return df,filter_authors(df,authors_names,match_all,exclude_empty_values)
        elif self.df is not None and isinstance(self.df,pd.DataFrame):
            if 'authors' not in self.df.keys():
                raise KeyError('Necessário coluna "authors" no dataframe passado como parâmetro')
            return self.df,filter_authors(self.df,authors_names,match_all,exclude_empty_values)
        else:
            df_mock = generate_mock_df(lines_amount=mock_df_lines_amount,
                                       authors=mock_authors)
            return df_mock,filter_authors(df_mock,authors_names,match_all,exclude_empty_values)
        
    def test_filter_advisors(self,
                            advisor_names : list[str],
                            match_all : bool,
                            exclude_empty_values : bool,
                            df : pd.DataFrame|None = None,
                            mock_df_lines_amount : int = 10,
                            mock_advisors : dict = DIC_USE_ADVISORS) -> tuple[pd.DataFrame,pd.DataFrame]:
        if (df is not None) and isinstance(df,pd.DataFrame):
            if 'advisors' not in df.keys():
                raise KeyError('Necessário coluna "advisors" no dataframe passado como parâmetro')
            return df,filter_advisors(df,advisor_names,match_all,exclude_empty_values)
        elif self.df is not None and isinstance(self.df,pd.DataFrame):
            if 'advisors' not in self.df.keys():
                raise KeyError('Necessário coluna "advisors" no dataframe passado como parâmetro')
            return self.df,filter_advisors(self.df,advisor_names,match_all,exclude_empty_values)
        else:
            df_mock = generate_mock_df(lines_amount=mock_df_lines_amount,
                                       advisors=mock_advisors)
            return df_mock,filter_advisors(df_mock,advisor_names,match_all,exclude_empty_values)

    def test_filter_gender(self,
                            genders : list[str],
                            just_contain : bool,
                            exclude_empty_values : bool,
                            df : pd.DataFrame|None = None,
                            mock_df_lines_amount : int = 10,
                            mock_genders : dict = DIC_USE_GENDERS) -> tuple[pd.DataFrame,pd.DataFrame]:
        if (df is not None) and isinstance(df,pd.DataFrame):
            if 'gender_name' not in df.keys():
                raise KeyError('Necessário coluna "gender_name" no dataframe passado como parâmetro')
            return df,filter_gender(df,genders,just_contain,exclude_empty_values)
        elif self.df is not None and isinstance(self.df,pd.DataFrame):
            if 'gender_name' not in self.df.keys():
                raise KeyError('Necessário coluna "gender_name" no dataframe passado como parâmetro')
            return self.df,filter_gender(self.df,genders,just_contain,exclude_empty_values)
        else:
            df_mock = generate_mock_df(lines_amount=mock_df_lines_amount,
                                       genders=mock_genders)
            return df_mock,filter_gender(df_mock,genders,just_contain,exclude_empty_values)
    
    def test_filter_language(self,
                            languages : list[str],
                            exclude_empty_values : bool,
                            df : pd.DataFrame|None = None,
                            mock_df_lines_amount : int = 10,
                            mock_languages : dict = DIC_USE_LANGUAGES) -> tuple[pd.DataFrame,pd.DataFrame]:
        if (df is not None) and isinstance(df,pd.DataFrame):
            if 'language' not in df.keys():
                raise KeyError('Necessário coluna "language" no dataframe passado como parâmetro')
            return df,filter_language(df,languages,exclude_empty_values)
        elif self.df is not None and isinstance(self.df,pd.DataFrame):
            if 'language' not in self.df.keys():
                raise KeyError('Necessário coluna "language" no dataframe passado como parâmetro')
            return self.df,filter_language(self.df,languages,exclude_empty_values)
        else:
            df_mock = generate_mock_df(lines_amount=mock_df_lines_amount,
                                       languages=mock_languages)
            return df_mock,filter_language(df_mock,languages,exclude_empty_values)

    def test_filter_course(self,
                            courses : list[str],
                            exclude_empty_values : bool,
                            df : pd.DataFrame|None = None,
                            mock_df_lines_amount : int = 10,
                            mock_courses : dict = DIC_USE_COURSES) -> tuple[pd.DataFrame,pd.DataFrame]:
        if (df is not None) and isinstance(df,pd.DataFrame):
            if 'course' not in df.keys():
                raise KeyError('Necessário coluna "course" no dataframe passado como parâmetro')
            return df,filter_course(df,courses,exclude_empty_values)
        elif self.df is not None and isinstance(self.df,pd.DataFrame):
            if 'course' not in self.df.keys():
                raise KeyError('Necessário coluna "course" no dataframe passado como parâmetro')
            return self.df,filter_course(self.df,courses,exclude_empty_values)
        else:
            df_mock = generate_mock_df(lines_amount=mock_df_lines_amount,
                                       courses=mock_courses)
            return df_mock,filter_course(df_mock,courses,exclude_empty_values)

    def test_filter_type_course(self,
                            type_courses : list[str],
                            exclude_empty_values : bool,
                            df : pd.DataFrame|None = None,
                            mock_df_lines_amount : int = 10,
                            mock_type_courses : dict = DIC_USE_TYPE_COURSES) -> tuple[pd.DataFrame,pd.DataFrame]:
        if (df is not None) and isinstance(df,pd.DataFrame):
            if 'type_course' not in df.keys():
                raise KeyError('Necessário coluna "type_course" no dataframe passado como parâmetro')
            return df,filter_type_course(df,type_courses,exclude_empty_values)
        elif self.df is not None and isinstance(self.df,pd.DataFrame):
            if 'type_course' not in self.df.keys():
                raise KeyError('Necessário coluna "type_course" no dataframe passado como parâmetro')
            return self.df,filter_type_course(self.df,type_courses,exclude_empty_values)
        else:
            df_mock = generate_mock_df(lines_amount=mock_df_lines_amount,
                                       type_courses=mock_type_courses)
            return df_mock,filter_type_course(df_mock,type_courses,exclude_empty_values)

    def test_filter_centro(self,
                            centros : list[str],
                            exclude_empty_values : bool,
                            df : pd.DataFrame|None = None,
                            mock_df_lines_amount : int = 10,
                            mock_centros : dict = DIC_USE_CENTROS) -> tuple[pd.DataFrame,pd.DataFrame]:
        if (df is not None) and isinstance(df,pd.DataFrame):
            if 'centro' not in df.keys():
                raise KeyError('Necessário coluna "centro" no dataframe passado como parâmetro')
            return df,filter_centro(df,centros,exclude_empty_values)
        elif self.df is not None and isinstance(self.df,pd.DataFrame):
            if 'centro' not in self.df.keys():
                raise KeyError('Necessário coluna "centro" no dataframe passado como parâmetro')
            return self.df,filter_centro(self.df,centros,exclude_empty_values)
        else:
            df_mock = generate_mock_df(lines_amount=mock_df_lines_amount,
                                       centros=mock_centros)
            return df_mock,filter_centro(df_mock,centros,exclude_empty_values)

    def test_filter_campus(self,
                            campuses : list[str],
                            exclude_empty_values : bool,
                            df : pd.DataFrame|None = None,
                            mock_df_lines_amount : int = 10,
                            mock_campuses : dict = DIC_USE_CAMPUS) -> tuple[pd.DataFrame,pd.DataFrame]:
        if (df is not None) and isinstance(df,pd.DataFrame):
            if 'campus' not in df.keys():
                raise KeyError('Necessário coluna "campus" no dataframe passado como parâmetro')
            return df,filter_campus(df,campuses,exclude_empty_values)
        elif self.df is not None and isinstance(self.df,pd.DataFrame):
            if 'campus' not in self.df.keys():
                raise KeyError('Necessário coluna "campus" no dataframe passado como parâmetro')
            return self.df,filter_campus(self.df,campuses,exclude_empty_values)
        else:
            df_mock = generate_mock_df(lines_amount=mock_df_lines_amount,
                                       campus=mock_campuses)
            return df_mock,filter_campus(df_mock,campuses,exclude_empty_values)

    ####### Testes para visualizações da interface web ############################
        
    # def test_plot_line_by_year(self,
    #                            df : pd.DataFrame|None = None,
    #                            year_range : tuple[int,int] = (2002,2025),
    #                            year_col : str = 'year',                               
    #                            mock_df_lines_amount : int = 10,
    #                            mock_years : dict = DIC_USE_YEARS) -> tuple[pd.DataFrame,Any]:
    #     if (df is not None) and isinstance(df,pd.DataFrame):
    #         if 'year' not in df.keys():
    #             raise KeyError('Necessário coluna "year" no dataframe passado como parâmetro')
    #         fig = plot_line_by_year(df,year_col,year_range)
    #         return add_value_counts(df=df,column='year'),fig
    #     elif self.df is not None and isinstance(self.df,pd.DataFrame):
    #         if 'year' not in self.df.keys():
    #             raise KeyError('Necessário coluna "year" no dataframe passado como parâmetro')
    #         fig = plot_line_by_year(self.df,year_col,year_range)
    #         return add_value_counts(df=self.df,column='year'),fig
    #     else:
    #         df_mock = generate_mock_df(lines_amount=mock_df_lines_amount,
    #                                    years=mock_years)
    #         fig = plot_line_by_year(df_mock,year_col,year_range)
    #         return add_value_counts(df=df_mock,column='year'),fig

    # def test_plot_line_by_year_and_gender(self,
    #                            df : pd.DataFrame|None = None,
    #                            year_range : tuple[int,int] = (2002,2025),                             
    #                            mock_df_lines_amount : int = 10,
    #                            mock_years : dict = DIC_USE_YEARS,
    #                            mock_genders : dict = DIC_USE_GENDERS) -> tuple[pd.DataFrame,Any]:
    #     if (df is not None) and isinstance(df,pd.DataFrame):
    #         if 'year' not in df.keys():
    #             raise KeyError('Necessário coluna "year" no dataframe passado como parâmetro')
    #         if 'gender_name' not in df.keys():
    #             raise KeyError('Necessário coluna "gender_name" no dataframe passado como parâmetro')
    #         fig = plot_line_by_year_and_gender(df,year_range)
    #         return df,fig
    #     elif self.df is not None and isinstance(self.df,pd.DataFrame):
    #         if 'year' not in self.df.keys():
    #             raise KeyError('Necessário coluna "year" no dataframe passado como parâmetro')
    #         if 'gender_name' not in self.df.keys():
    #             raise KeyError('Necessário coluna "gender_name" no dataframe passado como parâmetro')
    #         fig = plot_line_by_year_and_gender(self.df,year_range)
    #         return self.df,fig
    #     else:
    #         df_mock = generate_mock_df(lines_amount=mock_df_lines_amount,
    #                                    years=mock_years,
    #                                    genders=mock_genders)
    #         fig = plot_line_by_year_and_gender(df_mock,year_range)
    #         return df_mock,fig

    # def test_plot_language_pie(self,
    #                            df : pd.DataFrame|None = None,
    #                            mock_df_lines_amount : int = 10,
    #                            mock_languages : dict = DIC_USE_LANGUAGES) -> tuple[pd.DataFrame,Any]:
    #     if (df is not None) and isinstance(df,pd.DataFrame):
    #         if 'language' not in df.keys():
    #             raise KeyError('Necessário coluna "language" no dataframe passado como parâmetro')
    #         fig = plot_language_pie(df)
    #         return add_value_counts(df=df,column='language'),fig
    #     elif self.df is not None and isinstance(self.df,pd.DataFrame):
    #         if 'language' not in self.df.keys():
    #             raise KeyError('Necessário coluna "language" no dataframe passado como parâmetro')            
    #         fig = plot_language_pie(self.df)
    #         return add_value_counts(df=self.df,column='language'),fig
    #     else:
    #         df_mock = generate_mock_df(lines_amount=mock_df_lines_amount,
    #                                    languages=mock_languages)
    #         fig = plot_language_pie(df_mock)
    #         return add_value_counts(df=df_mock,column='language'),fig
        
    # def test_plot_lantest_plot_gender_pieguage_pie(self,
    #                            df : pd.DataFrame|None = None,
    #                            mock_df_lines_amount : int = 10,
    #                            mock_genders : dict = DIC_USE_GENDERS) -> tuple[pd.DataFrame,Any]:
    #     if (df is not None) and isinstance(df,pd.DataFrame):
    #         if 'gender_name' not in df.keys():
    #             raise KeyError('Necessário coluna "gender_name" no dataframe passado como parâmetro')
    #         fig = plot_gender_pie(df)
    #         return add_value_counts(df=df,column='gender_name'),fig
    #     elif self.df is not None and isinstance(self.df,pd.DataFrame):
    #         if 'gender_name' not in self.df.keys():
    #             raise KeyError('Necessário coluna "gender_name" no dataframe passado como parâmetro')            
    #         fig = plot_gender_pie(self.df)
    #         return add_value_counts(df=self.df,column='gender_name'),fig
    #     else:
    #         df_mock = generate_mock_df(lines_amount=mock_df_lines_amount,
    #                                    genders=mock_genders)
    #         fig = plot_gender_pie(df_mock)
    #         return add_value_counts(df=df_mock,column='gender_name'),fig
        
    # def test_plot_top_subjects(self,
    #                            top_n : int,
    #                            show_just_words : bool,
    #                            remove_course_words : bool,
    #                            stopwords_pt=STOPWORDS_PT,
    #                            stopwords_ufsc=STOPWORDS_UFSC,
    #                            format_text_func=format_text,
    #                            df : pd.DataFrame|None = None,
    #                            mock_df_lines_amount : int = 10,
    #                            mock_subjects : dict = DIC_USE_SUBJECTS) -> tuple[pd.DataFrame,pd.DataFrame,Any]:
    #     if (df is not None) and isinstance(df,pd.DataFrame):
    #         if 'gender_name' not in df.keys():
    #             raise KeyError('Necessário coluna "gender_name" no dataframe passado como parâmetro')
    #         df_freq,fig = plot_top_subjects(df,top_n=top_n,
    #                                         show_just_words=show_just_words,
    #                                         remove_course_words=remove_course_words,
    #                                         stopwords_pt=stopwords_pt,
    #                                         stopwords_ufsc=stopwords_ufsc,
    #                                         format_text_func=format_text_func)
    #         return df,df_freq,fig
    #     elif self.df is not None and isinstance(self.df,pd.DataFrame):
    #         if 'subjects' not in self.df.keys():
    #             raise KeyError('Necessário coluna "subjects" no dataframe passado como parâmetro')            
    #         df_freq,fig = plot_top_subjects(self.df,top_n=top_n,
    #                                         show_just_words=show_just_words,
    #                                         remove_course_words=remove_course_words,
    #                                         stopwords_pt=stopwords_pt,
    #                                         stopwords_ufsc=stopwords_ufsc,
    #                                         format_text_func=format_text_func)
    #         return self.df,df_freq,fig
    #     else:
    #         df_mock = generate_mock_df(lines_amount=mock_df_lines_amount,
    #                                    subjects=mock_subjects)
    #         df_freq,fig = plot_top_subjects(df_mock,top_n=top_n,
    #                                         show_just_words=show_just_words,
    #                                         remove_course_words=remove_course_words,
    #                                         stopwords_pt=stopwords_pt,
    #                                         stopwords_ufsc=stopwords_ufsc,
    #                                         format_text_func=format_text_func)
    #         return df_mock,df_freq,fig
        
    # def test_plot_top_courses_by_year_and_subject(self,
    #                            subjects : list[str],
    #                            match_all : bool,
    #                            filter_subjects_func=filter_subjects,
    #                            df : pd.DataFrame|None = None,
    #                            mock_df_lines_amount : int = 10,
    #                            mock_subjects : dict = DIC_USE_SUBJECTS,
    #                            mock_years : dict = DIC_USE_YEARS,
    #                            mock_courses : dict = DIC_USE_COURSES) -> tuple[pd.DataFrame,pd.DataFrame,Any]:
    #     if (df is not None) and isinstance(df,pd.DataFrame):
    #         if 'year' not in df.keys():
    #             raise KeyError('Necessário coluna "gender_name" no dataframe passado como parâmetro')
    #         if 'course' not in df.keys():
    #             raise KeyError('Necessário coluna "course" no dataframe passado como parâmetro')
    #         if 'subjects' not in df.keys():
    #             raise KeyError('Necessário coluna "subjects" no dataframe passado como parâmetro')
    #         df_freq,fig = plot_top_courses_by_year_and_subject(df,subjects=subjects,
    #                                                            match_all=match_all,
    #                                                            filter_subjects_func=filter_subjects_func)
    #         return df,df_freq,fig
    #     elif self.df is not None and isinstance(self.df,pd.DataFrame):
    #         if 'year' not in self.df.keys():
    #             raise KeyError('Necessário coluna "gender_name" no dataframe passado como parâmetro')
    #         if 'course' not in self.df.keys():
    #             raise KeyError('Necessário coluna "course" no dataframe passado como parâmetro')
    #         if 'subjects' not in self.df.keys():
    #             raise KeyError('Necessário coluna "subjects" no dataframe passado como parâmetro')
    #         df_freq,fig = plot_top_courses_by_year_and_subject(self.df,subjects=subjects,
    #                                                            match_all=match_all,
    #                                                            filter_subjects_func=filter_subjects_func)
    #         return self.df,df_freq,fig
    #     else:
    #         df_mock = generate_mock_df(lines_amount=mock_df_lines_amount,
    #                                    subjects=mock_subjects,
    #                                    years=mock_years,
    #                                    courses=mock_courses)
    #         df_freq,fig = plot_top_courses_by_year_and_subject(df_mock,subjects=subjects,
    #                                                            match_all=match_all,
    #                                                            filter_subjects_func=filter_subjects_func)
    #         return df_mock,df_freq,fig
