# GoodMem Claude Code Plugin

A Claude Code plugin for [GoodMem](https://docs.goodmem.ai) — memory infrastructure for AI agents.

## What it does

This plugin provides two ways to work with GoodMem from Claude Code:

- **Python SDK skills** — Claude writes Python code using the GoodMem SDK, guided by the full API reference. Use this when building applications that integrate with GoodMem.
- **MCP tools** — Claude calls GoodMem APIs directly via natural language. Use this to create embedders, store memories, run retrieval, and manage resources without writing code.

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

Set your GoodMem server credentials as environment variables:

```bash
export GOODMEM_BASE_URL="https://your-server.example.com"
export GOODMEM_API_KEY="gm_..."
```

The MCP tools use these to connect to your GoodMem server. The Python SDK skill works without them (it teaches Claude how to write SDK code, not call APIs directly).

## What's included

| Component | Description |
|-----------|-------------|
| `skills/python/` | Python SDK reference — method signatures, parameters, examples |
| `.mcp.json` | MCP server config — 41 tools across 10 namespaces |

### MCP tools

The MCP server exposes all GoodMem API operations as tools:

- **embedders** — create, list, get, update, delete embedding models
- **llms** — create, list, get, update, delete LLM configurations
- **rerankers** — create, list, get, update, delete reranker models
- **spaces** — create, list, get, update, delete memory spaces
- **memories** — create, list, get, update, delete, retrieve, batch operations
- **ocr** — extract text from documents
- **users** — manage users
- **apikeys** — manage API keys
- **system** — server info, initialization
- **admin** — background jobs, drain, license management

## Links

- [GoodMem Documentation](https://docs.goodmem.ai)
- [Python SDK on PyPI](https://pypi.org/project/goodmem/)
- [MCP Server on npm](https://www.npmjs.com/package/@pairsystems/goodmem-mcp)
