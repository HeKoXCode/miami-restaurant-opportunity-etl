from pathlib import Path

import nbformat
from nbclient import NotebookClient


BASE_DIR = Path(__file__).resolve().parents[1]
NOTEBOOK_PATH = BASE_DIR / "notebooks" / "01_miami_business_case.ipynb"


def render_notebook():
    notebook = nbformat.read(NOTEBOOK_PATH, as_version=4)
    kernel_name = notebook.metadata.get("kernelspec", {}).get("name", "python3")

    client = NotebookClient(
        notebook,
        timeout=180,
        kernel_name=kernel_name,
        resources={"metadata": {"path": str(BASE_DIR)}},
    )
    client.execute()
    nbformat.write(notebook, NOTEBOOK_PATH)

    print(f"Notebook ejecutado y guardado: {NOTEBOOK_PATH}")


if __name__ == "__main__":
    render_notebook()
