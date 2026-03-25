---
name: goodmem:mcp
description: Workflow guide for GoodMem MCP server tools. Use when an agent needs to understand what GoodMem MCP tools are available and how to use them. Parameter signatures are provided by the MCP protocol itself — do not hardcode them here.
allowed-tools: Read
---

# GoodMem MCP Tools — Workflow Guide

The GoodMem MCP server exposes tools across 10 namespaces. Each tool maps directly to a GoodMem REST API endpoint. Use `tools/list` to discover exact parameter schemas — this document covers workflow and patterns only.

**Setup**: The MCP server needs `GOODMEM_BASE_URL` and `GOODMEM_API_KEY`. These can be set as environment variables before launch, or configured from chat via `goodmem_configure`.

**TLS**: If the server uses self-signed or private CA certificates, set `NODE_EXTRA_CA_CERTS=/path/to/rootCA.pem` or `NODE_TLS_REJECT_UNAUTHORIZED=0` (local dev only) as an environment variable before launch.

---

## Typical workflow

1. **Configure** — call `goodmem_configure` if credentials weren't set via env vars.
2. **Register providers** — create embedder, LLM, and optionally reranker. Use `goodmem_lookup_model` to check the model registry before creating — it auto-infers provider, endpoint, and dimensionality for known models.
3. **Create a space** — a space binds an embedder and chunking config. Memories ingested into a space are automatically chunked and embedded.
4. **Ingest memories** — use `goodmem_memories_create` (single) or `goodmem_memories_batch_create` (bulk). Supports text, base64-encoded files, or URL references.
5. **Wait for processing** — after ingestion, memories are processed asynchronously. Poll with `goodmem_memories_get` until `status` is `ACTIVE`.
6. **Retrieve** — `goodmem_memories_retrieve` performs semantic search. Returns NDJSON with ranked results.

---

## Namespaces

### Embedders (`goodmem_embedders_*`)
Register and manage embedding models. SaaS providers (OpenAI, Cohere, Voyage, Jina, Anthropic, Google, Mistral) require `credentials`. Omitting credentials for a known SaaS endpoint throws an error before the request is sent.

CRUD: `create`, `list`, `get`, `update`, `delete`.

### LLMs (`goodmem_llms_*`)
Register and manage LLM configurations. Same credential pattern as embedders.

CRUD: `create`, `list`, `get`, `update`, `delete`.

### Rerankers (`goodmem_rerankers_*`)
Register and manage reranker models for result re-ranking.

CRUD: `create`, `list`, `get`, `update`, `delete`.

### Spaces (`goodmem_spaces_*`)
Memory spaces — containers that bind an embedder and chunking config.

CRUD: `create`, `list`, `get`, `update`, `delete`.

### Memories (`goodmem_memories_*`)
Store, retrieve, and manage memories within spaces.

- `create` / `batch_create` — ingest content (text, base64, or URL reference)
- `retrieve` — semantic search across one or more spaces (returns NDJSON)
- `get` / `batch_get` — fetch by ID
- `list` — list memories in a space
- `delete` / `batch_delete` — remove memories
- `pages` — get page metadata for a processed document

*Not available via MCP (binary response)*: `content`, `pages_image`.

### OCR (`goodmem_ocr_*`)
- `document` — extract text from a document using OCR

### Users (`goodmem_users_*`)
- `me` — get the current authenticated user
- `get` — get a user by ID or email

### API Keys (`goodmem_apikeys_*`)
Manage API keys for authentication.

CRUD: `create`, `list`, `update`, `delete`.

### System (`goodmem_system_*`)
- `info` — server version and configuration
- `init` — first-time server initialization

### Admin (`goodmem_admin_*`)
- `drain` — request the server to enter drain mode
- `background_jobs_purge` — purge completed background jobs
- `license_reload` — reload the server license

### Utilities
- `goodmem_configure` — set base URL and API key from chat
- `goodmem_lookup_model` — look up model registry entries before creating embedders/LLMs/rerankers
