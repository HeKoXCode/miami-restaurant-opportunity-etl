import asyncio
import sys
import warnings
from pathlib import Path

import nbformat
from nbclient import NotebookClient


BASE_DIR = Path(__file__).resolve().parents[1]
NOTEBOOK_PATH = BASE_DIR / "notebooks" / "01_miami_business_case.ipynb"


def configure_windows_event_loop():
    """Use the selector loop required by pyzmq on supported Windows versions."""
    if sys.platform != "win32":
        return

    # Python 3.14 deprecates policies ahead of their removal in 3.16. The
    # project supports up to 3.14, where this remains the documented pyzmq fix.
    with warnings.catch_warnings():
        warnings.filterwarnings(
            "ignore",
            message=r"'asyncio\.(WindowsSelectorEventLoopPolicy|set_event_loop_policy)'.*",
            category=DeprecationWarning,
        )
        selector_policy = getattr(asyncio, "WindowsSelectorEventLoopPolicy", None)
        if selector_policy is None:
            return
        asyncio.set_event_loop_policy(selector_policy())


def render_notebook():
    configure_windows_event_loop()

    notebook = nbformat.read(NOTEBOOK_PATH, as_version=4)
    for cell in notebook.cells:
        cell.metadata.pop("execution", None)

    kernel_name = notebook.metadata.get("kernelspec", {}).get("name", "python3")

    client = NotebookClient(
        notebook,
        timeout=180,
        kernel_name=kernel_name,
        record_timing=False,
        # The managed kernel is local and short-lived. Keep its transport
        # notice out of the report log while preserving errors and cell output.
        extra_arguments=["--Application.log_level=ERROR"],
        resources={"metadata": {"path": str(BASE_DIR)}},
    )
    client.execute()
    nbformat.write(notebook, NOTEBOOK_PATH)

    print(f"Notebook ejecutado y guardado: {NOTEBOOK_PATH}")


if __name__ == "__main__":
    render_notebook()
