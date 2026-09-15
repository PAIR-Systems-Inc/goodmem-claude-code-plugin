---
name: goodmem:help
description: Overview of all available GoodMem skills and what a user needs to get started. Invoke when a user asks what GoodMem skills are available, how to get started, or what they need to set up.
allowed-tools: Skill, Bash, Read
---

# GoodMem Plugin — Help & Overview

GoodMem is memory infrastructure for AI agents — store, retrieve, and manage memories with vector embeddings, semantic search, and RAG.

## Credential Setup

Before calling any GoodMem MCP tool, you MUST ensure credentials are configured. Follow this sequence:

1. Try calling `goodmem_system_info` to check if credentials are already set (from environment variables).
2. If it fails with a connection or auth error, ask the user for:
   - **Base URL** — their GoodMem server address (e.g., `https://your-server.example.com`)
   - **API key** — starts with `gm_`
3. Call `goodmem_configure` with the provided `base_url` and `api_key`.
4. Confirm the connection succeeded before proceeding.

Credentials persist for the entire session. The user can call `goodmem_configure` again to switch servers.

If the user has set `GOODMEM_BASE_URL` and `GOODMEM_API_KEY` environment variables before starting Claude Code, credentials are picked up automatically — no setup needed.

**TLS errors?** For a private or self-signed CA, tell the user to set `NODE_EXTRA_CA_CERTS` to the absolute path of its PEM certificate file before launching Claude Code, then restart the MCP connection. Certificate errors can also indicate an expired or invalid server certificate; those must be fixed on the server.

## Available Skills

### `goodmem:mcp` — MCP Tools Reference
Reference for all GoodMem MCP tools. Use this when you need to look up tool names, parameters, or behavior. The MCP tools let you operate GoodMem directly — create embedders, store memories, run retrieval — all via natural language.

### `goodmem:python` — Python SDK Reference
Complete API reference for the `goodmem` Python package. Use this when writing Python code that integrates with GoodMem. Includes method signatures, convenience shortcuts, model identifiers, and code examples.

### `goodmem:java` — Java SDK Reference
Usage reference for the `ai.pairsys:goodmem-java` package. Use this when writing Java code that integrates with GoodMem. Includes client setup, request builders, typed IDs, streaming, pagination, async usage, and common RAG patterns.

### `goodmem:help` — This skill
Overview and setup instructions.

## Three Ways to Use GoodMem

### 1. Direct operations (MCP tools)
Ask Claude to perform GoodMem operations in natural language. Claude calls MCP tools behind the scenes.

Examples:
- "Create an OpenAI embedder called 'my-embedder' using text-embedding-3-large"
- "Create a space called 'knowledge-base' using that embedder"
- "Store this text as a memory in the knowledge-base space"
- "Search my knowledge-base for information about authentication"
- "List all my spaces"

### 2. Python code generation (SDK skill)
Ask Claude to write Python code using the GoodMem SDK.

Examples:
- "Write a Python script that creates an embedder and stores some documents"
- "Show me how to do semantic retrieval with the GoodMem SDK"
- "Write a RAG pipeline using GoodMem for memory storage"

### 3. Java code generation (SDK skill)
Ask Claude to write Java code using the GoodMem SDK.

Examples:
- "Write a Java program that creates an embedder and stores documents"
- "Show me Java streaming retrieval with the GoodMem SDK"
- "Write a Java RAG pipeline using GoodMem with typed request builders"

## Common Workflows

### Quick start with MCP
1. "Create an embedder using text-embedding-3-large with my OpenAI key"
2. "Create a space called 'docs' using that embedder"
3. "Store this text as a memory: [your content]"
4. "Search docs for [your query]"

### Build a RAG app with an SDK
1. "Write a Python or Java script that sets up a GoodMem RAG pipeline"
2. Claude generates code using the `goodmem` Python package or `ai.pairsys:goodmem-java`
3. Run the generated script
