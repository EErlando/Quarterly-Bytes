# fix_widgets_metadata.py
import json, pathlib

def clean_notebook(p: pathlib.Path):
    nb = json.loads(p.read_text(encoding="utf-8"))
    # Drop top-level widgets metadata
    nb.setdefault("metadata", {}).pop("widgets", None)
    # Drop any per-cell widgets metadata
    for cell in nb.get("cells", []):
        if isinstance(cell, dict):
            cell.get("metadata", {}).pop("widgets", None)
    p.write_text(json.dumps(nb, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"Fixed: {p}")

def main():
    repo = pathlib.Path(".")
    for p in repo.rglob("*.ipynb"):
        try:
            clean_notebook(p)
        except Exception as e:
            print(f"Skipped {p} -> {e}")

if __name__ == "__main__":
    main()
