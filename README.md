# Dados do TCM-BA

[![CI](https://github.com/DadosAbertosDeFeira/documentos-tcmba/actions/workflows/ci.yml/badge.svg)](https://github.com/DadosAbertosDeFeira/documentos-tcmba/actions/workflows/ci.yml)

Aqui você encontrará raspadores para o site do Tribunal de Contas dos Municípios da Bahia.

Raspadores disponíveis:

* Documentos da consulta pública
* Processos

**ATENÇÃO**: o acesso por máquina é um direito garantido pela [Lei de Acesso à Informação](http://www.planalto.gov.br/ccivil_03/_ato2011-2014/2011/lei/l12527.htm).
Mas para evitar sobrecarga nos servidores do órgão, certifique-se de baixar os arquivos já disponibilizados ao invés de raspar ou,
se possível, disponibilizar os arquivos que você tenha baixado.

## Dados

Visite nosso [Kaggle](https://www.kaggle.com/dadosabertosdefeira/datasets) para baixar os dados raspados por nós.
Em breve mais dados disponíveis para _download_ aqui. :soon:

### Processos

O Tribunal lista todos os processos na página de [jurisdicação](https://www.tcm.ba.gov.br/consulta/jurisprudencia/consulta-ementario-juridico/).
Veja mais detalhes sobre os processos listados lá e os detalhes da [consulta processual](https://www.tcm.ba.gov.br/consulta-processual/).

### Documentos da consulta pública

O Tribunal de Contas dos Municípios da Bahia tem uma
[consulta pública](https://e.tcm.ba.gov.br/epp/ConsultaPublica/listView.seam)
para todos os documentos submetidos pelas prefeituras através do SIGA.

Infelizmente esses dados não estão disponíveis para download em massa
ou em formato aberto. Nós queremos libertar esses dados. Dessa forma,
qualquer cidadão poderá ter acesso a prestação de contas feita por qualquer
município no estado da Bahia.

Os municípios podem submeter esses dados até 40 dias depois do final do mês.

Esse repositório está sujeito ao código de conduta e guia de contribuição
do Dados Abertos de Feira disponíveis [aqui](https://github.com/DadosAbertosDeFeira/guias).

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

## Desenvolvimento

Para rodar o _spider_:

```
scrapy crawl consulta_publica -a periodicidade=mensal -a competencia=08/2018 -a cidade="feira de santana"
scrapy crawl consulta_publica -a periodicidade=anual -a competencia=2018 -a cidade="são gonçalo"
```

---

Outras informações:

- Competência (período) mais antigo: 10/2015

Demandas técnicas:

- Cuidado com o número de acessos para não sobrecarregar o portal
