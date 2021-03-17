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
        # FIXME parametrizar para formato atual de pastas e json
        path = Path(
            "/home/ana/workspace/documentos-tcmba/tcmba/files/feira-de-santana/2018/anual"  # noqa
        )
        all_files = list(filter(Path.is_file, path.glob("**/*")))
        print(len(all_files))
        items_file = (
            "/home/ana/workspace/documentos-tcmba/consulta-publica-feira-2018.json"
        )
        items = read_items(items_file)
        print(len(items))
