---
name: goodmem:java
description: "Use when the user wants to write Java code that interacts with GoodMem - creating embedders, spaces, memories, retrieval, pagination, streaming, or async workflows with the goodmem-java SDK."
user-invocable: false
---

You have access to the GoodMem Java SDK. Use it to write Java code that accomplishes the user's request.

See [reference.md](reference.md) for install instructions, common request builders, streaming,
pagination, async usage, typed IDs, and end-to-end snippets.

Key principles:
- Use `Goodmem.builder().baseUrl(...).apiKey(...).build()` and prefer try-with-resources.
- Use `AsyncGoodmem` when the user asks for async code; async methods return `CompletableFuture<T>`.
- Import request/response records from `ai.pairsys.goodmem.client.models`.
- Use request builders for creates and updates, for example `EmbedderCreationRequest.builder()...build()`.
- For SaaS providers, pass the provider API key to create calls, for example `client.embedders.create(request, openaiApiKey)`.
- Use `modelIdentifier(...)` for embedders, LLMs, and rerankers; the SDK auto-infers provider details.
- Preserve typed handles such as `SpaceId`, `MemoryId`, `EmbedderId`, `LlmId`, and `RerankerId`.
- Create spaces with `List.of(new SpaceEmbedderConfig(embedderId, null))`.
- Iterate paginated results directly with `Page<T>` or `AsyncPage<T>`; list option `maxResults` takes an integer page size.
- Use try-with-resources for streaming types such as `RetrieveMemoryStream` and `PingStream`.
- Use the file-upload convenience `client.memories.create(spaceId, Path.of(...))` instead of manual base64 encoding.
- Compare typed enums directly, for example `status == MemoryProcessingStatus.COMPLETED`.
