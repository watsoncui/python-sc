# AGENTS.md

## Cursor Cloud specific instructions

This repository is a **Python 科学计算 (Python Scientific Computing)** course materials repo for undergraduate math students. It currently contains course planning documents in `meta_course/` and will eventually hold Jupyter Notebooks in `notebooks/`.

### Environment

- **Python 3.12** with a `.venv` managed by `uv` (prompt name: `python-computing-science`).
- The `.venv` is gitignored; the update script recreates it if missing.
- Core packages: `numpy`, `scipy`, `matplotlib`, `sympy`, `pandas`, `jupyter`, `jupyterlab`, `ipykernel`, `ipywidgets`, `pytest`.
- Activate with: `source /workspace/.venv/bin/activate` or use `/workspace/.venv/bin/python` directly.

### Running services

- **JupyterLab**: `/workspace/.venv/bin/jupyter lab --ip=0.0.0.0 --port=8888 --no-browser --NotebookApp.token="" --NotebookApp.password=""`
- No other services (databases, APIs, Docker) are needed.

### Lint / Test / Build

- No lint or test suite exists yet (the repo only has markdown planning docs at this early stage).
- When notebooks are added, run them with: `/workspace/.venv/bin/jupyter nbconvert --to notebook --execute <notebook>.ipynb`
- pytest is available at `/workspace/.venv/bin/pytest` for any future test files.

### Key caveats

- There is no `pyproject.toml` or `requirements.txt` in the repo yet. The update script installs core packages directly via `uv pip install`.
- If a `pyproject.toml` or `requirements.txt` is added to the repo in the future, the update script should be updated to use it instead.
