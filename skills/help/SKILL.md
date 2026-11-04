---
name: goodmem:help
description: Overview of all available GoodMem skills and what a user needs to get started. Invoke when a user asks what GoodMem skills are available, how to get started, or what they need to set up.
allowed-tools: Skill, Bash, Read
---

# GoodMem Plugin — Help & Overview

GoodMem is memory infrastructure for AI agents — store, retrieve, and manage memories with vector embeddings, semantic search, and RAG.

## Connecting

The plugin provides two MCP servers. Tool names are prefixed by server, so you can tell them apart:

| Server | Tool prefix | Connects to | Access |
|--------|-------------|-------------|--------|
| `goodmem` | `mcp__plugin_goodmem_goodmem__` | The user's own GoodMem instance, local or remote | All tools — search plus full control over spaces, memories, models, users, and API keys |
| `goodmem-gateway` | `mcp__plugin_goodmem_goodmem-gateway__` | The user's instance on GoodMem Cloud | Search and read, save memories, save documents by URL, delete memories, create and rename spaces; models and administration via the Cloud console |

### Check what is connected

Before the first GoodMem operation in a session:

- **`goodmem`**: two calls that need no spaces or memories to exist.
  1. `goodmem_system_info` — needs no key. "Not configured" → no credentials yet; offer the choices below. A connection error → the base URL is wrong or the server is down.
  2. `goodmem_instance_get` — checks the key. Success → connected. 401 → the key is missing or invalid; ask the user to check it. 403 → the key is valid but scoped (for example to one space); the connection works, so go ahead with the operation the user asked for and let that call decide.
  - Never use `goodmem_users_me` as the check. It looks up a human user profile: a service-identity key gets 404 and a scoped key may get 403 even though both can use GoodMem normally. Call it only when the user asks who they are.
- **`goodmem-gateway`**: if none of its tools are available, the user has not signed in or the gateway could not be reached; check `/mcp` for its status before asking them to authenticate.

### Nothing connected — offer the choices

Tell the user, in your own words:

> GoodMem isn't connected yet. Pick how you want to connect:
>
> 1. **Your own instance, local or remote (`goodmem`)** — all tools, with full control over spaces, memories, models, users, and API keys. Give me the server URL and a `gm_` API key, or set `GOODMEM_BASE_URL` and `GOODMEM_API_KEY` before starting Claude Code.
> 2. **GoodMem Cloud (`goodmem-gateway`)** — sign in through your browser. Requires a GoodMem Cloud account with an instance. Run `/mcp`, select **goodmem-gateway**, and choose **Authenticate**.

For option 1, call `goodmem_configure` with the `base_url` and `api_key`, then run the check above (a 403 from `goodmem_instance_get` still counts as connected). Credentials last for the session. `goodmem_configure` only affects the `goodmem` server — never use it for the gateway.

### Choosing a server when both are connected

- If the user names a target ("my local server", "cloud", a URL or instance), use that server.
- If only one is connected, use it and say which in one line.
- If both are connected and the request is ambiguous, ask once which one, then keep using it for the session.
- If the user asks for model setup or administration on the gateway, explain that those happen in the Cloud console and offer the console link. Deleting a space is also console-only on the gateway; on `goodmem` it is `goodmem_spaces_delete`.

### Server-specific rules

- **Gateway:** never ask for an API key or URL. Model setup (embedder, reranker, LLM) is a one-time GoodMem Cloud console link from `goodmem_console_setup` — relay it verbatim; do not create models with tools or code. If tools fail with an authorization error, tell the user to run `/mcp` → **goodmem-gateway** → **Authenticate** again.
- **Identity on the gateway:** calls act with the instance's root authority, not the signed-in user's own GoodMem permissions; `goodmem_users_me` returns the root user, which is expected. The gateway is intended for single-owner instances until per-user identity ships (goodmem-cloud-provisioning#5455). If the user asks who they are or about permissions, say this plainly.
- **Rerankers and LLMs:** on `goodmem`, register them with `goodmem_rerankers_create` / `goodmem_llms_create` (check `goodmem_lookup_model` first) and apply them in retrieval through `post_processor`. On the gateway, add them through the console link; searches rerank automatically with the first reranker listed by `goodmem_rerankers_list`, and `answer: true` generates an answer with the first LLM listed by `goodmem_llms_list`. Parameters are in `goodmem:mcp`.
- **TLS errors on `goodmem`:** for localhost, the server should run with TLS disabled and be reached over `http://localhost:8080`. For a remote server with a private or self-signed CA, the user exports `NODE_EXTRA_CA_CERTS` with the absolute path of its PEM file before launching Claude Code and restarts Claude Code after changing it. Expired or invalid certificates must be fixed on the server.

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
- "Search docs for our refund policy, rerank the results, and answer with my LLM"
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
