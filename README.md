# GoodMem Claude Code Plugin

A Claude Code plugin for [GoodMem](https://docs.goodmem.ai) — memory infrastructure for AI agents.

With this plugin, you can operate GoodMem's memory infrastructure in plain English — create and manage embedders, rerankers, and LLMs, ingest memories from files, base64 strings, and plain text, and build knowledge-powered agents for RAG and Deep Research. Also includes the full Python SDK reference for writing GoodMem code.

## Use cases

- **Deep Research agent** — Create an embedder and space, ingest research papers and documents, then ask complex questions that retrieve and synthesize information across your entire knowledge base.
- **RAG pipeline** — Configure embedders, rerankers, and LLMs, store source materials as memories, and retrieve relevant context for answering questions.
- **Self-improving support agent** — Ingest historical issue tickets and resolutions, search for solutions matching a new problem description, and iteratively store new discoveries and fixes as memories so future troubleshooting gets smarter over time.

## Installation

**From the official marketplace:**

```
/plugin install goodmem
```

**From this repo:**

```
/plugin marketplace add PAIR-Systems-Inc/goodmem-claude-code-plugin
/plugin install goodmem@goodmem-plugins
```

## Setup

**Option 1: Environment variables** (set before launching Claude Code)

```bash
export GOODMEM_BASE_URL="https://your-server.example.com"
export GOODMEM_API_KEY="gm_..."
```

**Option 2: In-chat configuration** (no env vars needed)

Just tell Claude your server details — it will call `goodmem_configure` automatically:

> "Configure GoodMem with base URL https://my-server.com and API key gm_abc123"

Credentials persist for the session. You can reconfigure anytime to switch servers.

## Reloading after updates

After installing a new version or pulling the latest changes, run `/reload-plugins` inside Claude Code to pick up the updates without restarting.

## What's included

| Component | Description |
|-----------|-------------|
| `skills/help/` | Setup guide, available skills overview, example workflows |
| `skills/python/` | Python SDK reference — method signatures, parameters, examples |
| `skills/mcp/` | MCP tools reference — all 41+ tools with parameters |
| `.mcp.json` | MCP server with auto-inference from 79 model registries |

### Skills

- **`goodmem:help`** — Overview of all skills, setup instructions, example workflows
- **`goodmem:python`** — Python SDK reference for writing GoodMem code
- **`goodmem:mcp`** — MCP tools reference for direct operations

### MCP tools

The MCP server exposes all GoodMem API operations as tools:

- **goodmem_configure** — set server credentials from chat
- **goodmem_lookup_model** — look up model info from the registry (79 models: 29 embedders, 34 LLMs, 16 rerankers)
- **embedders** — create, list, get, update, delete embedding models
- **llms** — create, list, get, update, delete LLM configurations
- **rerankers** — create, list, get, update, delete reranker models
- **spaces** — create, list, get, update, delete memory spaces
- **memories** — create, list, get, update, delete, retrieve, batch operations
- **ocr** — extract text from documents
- **users, apikeys, system, admin** — manage users, API keys, server

### Auto-inference

When creating embedders, LLMs, or rerankers, just provide `model_identifier` and the plugin auto-fills provider, endpoint, dimensions, and other fields from the built-in model registry. You only need to provide `display_name`, `model_identifier`, and credentials — everything else is inferred.

Explicit values always override inferred defaults.

### Credential validation

SaaS providers (OpenAI, Cohere, Voyage, Jina, and OpenAI-compatible endpoints for Anthropic, Google, Mistral) require API credentials. If you create an embedder, LLM, or reranker pointing at a known SaaS hostname without providing credentials, the plugin raises a clear error before the request reaches the server. Pass `credentials` (MCP) or `api_key` (Python SDK) to proceed.

## Links

- [GoodMem Documentation](https://docs.goodmem.ai)
- [Python SDK on PyPI](https://pypi.org/project/goodmem/)
- [MCP Server on npm](https://www.npmjs.com/package/@pairsystems/goodmem-mcp)
