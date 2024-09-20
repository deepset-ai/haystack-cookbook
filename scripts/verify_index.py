from pathlib import Path

import tomllib

if __name__ == "__main__":
    root_path = Path(__file__).parent.parent

    index_file = root_path / "index.toml"
    index_data = tomllib.loads(index_file.read_text())

    notebooks = list(root_path.glob("notebooks/*.ipynb"))

    failed = False
    indexed_notebooks = [
        notebook["notebook"]
        for notebook in index_data["cookbook"]
        if "notebook" in notebook
    ]
    for notebook in notebooks:
        if notebook.name not in indexed_notebooks:
            print(f"Notebook '{notebook.name}' not found in 'index.toml'")
            failed = True

    for notebook in index_data["cookbook"]:
        if "notebook" not in notebook:
            print(f"Notebook '{notebook}' has no file")
            failed = True
            continue

        if not (root_path / f"notebooks/{notebook['notebook']}").exists():
            print(f"Notebook '{notebook['notebook']}' file not found")
            failed = True

        if "title" not in notebook:
            print(f"Notebook '{notebook['notebook']}' has no title")
            failed = True

        if not notebook.get("topics"):
            print(f"Notebook '{notebook['notebook']}' has no topics")
            failed = True

    if failed:
        exit(1)
