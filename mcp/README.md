# @pairsystems/goodmem-mcp

[GoodMem](https://goodmem.ai/) MCP server — gives AI agents direct access to GoodMem memory infrastructure via the [Model Context Protocol](https://modelcontextprotocol.io).

41 tools across 10 namespaces: embedders, LLMs, rerankers, spaces, memories, retrieval, OCR, users, API keys, and system administration.

## Prerequisites

- A running [GoodMem](https://github.com/PAIR-Systems-Inc/goodmem) server
- Node.js 18+

## Installation

### Claude Desktop

Add to `~/Library/Application Support/Claude/claude_desktop_config.json` (macOS) or `%APPDATA%\Claude\claude_desktop_config.json` (Windows):

```json
{
  "mcpServers": {
    "goodmem": {
      "command": "npx",
      "args": ["-y", "@pairsystems/goodmem-mcp"],
      "env": {
        "GOODMEM_BASE_URL": "https://your-server.example.com",
        "GOODMEM_API_KEY": "gm_..."
      }
    }
  }
}
```

### Claude Code

```bash
claude mcp add goodmem -- env GOODMEM_BASE_URL=https://your-server.example.com env GOODMEM_API_KEY=gm_... npx -y @pairsystems/goodmem-mcp
```

Or add to `.claude/mcp.json` in your project:

```json
{
  "mcpServers": {
    "goodmem": {
      "command": "npx",
      "args": ["-y", "@pairsystems/goodmem-mcp"],
      "env": {
        "GOODMEM_BASE_URL": "https://your-server.example.com",
        "GOODMEM_API_KEY": "gm_..."
      }
    }
  }
}
```

### VS Code / Cursor / Other MCP clients

Use the same `npx -y @pairsystems/goodmem-mcp` command pattern with `GOODMEM_BASE_URL` and `GOODMEM_API_KEY` set in the environment.

### Global install

```bash
npm install -g @pairsystems/goodmem-mcp
goodmem-mcp
```

## Runtime configuration

If you can't set environment variables before launch, call `goodmem_configure` from chat:

```
Configure GoodMem with base URL https://my-server.com and API key gm_abc123
```

Credentials set this way persist for the session and override environment variables.

## Quick start

Once connected, ask your AI assistant to:

```
Create a text-embedding-3-large embedder called "My Embedder" with credentials <sk-...>
Create a space called "Research" using that embedder
Store this text as a memory: "GoodMem is a memory infrastructure platform for AI agents"
Search my Research space for "memory infrastructure"
```

The MCP server auto-infers provider, endpoint, dimensions, and other fields from the model name — you only need `display_name`, `model_identifier`, and credentials for the embedding provider.

## Available tools

### `goodmem_configure`
Set server credentials at runtime. Call this if `GOODMEM_BASE_URL` / `GOODMEM_API_KEY` are not set as environment variables.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `base_url` | string | yes | GoodMem server URL |
| `api_key` | string | yes | GoodMem API key (`gm_...`) |

### `goodmem_lookup_model`
Inspect the built-in model registry. Shows what fields will be auto-inferred for a given model identifier.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `model_identifier` | string | yes | Model name to look up |
| `type` | string | no | `embedder`, `llm`, or `reranker` |

---

### Embedders

| Tool | Description |
|------|-------------|
| `goodmem_embedders_create` | Register an embedding model |
| `goodmem_embedders_list` | List registered embedders |
| `goodmem_embedders_get` | Get embedder by ID |
| `goodmem_embedders_update` | Update embedder configuration |
| `goodmem_embedders_delete` | Delete an embedder |

**Create parameters**: `display_name` (required), `model_identifier` (required), `credentials` (required for SaaS providers), `provider_type`, `endpoint_url`, `dimensionality` — last three auto-inferred from `model_identifier` for 29 known models.

### LLMs

| Tool | Description |
|------|-------------|
| `goodmem_llms_create` | Register an LLM configuration |
| `goodmem_llms_list` | List registered LLMs |
| `goodmem_llms_get` | Get LLM by ID |
| `goodmem_llms_update` | Update LLM configuration |
| `goodmem_llms_delete` | Delete an LLM |

**Create parameters**: `display_name` (required), `model_identifier` (required), `credentials` (required for SaaS providers) — `provider_type`, `endpoint_url`, `max_context_length` auto-inferred for 34 known models.

### Rerankers

| Tool | Description |
|------|-------------|
| `goodmem_rerankers_create` | Register a reranker model |
| `goodmem_rerankers_list` | List registered rerankers |
| `goodmem_rerankers_get` | Get reranker by ID |
| `goodmem_rerankers_update` | Update reranker configuration |
| `goodmem_rerankers_delete` | Delete a reranker |

**Create parameters**: `display_name` (required), `model_identifier` (required), `credentials` (required for SaaS providers) — `provider_type` and `endpoint_url` auto-inferred for 16 known models.

### Spaces

Memory spaces are containers that associate a set of memories with an embedder.

| Tool | Description |
|------|-------------|
| `goodmem_spaces_create` | Create a memory space |
| `goodmem_spaces_list` | List spaces |
| `goodmem_spaces_get` | Get space by ID |
| `goodmem_spaces_update` | Update space configuration |
| `goodmem_spaces_delete` | Delete a space |

### Memories

| Tool | Description |
|------|-------------|
| `goodmem_memories_create` | Store a memory (text, base64, or file reference) |
| `goodmem_memories_list` | List memories in a space |
| `goodmem_memories_get` | Get memory by ID |
| `goodmem_memories_update` | Update memory metadata |
| `goodmem_memories_delete` | Delete a memory |
| `goodmem_memories_retrieve` | **Semantic search** — query memories by meaning |
| `goodmem_memories_batch_create` | Create multiple memories in one request |
| `goodmem_memories_batch_get` | Get multiple memories by IDs |
| `goodmem_memories_batch_delete` | Delete multiple memories by IDs |

**`goodmem_memories_retrieve` key parameters**: `space_keys` (required), `query` (required), `llm_id` (optional, for RAG), `reranker_id` (optional), `max_results`, `relevance_threshold`.

### OCR

| Tool | Description |
|------|-------------|
| `goodmem_ocr_document` | Extract text from a document |

### Users

| Tool | Description |
|------|-------------|
| `goodmem_users_me` | Get current authenticated user |
| `goodmem_users_get` | Get user by ID or email |

### API Keys

| Tool | Description |
|------|-------------|
| `goodmem_apikeys_create` | Create an API key |
| `goodmem_apikeys_list` | List API keys |
| `goodmem_apikeys_update` | Update an API key |
| `goodmem_apikeys_delete` | Delete an API key |

### System

| Tool | Description |
|------|-------------|
| `goodmem_system_info` | Get server version and configuration |
| `goodmem_system_init` | Initialize the server (first-time setup) |

### Admin

| Tool | Description |
|------|-------------|
| `goodmem_admin_drain` | Drain the server |
| `goodmem_admin_background_jobs_purge` | Purge completed background jobs |
| `goodmem_admin_license_reload` | Reload the server license |

---

## Auto-inference

When creating embedders, LLMs, or rerankers, provide `model_identifier` and the server fills in `provider_type`, `endpoint_url`, dimensions, and other fields automatically from the built-in registry of 79 models.

**Example**: calling `goodmem_embedders_create` with `model_identifier: "text-embedding-3-large"` auto-fills:
- `provider_type` → `"OPENAI"`
- `endpoint_url` → `"https://api.openai.com/v1"`
- `dimensionality` → `1536`
- `distribution_type` → `"DENSE"`

User-provided values always override inferred defaults. Use `goodmem_lookup_model` to inspect what will be inferred before creating a resource.

## Credential validation

SaaS providers require API credentials. If you call a create tool for a known SaaS endpoint (OpenAI, Cohere, Voyage, Jina, Anthropic via OpenAI-compatible API, Google, Mistral) without providing `credentials`, the server returns a clear error before the request is sent — no wasted round trips.

For self-hosted or local providers (vLLM, TEI, Ollama, custom endpoints), credentials are optional.

## Links

- [GoodMem Documentation](https://docs.goodmem.ai)
- [GoodMem on GitHub](https://github.com/PAIR-Systems-Inc/goodmem)
- [Python SDK on PyPI](https://pypi.org/project/goodmem/)
- [Claude Code Plugin](https://github.com/PAIR-Systems-Inc/goodmem-claude-code-plugin)
