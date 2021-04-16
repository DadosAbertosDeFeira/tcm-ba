# Dados do TCM-BA

[![CI](https://github.com/DadosAbertosDeFeira/documentos-tcmba/actions/workflows/ci.yml/badge.svg)](https://github.com/DadosAbertosDeFeira/documentos-tcmba/actions/workflows/ci.yml)

Aqui você encontrará raspadores para o site do Tribunal de Contas dos Municípios da Bahia.

Raspadores disponíveis:

* Documentos da consulta pública
* Processos

**ATENÇÃO**: o acesso por máquina é um direito garantido pela [Lei de Acesso à Informação](http://www.planalto.gov.br/ccivil_03/_ato2011-2014/2011/lei/l12527.htm).
Mas para evitar sobrecarga nos servidores do órgão, certifique-se de baixar os arquivos já disponibilizados ao invés de raspar ou,
se possível, disponibilizar os arquivos que você tenha baixado.

Esse repositório está sujeito ao código de conduta e guia de contribuição
do Dados Abertos de Feira disponíveis [aqui](https://github.com/DadosAbertosDeFeira/guias).

## Raspadores e Dados

Visite nosso [Kaggle](https://www.kaggle.com/dadosabertosdefeira/datasets) para baixar os dados raspados por nós
ou a nossa [página de buscas de dados](https://www.dadosabertosdefeira.com.br/painel/).

Para rodar o ambiente de desenvolvimento utilize o [Poetry](https://python-poetry.org/).

### Processos

O Tribunal lista todos os processos na página de [jurisdicação](https://www.tcm.ba.gov.br/consulta/jurisprudencia/consulta-ementario-juridico/).
Veja mais detalhes sobre os processos listados lá e os detalhes da [consulta processual](https://www.tcm.ba.gov.br/consulta-processual/).

#### Desenvolvimento

Para rodar o _spider_:

```
scrapy crawl processos -o processos-tcmba.json
```

### Documentos da consulta pública

O Tribunal de Contas dos Municípios da Bahia tem uma
[consulta pública](https://e.tcm.ba.gov.br/epp/ConsultaPublica/listView.seam)
para todos os documentos submetidos pelas prefeituras através do SIGA.

Os municípios podem submeter esses dados até 40 dias depois do final do mês.

#### Passo a passo para acesso aos documentos

##### Passo 1: filtros

![](images/filtros.png)

Para carregar a tabela "Prestações de Contas" você precisa selecionar alguns filtros:

* **Periodicidade PCO**:
    - Anual
    - Mensal
* **Competência**: filtro de mês ou ano
* **Tipo**: pode deixar em branco (?)
* **Munícipio**: Feira de Santana (podemos pensar em criar um pacote para raspar por município, assim outras cidades podem se beneficiar da solução)
* **Unidade Jurisdicionada**: todas (teremos que selecionar uma por uma no próximo passo)
* **Status**: pode deixar em branco (esperamos que venham todas)

##### Passo 2: Prestações de Contas

Aqui irão aparecer os resultados das opções selecionadas no Passo 1.
Geralmente uma lista com as unidades jurisdicionadas e a competência (mês/ano).

![](images/prestacao-de-contas.png)

##### Passo 3: Resultados

Ao clicar em uma unidade jurisdicionada (do passo anterior), temos acesso a lista de
documentos, paginada a cada 10 resultados:

![](images/documentos.png)

É interessante utilizar os filtros para coletar a categoria de um grupo de documentos:

![](images/classificacao-de-documento.png)

Essas categorias não estão disponíveis na tabela de resultados mas são interessantes
como filtros para o cidadão.

#### Desenvolvimento

Para rodar o _spider_:

```
scrapy crawl consulta_publica -a periodicidade=mensal -a competencia=08/2018 -a cidade="feira de santana"
scrapy crawl consulta_publica -a periodicidade=anual -a competencia=2018 -a cidade="são gonçalo"
```
