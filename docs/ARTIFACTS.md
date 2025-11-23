# Artifact Management

## Naming Conventions

Artifacts are persisted with generated names:
- **Datasets**: `storage/datasets/dataset_{uuid_hex_8chars}.parquet` (e.g., `dataset_a1b2c3d4.parquet`)
- **Models**: `storage/models/model_{uuid_hex_8chars}.pkl` (e.g., `model_a1b2c3d4.pkl`)
- **Pruned models**: `storage/models/{model_name}_pruned.pkl` (e.g., `model_a1b2c3d4_pruned.pkl`)

**Rationale:**
- All artifacts use UUID prefixes (8 hex characters) for consistency and collision prevention
- UUIDs ensure uniqueness even when artifacts are created in rapid succession
- Pruned models derive their names from the base model for traceability
- Chronological ordering available via database `created_at` timestamps

**Note:** API responses return artifact names **without file extensions** (e.g., `model_a1b2c3d4`). Filesystem storage includes extensions (e.g., `model_a1b2c3d4.pkl`). The `pruned_model_name` in API responses maps to the filesystem path by appending `_pruned.pkl` to the base model name.

To list artifacts:
```bash
ls storage/datasets
ls storage/models
```

## Reproducibility

Dataset generation uses numpy random state, but the seed is not exposed in the API or documented. As a result, **dataset generation is not deterministic** across runs.

Model artifacts use UUID-based naming for uniqueness. Macro data cached to `storage/macro_cache/` enables consistent dataset generation when macro values are fixed via API override.

**Note:** Full reproducibility would require explicit seed management in the API, which is not currently implemented.

