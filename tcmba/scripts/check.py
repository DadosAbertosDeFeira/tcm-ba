"""Script para verificar os arquivos dos itens com os arquivos salvos no disco.

Para isso é esperado que a estrutura de arquivos esteja organizada da seguinte forma:

<cidade>
    <ano>
        anual
            consulta<qualquer-nome>.json
            <unidades>
        mensal
            consulta<qualquer-nome>.json
            <mês-formato-DD>
                <unidades>

O script vai contar com o JSON na mesma pasta da periodicidade (mensal ou anual).
Durante a execução o raspador criar as pastas e arquivos.
Ao final você precisa copiar da pasta atual para a pasta da periodicidade
correspondente.

Os argumentos são passados durante a execução do raspador:

scrapy crawl consulta_publica \
    -a periodicidade=mensal \
    -a competencia=01/2019 \
    -s FILES_STORE="/home/user/" \
    -o consulta-publica-feira-2019-01.json
cp consulta-publica-feira-2019-01.json \
    /home/user/2019/mensal/01/consulta-publica-feira-2019-01.json
"""
import argparse
import json
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("tcmba.check")


def read_items(items_file):
    return json.loads(items_file.read_text())


def check_files_from(dir):
    path = Path(dir)
    if not path.is_dir():
        raise Exception("Não é um diretório.")
    all_files = path.glob("**/*.json")
    json_not_found = True
    stats = {}
    for file in all_files:
        json_not_found = False
        if file.name.startswith("consulta") and file.name.endswith(".json"):
            logger.info("==============================================")
            logger.info(file.parent)  # cidade/ano/modalidade
            try:
                items = read_items(file)
                exists = 0
                not_found = 0
                all_files_from_parent = list(
                    filter(Path.is_file, file.parent.glob("**/*"))
                )
                for item in items:
                    item_path = f"{item['filepath']}{item['filename']}"
                    if Path(item_path).exists():
                        exists += 1
                    else:
                        not_found += 1
                logger.info(
                    f"Arquivos da pasta: {len(all_files_from_parent) - 1} - Itens do JSON: {len(items)}"  # noqa
                )
                logger.info(f"Encontrados: {exists} - Não encontrados: {not_found}")
                stats[file.name] = {
                    "count_folder_files": len(all_files_from_parent) - 1,
                    "count_items": len(items),
                }
            except Exception as e:
                logger.error(f"error: {e}")

    if json_not_found:
        logger.warning("Nenhum JSON encontrado.")

    return stats


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("dir")
    args = parser.parse_args()

    check_files_from(args.dir)
