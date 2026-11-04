---
name: goodmem:mcp
description: Workflow guide for GoodMem MCP server tools. Use when an agent needs to understand what GoodMem MCP tools are available and how to use them. Parameter signatures are provided by the MCP protocol itself — do not hardcode them here.
allowed-tools: Read
---

# GoodMem MCP Tools — Workflow Guide

The GoodMem MCP server exposes tools across multiple API namespaces plus local utilities. Most tools map to a GoodMem REST API endpoint; the utilities (`goodmem_configure`, `goodmem_lookup_model`, `goodmem_client_info`) run locally without contacting the server. Use `tools/list` to discover exact parameter schemas — this document covers workflow and patterns only.

**Two servers**: the plugin provides `goodmem` (all tools on the user's own instance, local or remote — the namespaces below) and `goodmem-gateway` (GoodMem Cloud through the hosted gateway, OAuth sign-in). Connection checks, the first-use message, and the rules for choosing between them are in `goodmem:help` — follow those before the first operation. The gateway section at the end of this document covers its differences.

**Setup for `goodmem`**: needs `GOODMEM_BASE_URL` and `GOODMEM_API_KEY`, set as environment variables before launch or from chat via `goodmem_configure`. For localhost, the server should run with TLS disabled and be reached over `http://`. For a remote server with a private or self-signed CA, export `NODE_EXTRA_CA_CERTS` with the absolute path of its PEM certificate file before launching Claude Code, and restart Claude Code after changing it. An expired or invalid server certificate must be fixed on the server.

---

## Typical workflow

1. **Configure** — check the connection with two calls that need no existing data: `goodmem_system_info` (no key; "not configured" → get the base URL and API key from the user, call `goodmem_configure`, and check again) then `goodmem_instance_get` (401 → key missing or invalid; 403 → valid scoped key, proceed with the requested operation and let it decide). Do not use `goodmem_users_me` as the check: service-identity keys have no user profile (404) and scoped keys may lack user-read authority (403) while still being fully usable for their purpose.
2. **Register providers** — create embedder, LLM, and optionally reranker. Use `goodmem_lookup_model` to check the model registry before creating — it auto-infers provider, endpoint, and dimensionality for known models.
3. **Create a space** — a space binds an embedder and chunking config. Memories ingested into a space are automatically chunked and embedded.
4. **Ingest memories** — use `goodmem_memories_create` (single) or `goodmem_memories_batch_create` (bulk). Supports text, base64-encoded files, or URL references.
5. **Wait for processing** — after ingestion, memories are processed asynchronously. Poll with `goodmem_memories_get` until `processingStatus` is `COMPLETED`.
6. **Retrieve** — `goodmem_memories_retrieve` performs semantic search. Returns NDJSON with ranked results. Optionally rerank the results and generate an answer with an LLM — see *Reranking and LLM answers in retrieval*.

---

## Namespaces

### Embedders (`goodmem_embedders_*`)
Register and manage embedding models. The four SaaS provider types (OpenAI, Cohere, Voyage, Jina) require `credentials`. OpenAI-compatible endpoints (Anthropic, Google, Mistral) also require credentials when used under the `OPENAI` provider type. Omitting credentials for a known SaaS endpoint throws an error before the request is sent.

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
- `pages` — list memory page images with optional filters and pagination
- `content` — download the original memory bytes (text, image, PDF, etc.)
- `pages_image` — download one rendered page image as bytes

**Binary delivery and size cap** — `content` and `pages_image` return raw
bytes, wrapped in the appropriate MCP content block:

- `image/*` MIMEs → MCP `image` block (base64 + `mimeType`). Claude
  reads these as vision input directly.
- `text/*` and `application/json` → MCP embedded `resource` block with
  `text` + `mimeType`. Preserves MIME signaling for markdown, source
  code, JSON.
- Other binary (PDF, octet-stream, etc.) → embedded `resource` block
  with `blob` + `mimeType`. Claude cannot natively decode the bytes
  today (PDF understanding goes through the page-image path); the
  block is delivered for forward compatibility and host-side use.

Both tools accept an optional `max_inline_bytes` parameter. Defaults
to **8 MB** when unset; the server's absolute ceiling is **64 MB**.
If the requested content exceeds your cap, the tool errors with the
actual size — retry with a larger `max_inline_bytes` (up to 64 MB)
to receive it inline. Above 64 MB, fetch via REST instead.

### Reranking and LLM answers in retrieval

`goodmem_memories_retrieve` can rerank results and generate an answer from them. Pass a `post_processor` that uses the built-in chat post-processor:

```json
"post_processor": {
  "name": "com.goodmem.retrieval.postprocess.ChatPostProcessorFactory",
  "config": { "reranker_id": "<reranker UUID>", "llm_id": "<LLM UUID>", "max_results": 5 }
}
```

- Get IDs from `goodmem_rerankers_list` and `goodmem_llms_list`. Either works alone: `reranker_id` reorders the results, `llm_id` adds a generated answer.
- Set `requested_size` above `max_results` (for example 20 and 5) so the reranker has candidates to choose from.
- Optional config keys: `max_results`, `relevance_threshold` (reranker only), `llm_temp` (0.0–2.0, default 0.3), `gen_token_budget`, `prompt`, `sys_prompt`, `chronological_resort` (default false).
- Defaults that are easy to get wrong — set these explicitly when the result count or answer length matters:
  - `max_results` omitted → the request's `requested_size` is used; 10 only when `requested_size` is also unset. So `requested_size: 20` with no `max_results` returns up to 20.
  - Answer token budget precedence: the request's `output_budget.tokens`, then `gen_token_budget`, then the LLM's configured `max_tokens`, then 512.
- Reranked chunks carry the reranker's `relevanceScore`. The generated answer arrives as a final `abstractReply` event with `text`.
- If the LLM call fails — for example the provider account is out of credits — the final event is `status` with code `SUMMARIZATION_FAILED` and the provider's message. The reranked chunks are still valid: report the error and answer from the chunks.

### OCR (`goodmem_ocr_*`)
- `document` — extract text from a document using OCR

### Ping (`goodmem_ping_*`)
Connectivity probes for embedders, LLMs, rerankers, and other GoodMem endpoints.

- `once` — run one probe and return a `PingResult`
- `stream` — run streaming probes and return NDJSON ping events

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
- `goodmem_configure` — set base URL and API key from chat (`goodmem` server only)
- `goodmem_lookup_model` — look up model registry entries before creating embedders/LLMs/rerankers
- `goodmem_client_info` — return MCP client version and the goodmem server commit it was built against

---

## `goodmem-gateway` — GoodMem Cloud

The gateway connects to the GoodMem Cloud instance the user chose at sign-in. It exposes a curated tool set, not the full API above: spaces (`list`, `get`, `create`, `update`), memories (`create`, `upload`, `list`, `get`, `content`, `pages`, `retrieve`, `delete`), `goodmem_embedders_list`, `goodmem_rerankers_list`, `goodmem_llms_list`, `goodmem_console_setup`, `goodmem_users_me`, `goodmem_ping`, and generic `search` / `fetch`.

- **Identity:** every gateway call acts with the instance's root authority, not the signed-in user's permissions, so `goodmem_users_me` returns the root user; the gateway is intended for single-owner instances until per-user identity ships (goodmem-cloud-provisioning#5455).
- **Never ask for an API key or URL.** If tools fail with an authorization error, tell the user to run `/mcp` → **goodmem-gateway** → **Authenticate**.
- **Model setup is a console link.** Call `goodmem_console_setup` with `kind`: `quick_start` (first-time setup — embedder, chat model or reranker, and an optional first space), `embedder`, `reranker`, or `llm`. Relay the link verbatim: it works once, expires after 30 minutes, and a new link invalidates the previous one. When the user is done, retry what needed the model. Use the `*_list` tools to see what is configured. Never create models with tools or write code for this.
- **Reranking and LLM answers:** `goodmem_memories_retrieve` reranks automatically with the first reranker listed by `goodmem_rerankers_list`; there is no per-query reranker or LLM choice. `answer: true` adds a synthesized answer from the first LLM listed by `goodmem_llms_list` (requires one; slower). `requested_size` is 1–20 (default 6). To pick a specific reranker or LLM per query, use `goodmem`.
- **Report problems in the response:** `reranker_error` (results fell back to embedder order), `synthesis_error` (answer from the returned passages instead), `failed_count` (memories that never finished processing — results are incomplete), `warnings`, and `skipped_spaces`.
- **Search:** prefer `goodmem_memories_retrieve` — it supports space scoping, metadata filters, and answers — over the generic `search` / `fetch`. `fetch` returns the first page of a memory's text; continue with `goodmem_memories_content` and `next_offset`.
- **Files:** `goodmem_memories_upload` saves an original document as one memory, but it needs a public HTTPS download URL for the file. For a local file, save it through `goodmem` (`goodmem_memories_create` with `original_content_b64` and `content_type`), or save extracted text with `goodmem_memories_create` here. Do not transcribe a document page by page.
- **Spaces:** `goodmem_spaces_create` picks the embedder automatically only when the instance has exactly one. With several, it returns the options; ask the user which to use and pass it as `embedder_name`. If it reports that no embedder exists, relay its setup link. Spaces cannot be deleted through the gateway: deleting a space is done in the GoodMem Cloud console (https://cloud.goodmem.ai). If the user asks, say so; do not look for another tool.
