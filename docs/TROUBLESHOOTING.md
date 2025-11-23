# Troubleshooting

## Common Issues

### FRED API errors

If the FRED API is unavailable, the system falls back to cached macro data. Make sure `storage/macro_cache/` exists and contains cached values.

### Missing artifacts

Datasets and models are stored in `storage/datasets/` and `storage/models/`. If an endpoint returns a "not found" error, verify the artifact exists in these directories.

### Import errors

Ensure you're running commands with `uv run` to use the correct Python environment. The project uses [uv](https://github.com/astral-sh/uv) as the package manager instead of pip/venv.

### Module not found errors

If you encounter import errors, ensure the project root is in your Python path. Tests use `tests/conftest.py` to add the project root to `sys.path`.

