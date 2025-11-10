# Releasing legends

1. Ensure `main` is green and CHANGELOG is updated.
2. Bump version in `pyproject.toml` (and package `__version__`).
3. Tag and push:
   ```bash
   git tag -a vX.Y.Z -m "Release vX.Y.Z"
   git push origin vX.Y.Z
   ```
4. Build & publish (if packaging to PyPI):
   ```bash
   python -m pip install build twine
   python -m build
   twine upload dist/*
   ```
5. Create a GitHub Release with notes.
