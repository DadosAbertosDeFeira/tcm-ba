"""
De:

    cidade
        ano
            mensal
                mes
                    unidades
                    consulta-publica-*.json
            anual
                unidades (camara, prefeitura etc)
S3 URL: https://s3.console.aws.amazon.com/s3/buckets/dadosabertosdefeira?
prefix=maria-quiteria/files/cityhallbid/2021/3/2/

Para:

    tcmbapublicview
        ano
            mes
                dia (?)
"""
import argparse
import json
import sqlite3
from pathlib import Path


def config():
    con = sqlite3.connect("tcmba.db")
    cur = con.cursor()
    cur.execute(open("scripts/create-table.sql").read())
    con.close()


def execute(query):
    con = sqlite3.connect("tcmba.db")
    cur = con.cursor()
    cur.execute(query)
    con.close()


def read_items(items_file):
    return json.loads(open(items_file).read())


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("action")
    parser.add_argument("--dir")

    args = parser.parse_args()

    if args.action == "createdb":
        config()
    elif args.action == "populate":
        # TODO ler json e salvar no banco
        pass
    elif args.action == "check":
        # TODO conferir se todos os arquivos do json podem ser encontrados
        # checar estrutura
        pass
    elif args.action == "metrics":
        path = Path(
            "/home/ana/workspace/documentos-tcmba/tcmba/files/feira-de-santana/"  # noqa
        )
        base_dir = path.name
        all_files = filter(Path.is_file, path.glob("**/*"))
        for file in all_files:
            if file.name.startswith("consulta") and file.name.endswith(".json"):
                print("==============================================")
                items = read_items(file)
                print(f"{len(items)} {file}")
                all_files_from_parent = list(
                    filter(Path.is_file, file.parent.glob("**/*"))
                )
                # exclui o JSON atual
                print(f"{len(all_files_from_parent)-1} {file.parent}")
