# Roadmap

## Planned Enhancements

- [ ] Multi-tier macro data fallback (API -> DB -> cache) for improved resilience
- [ ] Metrics and observability (Prometheus/Grafana or similar)
- [ ] Distributed artifact storage (S3/MinIO) for multi-node deployments
- [ ] Model versioning and lineage tracking (versions, rollbacks, metadata)
- [ ] Authentication and authorization for API endpoints
- [ ] Health checks and readiness probes for container orchestration (K8s-ready)

## Completed Features

- [X] Dockerized multi-service stack (API, Celery worker, PostgreSQL, Redis)
- [X] CI/CD pipeline with Docker validation + full test suite
- [X] PostgreSQL artifact store via SQLAlchemy ORM
- [X] Asynchronous ML workflows (Celery + Redis)
- [X] Unit and integration tests with mocking of Celery + external services
- [X] Project documentation (architecture, API, datasets, artifacts, testing)

## Known Limitations

- Local filesystem artifact storage (`storage/`) is not suited for distributed deployments
- Macro data fallback currently uses only cache and lacks DB persistence
- Logistic regression baseline model (architecture allows swapping but not implemented)
- No authentication/authorization — not safe for exposure to untrusted networks
