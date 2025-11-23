# Architecture

This project follows **Domain-Driven Design (DDD)** principles with bounded contexts for each ML pipeline stage:

```
app/
├── data/          # Dataset generation domain
├── train/         # Model training domain
├── evaluate/      # Model evaluation domain
└── prune/         # Feature pruning domain
```

Each domain contains:
- **`core/`** - Core business logic (pure functions, no dependencies)
- **`service/`** - Orchestration layer (workflow coordination, logging)
- **`routes/`** - HTTP endpoints (FastAPI routes)
- **`schemas/`** - Request/response models (Pydantic)

## Architecture Diagram

```mermaid
flowchart LR
    %% ============================
    %% STYLING
    %% ============================
    classDef domain fill:#1f2937,stroke:#e5e7eb,stroke-width:1px,color:#f8fafc;
    classDef artifact fill:#0f172a,stroke:#94a3b8,stroke-width:1px,color:#f1f5f9;
    classDef api fill:#334155,stroke:#cbd5e1,stroke-width:1px,color:#f1f5f9;

    %% ============================
    %% API LAYER
    %% ============================
    API_Generate(["POST /generate"]):::api
    API_Train(["POST /train"]):::api
    API_Eval(["POST /evaluate"]):::api
    API_Prune(["POST /prune"]):::api

    %% ============================
    %% DOMAINS (Bounded Contexts)
    %% ============================
    subgraph DATA[Dataset Generation Domain]
        DATA_core["core/<br/>synthetic generation<br/>+ FRED integration"]:::domain
        DATA_service["service/<br/>dataset orchestration"]:::domain
        DATA_routes["routes/<br/>/generate"]:::domain
    end

    subgraph TRAIN[Model Training Domain]
        TRAIN_core["core/<br/>logistic regression"]:::domain
        TRAIN_service["service/<br/>training orchestration"]:::domain
        TRAIN_routes["routes/<br/>/train"]:::domain
    end

    subgraph EVAL[Model Evaluation Domain]
        EVAL_core["core/<br/>AUC evaluation"]:::domain
        EVAL_service["service/<br/>evaluation orchestration"]:::domain
        EVAL_routes["routes/<br/>/evaluate"]:::domain
    end

    subgraph PRUNE[Pruning Domain]
        PRUNE_core["core/<br/>SelectFromModel"]:::domain
        PRUNE_service["service/<br/>pruning orchestration"]:::domain
        PRUNE_routes["routes/<br/>/prune"]:::domain
    end

    %% ============================
    %% ARTIFACT STORAGE
    %% ============================
    subgraph STORAGE[Artifact Storage]
        DATA_file["Dataset<br/>Parquet files"]:::artifact
        MODEL_file["Model<br/>Pickle files"]:::artifact
        PRUNED_file["Pruned Model<br/>Pickle files"]:::artifact
        MACRO_cache["Macro Cache<br/>Pickled FRED series"]:::artifact
    end

    %% ============================
    %% FLOWS
    %% ============================
    %% API -> routes
    API_Generate --> DATA_routes
    API_Train --> TRAIN_routes
    API_Eval --> EVAL_routes
    API_Prune --> PRUNE_routes

    %% routes -> service -> core
    DATA_routes --> DATA_service --> DATA_core
    TRAIN_routes --> TRAIN_service --> TRAIN_core
    EVAL_routes --> EVAL_service --> EVAL_core
    PRUNE_routes --> PRUNE_service --> PRUNE_core

    %% Domain outputs to storage
    DATA_core --> DATA_file
    TRAIN_core --> MODEL_file
    PRUNE_core --> PRUNED_file

    %% Macro cache usage
    MACRO_cache -. fallback .-> DATA_core

    %% Pipeline artifact flow
    DATA_file --> TRAIN_core
    TRAIN_core --> EVAL_core
    TRAIN_core --> PRUNE_core
    DATA_file --> EVAL_core
    DATA_file --> PRUNE_core
```

## Architecture Principles

Each bounded context produces named artifacts that subsequent contexts consume, enabling loose coupling. API endpoints use action-based routing (`/generate`, `/train`, `/evaluate`, `/prune`) for HTTP simplicity, while internal architecture follows DDD domain boundaries.

### Artifact Flow

- **Datasets** are generated and persisted with UUID-based names (`dataset_{uuid}.parquet`)
- **Models** are trained and persisted with timestamp-based names (`model_{timestamp}.pkl`)
- **Pruned models** derive their names from base models for traceability
- Artifacts are referenced by name across domain boundaries, avoiding direct data coupling

### Storage Layout

```
storage/
├── datasets/      # Persisted datasets (Parquet)
├── models/        # Persisted models (Pickle)
└── macro_cache/   # Cached FRED series (Pickle)
```

### Macro Cache Fallback

The macro cache (dashed line in diagram) is used only when FRED API is unavailable. Normal flow fetches from FRED API and updates cache; exceptions trigger cache fallback.

