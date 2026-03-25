---
name: goodmem:python
description: "Use when the user wants to write Python code that interacts with GoodMem — creating embedders, spaces, memories, retrieval, managing API keys, etc. Provides the complete SDK reference for the goodmem Python package."
user-invocable: false
---

You have access to the GoodMem Python SDK. Use it to write Python code that accomplishes the user's request.

See [reference.md](reference.md) for the complete API reference including all method signatures,
convenience shortcuts, available model identifiers, error handling, and common patterns.

Key principles:
- Context managers recommended: `with Goodmem(...) as client:` (plain construction is fine in short scripts)
- For create methods, pass flat kwargs (convenience transforms handle the rest)
- For update methods, pass either a typed request object or a plain dict
- Use `model_identifier` for embedders/LLMs/rerankers — the SDK auto-infers provider, endpoint, etc.
- Use `api_key="sk-..."` on create (not `credentials`) — the SDK builds the credential struct
- Iterate paginated results directly: `for item in client.spaces.list():`
- Use `stream=False` on retrieve if you want a plain list instead of a stream
- **SaaS endpoints require `api_key`**: creating an embedder/LLM/reranker for a known SaaS provider (OpenAI, Cohere, Voyage, Jina, Anthropic, Google, Mistral) without `api_key` raises `ValueError: Provider '...' at '...' requires an API key.` — always pass `api_key="sk-..."`
