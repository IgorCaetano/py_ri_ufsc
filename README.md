# py_ri_ufsc

*Se você está visualizando esta documentação no PyPI, por favor, visite a documentação no [GitHub](https://github.com/IgorCaetano/py_ri_ufsc) para uma versão mais completa.*

##  Conteúdos

* [Sobre o Projeto](#sobre-o-projeto)
* [Requisitos](#requisitos)
* [Instalação e uso](#instalação-e-uso)
* [Exemplos de uso](#exemplos-de-uso)
* [Metadados disponíveis no dataset e seus respectivos significados](#metadados-disponíveis-no-dataset-e-seus-respectivos-significados)
* [Testes e validações](#testes-e-validações)
* [Observações e dicas](#observações-e-dicas)
* [Autores](#autores)
* [Licença](#licença)

## Sobre o Projeto

Este pacote é o resultado de um Projeto de Fim de Curso do graduando Igor Caetano de Souza do curso de Engenharia de Controle e Automação da Universidade Federal de Santa Catarina. O objetivo principal do projeto foi construir um pacote em Python que facilitasse o acesso e análise dos metadados presentes no Repositório Institucional da UFSC (RIUFSC).

## Requisitos

Para executar este projeto, você precisará de:

* Python 3.x
* Gerenciador de pacotes (`pip`).


## Instalação e uso

O pacote está disponível no [Python Package Index (PyPI)](https://pypi.org/project/py-ri-ufsc/).

1.  **Instale o pacote via `pip install`:**
    ```bash
    pip install py-ri-ufsc -U
    ```
    Adicione "-U" para baixar o pacote disponível mais atualizado.
    
    *A instalação pode levar alguns minutos, pois há dependência de outras bibliotecas do Python, listadas no arquivo `requirements.txt` do projeto.*

2.  **Uso principal:**

    O ponto de entrada para todas as funcionalidades é a classe `RIUFSC()`. Veja um exemplo básico de como importá-la e instanciá-la:

    ```python
    from py_ri_ufsc import RIUFSC

    # Instanciando um objeto da classe principal
    ri_ufsc = RIUFSC()
    ```
    
    Após a execução de `from py_ri_ufsc import RIUFSC`, a importação do dataset será realizada e você poderá visualizar uma tela como esta:

    ![img-alt](dataset_download.png)

    Esse download só será realizado uma vez no ambiente de execução atual.

    *Caso você crie um novo ambiente virtual, por exemplo, será necessário realizar o download do dataset neste novo ambiente novamente ao importar a biblioteca.*

---

## Exemplos de uso

Abaixo estão alguns exemplos práticos de como utilizar a biblioteca após importar e instanciar um objeto (como o *`ri_ufsc`*) no código.

<details>
<summary>Exemplo 1: Obter todas as colunas/metadados disponíveis no dataset <i>(clique para expandir)</i></summary>
<br>

```python
available_columns = ri_ufsc.get_available_columns_in_ri_ufsc_dataset()
```
O conteúdo de `available_columns` ficará sendo:

```python
['identifier_header',
'datestamp_header',
'setSpec',
'title',
'authors',
'advisors',
'co_advisors',
'issued_date',
'available_date',
'accessioned_date',
'language',
'subjects',
'type',
'publisher',
'description',
'abstract',
'link_site',
'link_doc',
'source_xml_file',
'gender_name',
'full_locations',
'first_com',
'last_col',
'course',
'type_course',
'campus',
'centro',
'year']
```

Importante destacar que este método não carrega o dataset na memória RAM, pois, por se tratar de um arquivo parquet, consegue-se apenas ler o cabeçalho das colunas.

</details>

<details>
<summary>Exemplo 2: Obter dataset com colunas selecionadas <i>(clique para expandir)</i></summary>
<br>

Digamos que você queira carregar o dataset, mas apenas usar colunas selecionadas (para economizar RAM), você consegue isto da seguinte forma:

```python
df = ri_ufsc.get_raw_ri_ufsc_dataset(columns_to_use=['title','authors','language','year'])
```
O conteúdo de `df` ficará sendo um *dataframe* do `pandas` com mais de 168 mil linhas e com as colunas de título, autores, idioma e ano de publicação no RIUFSC.

</details>

<details>
<summary>Exemplo 3: Obter valores dentro de uma coluna específica <i>(clique para expandir)</i></summary>
<br>

Digamos que você queira saber quais valores e suas respectivas frequências estão contidos dentro de uma coluna específica (no caso de gênero dos autores `gender_name`).

```python
available_values = ri_ufsc.get_available_values_in_ri_ufsc_dataset(column_name='gender_name')
```
O conteúdo de `available_values` ficará sendo:
```python
[' (58172)', 'F (54513)', 'M (50165)', 'F,M (6119)']
```

Ou seja, parece que temos 58.172 registros em que o gênero não foi identificado, 54.513 apenas com autoras, 50.165 apenas com autores e 6.119 com autoras e autores.


Além disso, pode-se também obter apenas os valores, setando o parâmetro `show_amount=False`.
```python
available_values = ri_ufsc.get_available_values_in_ri_ufsc_dataset(column_name='gender_name',show_amount=False)
```
`available_values`:
```python
['', 'F', 'M', 'F,M']
```
</details>

<details>
<summary>Exemplo 4: Obter dataset filtrado <i>(clique para expandir)</i></summary>
<br>

Agora vamos para um uso mais robusto e completo, demonstrando toda potencialidade do nosso pacote.
Digamos que você queira obter os registros dentro do dataset que satisfaçam uma série de filtros para determinadas colunas/metadados com seus respectivos valores.
Para isto, pode-se usar o seguinte exemplo como base:


Suponha que queremos carregar apenas os registros que tenham seu tipo igual a "TCC", podemos então desenvolver uma linha de código como esta:
```python
df_filtered = ri_ufsc.get_df_filtered(type_filter=['TCC'])
```

Assim, o conteúdo de `df_filtered` ficará sendo um dataframe com uma coluna `link_site` (link para o registro no site do RIUFSC) e `type` (coluna de tipo utilizada para realização do filtro):


Se faz importante destacar que este método, por padrão, trabalha com valores vazios dentro da coluna que foi filtrada, substituindo por "NÂO ESPECIFICADO" ou "NÂO IDENTIFICADO" (na coluna de gênero).
Para obter apenas um dataset em que todos os registros têm valores iguais a "TCC" na coluna `type`, podemos usar o parâmetro `exclude_empty_valeus` da seguinte forma:
```python
df_filtered = ri_ufsc.get_df_filtered(type_filter=['TCC'],
                                      exclude_empty_values=True)
```
Agora a variável `df_filtered` conterá apenas registros em que `type` seja igual a "TCC".

Além disso, se quiser trabalhar com valores vazios nas colunas em que se deseja executar um filtro, pode-se setar um valor padrão para mostrar ao invés de "NÂO ESPECIFICADO"/"NÂO IDENTIFICADO".
```python
df_filtered = ri_ufsc.get_df_filtered(type_filter=['TCC'],
                                      replace_empty_values='-')
```
Como `exclude_empty_values`, por padrão, é `False`, podemos ocultá-lo da chamada da função. Dessa forma, obtemos um dataframe onde valores vazios na coluna `type` são preenchidos com "-".

Podemos, ainda, utilizar uma série de filtros na mesma chamada da função. Se quisermos, além de filtrar o tipo de registro, filtrar também o gênero dos autores, podemos usar:
```python
df_filtered = ri_ufsc.get_df_filtered(type_filter=['TCC'],
                                      gender_filter=['F'],
                                      exclude_empty_values=True)
```
O dataframe `df_filtered` conterá os registros que apresentem `type`="TCC" e `gender_name`="F" ou `gender_name`='F,M', ou seja, apenas registros que tenham, ao menos, uma autora.

Se quisermos tornar o filtro de gênero exclusivo para aceitar apenas "F", ou seja, registros publicados unicamente por mulheres, podemos usar o parâmetro `just_contain`, que é, por padrão, igual a `True`.

```python
df_filtered = ri_ufsc.get_df_filtered(type_filter=['TCC'],
                                      gender_filter=['F'],
                                      just_contain=False,
                                      exclude_empty_values=True)
```
Agora dataframe `df_filtered` conterá os registros que apresentem `type`="TCC" e `gender_name`="F".

No caso de querermos um dataset com registros de tipo sendo "TCC", gênero dos autores apenas "F" (só mulheres), deixar os valores vazios, mas setá-los para "-" e **escolher quais colunas serão retornadas no dataframe filtrado**, podemos escrever a seguinte linha de código:
```python
df_filtered = ri_ufsc.get_df_filtered(type_filter=['TCC'],                                    
                                      gender_filter=['F'],
                                      just_contain=False,
                                      replace_empty_values='-',
                                      exported_columns=['year','type','gender_name','authors'])
```

Com isso, podemos verificar que o parâmetro `exported_columns` edita as colunas que estarão contidas no dataframe retornado. Por padrão será retornado `link_site` e as colunas usadas no filtro, mas podemos alterar isso usando `exported_columns`, como no exemplo.
`df_filtered` ficará sendo um dataframe contendo todos os registros do dataset em que seu tipo é "TCC" ou não especificado, gênero dos autores igual a feminino ("F") ou não identificado, os valores não especificados/identificados serão substituídos por "-" e as colunas presentes serão `year`,`type`,`gender_name`,`authors`.

</details>

---

## Metadados disponíveis no dataset e seus respectivos significados
* **`title`**: Títulos.
* **`authors`**: Autor(es) (se tiver mais de um(a), estarão separados por ";").
* **`advisors`**: Orientador(es) (se tiver mais de um(a), estarão separados por ";").
* **`co_advisors`**: Co-orientador(es) (se tiver mais de um(a), estarão separados por ";").
* **`issued_date`**: A data de publicação.
* **`available_date`**: A data em que o documento foi tornado público e disponível para acesso no repositório.
* **`accessioned_date`**: A data em que o item foi formalmente incluído (catalogado) no acervo do repositório.
* **`language`**: O idioma principal em que o documento foi escrito (ex: `por` para português, `eng` para inglês, etc).
* **`subjects`**: As palavras-chave ou áreas de conhecimento que descrevem o tema do trabalho separadas por ";".
* **`type`**: O tipo do documento (ex: `TCC` para Trabalho de Conclusão de Curso, `ARTIGO` para artigos, etc).
* **`publisher`**: A instituição publicadora.
* **`description`**: A descrição contida do registro.
* **`abstract`**: O resumo (priorizando o escrito em português) contido no registro.
* **`link_site`**: O link para a página de apresentação do item no site do repositório.
* **`link_doc`**: O link direto para o documento (exclusivo para PDFs atualmente).
* **`identifier_header`**: O identificador único e universal para cada registro no repositório. É a "chave primária" do documento.
* **`datestamp_header`**: A data e hora da última modificação do registro no sistema, indicando quando a informação foi atualizada pela última vez.
* **`setSpec`**: Especifica a qual "conjunto" ou "coleção" o documento pertence dentro do repositório (ex: `col_123456789_128640` para Programa de Pós-Graduação em Engenharia de Automação e Sistemas).
* **`source_xml_file` (metadado extra)**: O nome do arquivo XML original de onde os metadados foram extraídos na etapa de coleta de dados deste pacote, útil para rastreamento e auditoria.
* **`gender_name` (metadado extra)**: O gênero (masculino "M"/feminino "F"/feminino e masculino "F,M") dos autores, inferido a partir do primeiro nome para fins de análise demográfica gênero "F,M" quer dizer que existem homens e mulheres nos autores do trabalho.
* **`full_locations` (metadado extra)**: A estrutura hierárquica completa da localização do trabalho na universidade (ex: `UFSC -> CTC -> -> Teses e Dissertações -> ECA`).
* **`first_com` (metadado extra)**: A primeira comunidade na hierarquia do repositório (ex: `Teses e Dissertações`).
* **`last_col` (metadado extra)**: A última e mais específica coleção a que o item pertence (ex: `Trabalhos de Conclusão de Curso de Graduação em Sistemas da Informação`).
* **`course` (metadado extra)**: O nome do curso ao qual o trabalho está vinculado.
* **`type_course` (metadado extra)**: O nível do curso (ex: `GRAD` para graduação, `POS` para pós-graduação).
* **`campus` (metadado extra)**: O campus da universidade (ex: `FLN`, `ARA`, `BLN`).
* **`centro` (metadado extra)**: O centro de ensino (ex: `CTC`, `CFH`, `CFM`).
* **`year` (metadado extra)**: O ano de publicação do trabalho, extraído de `issued_date`.

Os metadados "extras" foram enriquecidos no dataset original (adicionados por meio dos dados originais).

---

## Testes e validações

Se você ficou curioso para entender melhor como os motores de consulta e filtro funcionam dentro desse pacote, foi preparado uma classe especial para o desenvolvimento de teste e validações chamada `TestRIUFSC()`. Nela você pode verificar o funcionamento e adquirir segurança nos metadados extras (enriquecidos) no dataset.

### Testes de enriquecimento de dados

<details>
<summary>Teste 1: Coleta de gênero dos autores por meio do primeiro nome <i>(clique para expandir)</i></summary>
<br>

Digamos que você quer "ver com os próprios olhos" o funcionamento da lógica que analisa o gênero dos autores com base no (primeiro) nome. Para isso, pode-se seguir os seguintes passos:

1. Importar a classe de teste do pacote.
```python
from py_ri_ufsc.get_metadata.tests import TestRIUFSC
test_ri_ufsc = TestRIUFSC()
```
2. Gerar um dataframe com os dados processados:
```python
df_test = test_ri_ufsc.test_gender_by_name()
```
3. Visualizar o resultado do dataframe de teste. No caso de execução em (jupyter) notebook, podemos usar o comando `display()`:
```python
display(df_test)
```

Isso irá mostrar o resultado de um dataframe com uma coluna de autores `authors` e seus gêneros `gender_name`.
Os valores da coluna processada (`authors`) são gerados de forma aleatória por meio de uma função geradora de um dataframe (`generate_mock_df()`), que retorna um dataframe com dados fictícios de 10 (por padrão) linhas.


Se você gostaria de passar os próprios nomes para teste, pode-se seguir pelo seguinte caminho:
```python
df_test = test_ri_ufsc.test_gender_by_name(mock_df_lines_amount=5, # Seta o número de linhas do dataframe testado
                                           mock_authors={"use":True, # Necessário passar parâmetro True para chave "use"
                                                         "values":['Souza, Igor Caetano de', # Lista para teste na chave "values"
                                                                   'Silva, Franciele Dias da',
                                                                   'Soares, Henrique']})
```
</details>

<details>
<summary>Teste 2: Coleta de tipo de curso com base no tipo de registro <i>(clique para expandir)</i></summary>
<br>

A coleta de curso é uma etapa importantíssima no enriquecimento do dataset disponibilizado por este pacote. Tal coleta usa, inicialmente, a descrição do registro para tentar identificar o curso.

Para verificar o funcionamento, podemos testar da seguinte forma:

1. Importar a classe de teste do pacote.
```python
from py_ri_ufsc.get_metadata.tests import TestRIUFSC
test_ri_ufsc = TestRIUFSC()
```
2. Gerar um dataframe com os dados processados:
```python
df_test = test_ri_ufsc.test_insert_type_course_from_type()
```
3. Visualizar o resultado do dataframe de teste. No caso de execução em (jupyter) notebook, podemos usar o comando `display()`:
```python
display(df_test)
```

Isso irá mostrar o resultado de um dataframe com uma coluna de tipos `type` e seus tipos de curso `type_course`.

Toda vez que você executar `test_insert_type_course_from_type()`, os valores da coluna `type` irão mudar, já que, novamente, são gerados por uma função de dados aleatórios (dentro de um intervalo especificado préviamente).
</details>

<details>
<summary>Teste 3: Coleta de curso pela descrição <i>(clique para expandir)</i></summary>
<br>

A coleta de curso é uma etapa importantíssima no enriquecimento do dataset disponibilizado por este pacote. Tal coleta usa, inicialmente, a descrição do registro para tentar identificar o curso.

Para verificar o funcionamento, podemos testar da seguinte forma:

0. Dica extra para melhorar visualização de colunas com muitos dados, execute os seguintes códigos:
```python
import pandas as pd
pd.set_option('display.max_columns', None)
pd.set_option('display.width', 0)
pd.set_option('display.max_colwidth', None)
```

1. Importar a classe de teste do pacote.
```python
from py_ri_ufsc.get_metadata.tests import TestRIUFSC
test_ri_ufsc = TestRIUFSC()
```
2. Gerar um dataframe com os dados processados:
```python
df_test = test_ri_ufsc.test_get_course_from_description()
```
3. Visualizar o resultado do dataframe de teste. No caso de execução em (jupyter) notebook, podemos usar o comando `display()`:
```python
display(df_test)
```

Isso irá mostrar o resultado de um dataframe com uma coluna de descrições `description` e seus cursos `course`.

Toda vez que você executar `test_get_course_from_description()`, os valores da coluna `description` irão mudar, já que, novamente, são gerados por uma função de dados aleatórios (dentro de um intervalo especificado préviamente).
</details>

<details>
<summary>Teste 4: Coleta de campus pela descrição <i>(clique para expandir)</i></summary>
<br>

Pode-se, ainda, passar um dataframe pré-configurado para os métodos de teste da classe TestRIUFSC().

Podemos usar de exemplo o dataframe (`df_test`) retornado do exemplo 3, da seguinte forma:

1. Importar a classe de teste do pacote (se já tiver importado, ignore este passo):
```python
from py_ri_ufsc.get_metadata.tests import TestRIUFSC
test_ri_ufsc = TestRIUFSC()
```
2. Gerar um dataframe com os dados processados:
```python
df_test = test_ri_ufsc.test_insert_campus_into_df_from_description(df=df_test) # Use o parâmetro df para usar um dataframe pré-configurado
```
3. Visualizar o resultado do dataframe de teste. No caso de execução em (jupyter) notebook, podemos usar o comando `display()`:
```python
display(df_test)
```

Lembre-se que o dataframe passado como entrada da função (usando o parâmetro `df`) deve conter as colunas que serão usadas pelo método chamado. Neste caso, `df_test` tem uma coluna `description`, usada por `test_insert_campus_into_df_from_description()` para retornar um dataframe testado.

Isso irá mostrar o resultado de um dataframe com uma coluna de descrições `description`, seus cursos `course` e seus campus `campus`.
</details>


<details>
<summary>Teste 5: Coleta de centro baseado no campus <b>(só para campus que possuem apenas um centro)</b> <i>(clique para expandir)</i></summary>
<br>


1. Importar a classe de teste do pacote:
```python
from py_ri_ufsc.get_metadata.tests import TestRIUFSC
test_ri_ufsc = TestRIUFSC()
```
2. Gerar um dataframe com os dados processados:
```python
df_test = test_ri_ufsc.test_get_list_of_centro_from_campus()
```
3. Visualizar o resultado do dataframe de teste. No caso de execução em (jupyter) notebook, podemos usar o comando `display()`:
```python
display(df_test)
```

Isso irá mostrar o resultado de um dataframe com uma coluna de campus `campus` e seus centros em `centro`.
</details>


### Testes de filtros



---

## Observações e dicas

- Existem diversas funcionalidades neste pacote, todas as funções, parâmetros disponíveis, usabilidade, etc estão descritas com detalhes nas suas respectivas docstrings (pequenos textos informativos para cada função/método), type hints e alguns comentários para facilitar o entendimento ao desenvolver em tempo real os códigos.

- Nas versões mais atualizadas do Visual Studio Code, com a extensão do Python instalada, pode-se visualizar a docstring das funções e métodos simplesmente passando o mouse por cima de seu nome dentro do seu código.

![gif_docstrings](gif_docstrings.gif)

---

## Autores

* [Igor Caetano de Souza](https://www.github.com/IgorCaetano)

---

## Licença

Este projeto está licenciado sob a Licença MIT - veja o arquivo [LICENSE.md](LICENSE.md) para detalhes.
