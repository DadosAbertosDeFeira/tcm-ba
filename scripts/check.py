"""Script para verificar os arquivos dos itens com os arquivos salvos no disco."""
import argparse
import json
from pathlib import Path
from re import sub


def normalize_text(text):
    return sub(r"[^a-zA-Z0-9\u00C0-\u017F\s\.-]", "", text)


def read_items(items_file):
    return json.loads(items_file.read_text())


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("action")
    parser.add_argument("dir")
    args = parser.parse_args()

    if args.action == "check":
        path = Path(args.dir)
        all_files = path.glob("**/*.json")
        for file in all_files:
            if file.name.startswith("consulta") and file.name.endswith(".json"):
                print("==============================================")
                print(file.parent)  # cidade/ano/modalidade
                try:
                    items = read_items(file)
                    exists = 0
                    not_found = 0
                    all_files_from_parent = list(
                        filter(Path.is_file, file.parent.glob("**/*"))
                    )
                    for item in items:
                        unit = normalize_text(item["unit"])
                        category = normalize_text(item["category"])
                        filename = normalize_text(item["filename"])
                        item_path = f"{file.parent}/{unit}/{category}/{filename}"
                        if Path(item_path).exists():
                            exists += 1
                        else:
                            not_found += 1
                    print(
                        f"Arquivos da pasta: {len(all_files_from_parent)-1} - Itens do JSON: {len(items)}"  # noqa
                    )
                    print(f"Encontrados: {exists} - Não encontrados: {not_found}")
                except Exception as e:
                    print(f"error: {e}")
    elif args.action == "metrics":
        path = Path(args.dir)
        all_files = path.glob("**/*.json")
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
                assert len(items) == len(all_files_from_parent) - 1
