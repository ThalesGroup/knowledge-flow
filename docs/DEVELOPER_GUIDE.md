# Developer Guide – Knowledge Flow Backend

This guide explains how to understand, extend, and contribute to the Knowledge Flow microservice.

---

## 🧩 Processor Architecture

### Input Processors

Input processors extract structured content and metadata from uploaded files.

| Type     | Location                     | Output        |
|----------|------------------------------|---------------|
| Markdown | `input_processors/`          | Markdown text |
| Tabular  | `input_processors/`          | Table rows    |

Each input processor specializes in a file type (PDF, DOCX, CSV, etc.).

### Output Processors

Output processors transform parsed content into embeddings or structured records.

| Type         | Location                       | Output       |
|--------------|--------------------------------|--------------|
| Vectorization| `output_processors/vectorization_processor/` | Embeddings + metadata |
| Tabular      | `output_processors/tabular_processor/`       | Normalized records    |

---

## 🔄 Vectorization Pipeline

```txt
[ FILE PATH + METADATA ]
          │
          ▼
  DocumentLoaderInterface
          │
          ▼
   TextSplitterInterface
          │
          ▼
  EmbeddingModelInterface
          │
          ▼
   VectorStoreInterface
          │
          ▼
   BaseMetadataStore
```

Each interface is pluggable. You can switch OpenSearch → Pinecone, or Azure → HuggingFace by updating config and implementing the interface.

---

## 🗂 Project Layout

```text
knowledge_flow_app/
├── main.py                # FastAPI entrypoint
├── config/                # configuration.yaml + model settings
├── controllers/           # API routers
├── services/              # Orchestration logic
├── input_processors/      # File-to-content logic
├── output_processors/     # Content-to-storage logic
├── stores/                # Storage interfaces
├── common/                # Shared utilities and types
└── tests/                 # Unit + integration tests
```

---

## 🧑‍💻 Developer Tasks

| Task                      | Where to implement               |
|---------------------------|----------------------------------|
| Add new file type         | `input_processors/`              |
| Add new vector backend    | `output_processors/vectorization_processor/` |
| Add custom storage        | `stores/`                        |
| Expose new route          | `controllers/`                   |
| Add orchestration logic   | `services/`                      |

---

## 🧪 Testing

```bash
make test
```

Use standard `pytest`. Tests live in `tests/`, and you can run individual files with:

```bash
pytest tests/test_ingestion.py
```

---

## 📦 Custom Configuration

- See [`config/configuration.yaml`](../config/configuration.yaml)
- Set environment variables in `.env` (based on `.env.template`)
- Configure AI backend in the `ai:` block (OpenAI, Azure, Ollama)

---

## 🔁 Dev loop

```bash
make dev         # setup .venv
make run         # run the API
make test        # run tests
```

Swagger UI: [http://localhost:8111/knowledge/v1/docs](http://localhost:8111/knowledge/v1/docs)

---

## 👥 Contributions

Follow our [coding guidelines](./CODING_GUIDELINES.md) and submit PRs or issues on GitHub.

---
