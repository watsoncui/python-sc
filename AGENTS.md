# AGENTS.md

## Project overview

This repository hosts the **Python 科学计算** (Python Scientific Computing) university course.
It contains course-planning Markdown files (`meta_course/`) and, once built out, weekly
Jupyter Notebook lectures (`notebooks/`), sample data (`data/`), and optional solution files.

See `meta_course/syllabus.md` for course objectives, `meta_course/schedule-18weeks.md` for the
18-week schedule, and `meta_course/notebook-design.md` for notebook structure conventions and
gap analysis.

## Cursor Cloud specific instructions

### Environment

- **Package manager**: `uv` (as specified by the syllabus). Run `uv sync` from the repo root
  to install/refresh all dependencies into `.venv/`.
- **Python version**: 3.10+ (system Python 3.12 works fine).
- Activate the venv with `source .venv/bin/activate`, or prefix commands with `uv run`.

### Running Jupyter

```bash
uv run jupyter lab --ip=0.0.0.0 --port=8888 --no-browser
```

Notebooks live in `notebooks/` and assume data files are at `../data/` (relative path).

### Running tests

```bash
uv run pytest
```

No test files exist yet; pytest discovers and runs any `test_*.py` files automatically.

### Gotchas

- **Chinese fonts in Matplotlib**: The default DejaVu Sans font lacks CJK glyphs. If you
  produce plots with Chinese titles/labels, install a CJK font (e.g. `fonts-noto-cjk`) and
  configure `matplotlib.rcParams['font.sans-serif']`. For CI/headless environments, use
  English labels or the Agg backend to avoid warnings.
- **No buildable package**: The `pyproject.toml` intentionally has no `[build-system]` section
  because this is a course project, not a distributable Python package. `uv sync` handles
  dependency installation without building.
