# Assessment Add-on Pack (v2)

What’s new vs v1:
- CI matrix (3.10–3.12), cached pip, coverage **gate 80%**, JUnit output, profiling job.
- `.coveragerc` for consistent metrics.
- Rubric-aligned REPORT.md template.

## Install
1. Extract into repo root.
2. Commit & push to your fork.
3. Open the **Actions** tab to watch the pipeline.

## Local
```bash
pip install -r requirements.txt
pip install -r requirements-test.txt
pytest
```
