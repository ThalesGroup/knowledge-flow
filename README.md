# Knowledge Flow Backend

FastAPI microservice that ingests documents, extracts knowledge, and stores searchable vectors.

## Developer Docs

For a deeper understanding of how Knowledge Flow works — including how to add custom processors, services, or storage backends — see the full [**Developer Guide**](docs/DEVELOPER_GUIDE.md).

## Quick start

```bash
git clone https://github.com/ThalesGroup/knowledge-flow.git
cd knowledge-flow
make dev  # sets up .venv with uv
cp config/.env.template config/.env   # add OPENAI_API_KEY
make run  # http://localhost:8111/knowledge/v1/docs
```

Prefer VS Code + Docker? See **docs/devcontainer.md** for a one-click setup.

## ✨ Features

- PDF / DOCX / PPTX ingestion → Markdown
- Vectorization pipeline with OpenAI / Azure / Ollama
- Pluggable storage (filesystem, MinIO)
- Metadata index (OpenSearch or in-memory)

Supports local dev with just an OpenAI key — no external services required.

For advanced use cases (Keycloak, OpenSearch, MinIO, Knowledge UI), see the
**[fred-deployment-factory](https://github.com/ThalesGroup/fred-deployment-factory)** repo.

## Model Backends

Works with:

| Provider       | Setup Hint |
|----------------|------------|
| **OpenAI**     | Set `OPENAI_API_KEY` |
| **Azure OpenAI** | See `config/configuration.yaml` for required vars |
| **Ollama**     | Point `base_url` to your Ollama instance |

See the `ai:` block in `config/configuration.yaml` for examples.

## Make Commands

| Command            | Description                     |
|--------------------|---------------------------------|
| `make dev`         | Setup `.venv` and install deps  |
| `make run`         | Start FastAPI server            |
| `make build`       | Build Python package            |
| `make docker-build`| Build Docker image              |
| `make test`        | Run tests                       |
| `make clean`       | Remove build artifacts          |

---

## Docs

- [Code of conduct](docs/CODE_OF_CONDUCT.md)
- [How to extend / dev guide](docs/DEVELOPER_GUIDE.md)
- [Contributing guide](docs/CONTRIBUTING.md)
- [Coding guidelines](docs/CODING_GUIDELINES.md)
- [Security guidelines](docs/SECURITY.md)
- [Fred deployment stack](https://github.com/ThalesGroup/fred-deployment-factory)

---

Apache 2.0 — © Thales 2025
