# GoodMem Java SDK Reference

Use this reference when writing Java code with `ai.pairsys:goodmem-java`.

## Installation

Gradle:

```kotlin
dependencies {
    implementation("ai.pairsys:goodmem-java:0.1.3")
}
```

Maven:

```xml
<dependency>
  <groupId>ai.pairsys</groupId>
  <artifactId>goodmem-java</artifactId>
  <version>0.1.3</version>
</dependency>
```

Requires JDK 21.

## Client Setup

```java
import ai.pairsys.goodmem.client.Goodmem;

try (Goodmem client = Goodmem.builder()
        .baseUrl(System.getenv("GOODMEM_BASE_URL"))
        .apiKey(System.getenv("GOODMEM_API_KEY"))
        .build()) {
    System.out.println(client.system.info());
}
```

The async sibling is `AsyncGoodmem` and returns `CompletableFuture<T>`:

```java
import ai.pairsys.goodmem.client.AsyncGoodmem;

try (AsyncGoodmem client = AsyncGoodmem.builder()
        .baseUrl(System.getenv("GOODMEM_BASE_URL"))
        .apiKey(System.getenv("GOODMEM_API_KEY"))
        .build()) {
    client.system.info().thenAccept(System.out::println).join();
}
```

## Core Imports

```java
import ai.pairsys.goodmem.client.Goodmem;
import ai.pairsys.goodmem.client.Page;
import ai.pairsys.goodmem.client.RetrieveMemoryStream;
import ai.pairsys.goodmem.client.models.*;

import java.nio.file.Path;
import java.util.List;
```

## Create Embedders, LLMs, And Rerankers

Use `modelIdentifier(...)` plus the provider API key overload. The SDK infers provider, endpoint, dimensions, and other registry-backed defaults.

```java
String openaiApiKey = System.getenv("OPENAI_API_KEY");

EmbedderResponse embedder = client.embedders.create(
    EmbedderCreationRequest.builder()
        .displayName("OpenAI Embedder")
        .modelIdentifier("text-embedding-3-large")
        .build(),
    openaiApiKey);
EmbedderId embedderId = embedder.embedderId();

CreateLLMResponse llm = client.llms.create(
    LLMCreationRequest.builder()
        .displayName("GPT")
        .modelIdentifier("gpt-5.1")
        .build(),
    openaiApiKey);
LlmId llmId = llm.llm().llmId();
```

Rerankers follow the same pattern:

```java
String voyageApiKey = System.getenv("VOYAGE_API_KEY");

RerankerResponse reranker = client.rerankers.create(
    RerankerCreationRequest.builder()
        .displayName("Voyage Reranker")
        .modelIdentifier("rerank-2.5")
        .build(),
    voyageApiKey);
RerankerId rerankerId = reranker.rerankerId();
```

## Create Spaces

```java
Space space = client.spaces.create(
    SpaceCreationRequest.builder()
        .name("knowledge-base")
        .spaceEmbedders(List.of(new SpaceEmbedderConfig(embedderId, null)))
        .build());
SpaceId spaceId = space.spaceId();
```

## Create Memories

Plain text:

```java
Memory memory = client.memories.create(
    JsonMemoryCreationRequest.builder()
        .spaceId(spaceId)
        .originalContent("GoodMem stores and retrieves memories for RAG.")
        .contentType("text/plain")
        .build());
MemoryId memoryId = memory.memoryId();
```

File upload:

```java
Memory pdf = client.memories.create(spaceId, Path.of("employee_handbook.pdf"));
```

The file convenience reads the file, base64-encodes it, and infers content type.

## Retrieve And Stream RAG Events

```java
RetrieveMemoryRequest request = RetrieveMemoryRequest.builder()
    .message("What does the handbook say about expenses?")
    .spaceKeys(List.of(new SpaceKey(spaceId, null, null)))
    .postProcessor(ai.pairsys.goodmem.client.ChatPostProcessorConfig.builder()
        .llmId(llmId)
        .build())
    .build();

try (RetrieveMemoryStream stream = client.memories.retrieve(request)) {
    for (RetrieveMemoryEvent event : stream) {
        System.out.println(event);
    }
}
```

With reranking:

```java
RetrieveMemoryRequest request = RetrieveMemoryRequest.builder()
    .message("What does the handbook say about expenses?")
    .spaceKeys(List.of(new SpaceKey(spaceId, null, null)))
    .postProcessor(ai.pairsys.goodmem.client.ChatPostProcessorConfig.builder()
        .llmId(llmId)
        .rerankerId(rerankerId)
        .build())
    .build();
```

## Pagination

`Page<T>` lazily fetches additional pages as you iterate. Use integer page sizes for list option `maxResults`.

```java
Page<Space> spaces = client.spaces.list(
    SpaceListOptions.builder().maxResults(5).build());

for (Space space : spaces) {
    System.out.println(space.spaceId() + ": " + space.name());
}
```

## Updates

Use typed update request builders. Keep IDs typed instead of converting them to strings.

```java
EmbedderResponse updated = client.embedders.update(
    embedderId,
    UpdateEmbedderRequest.builder()
        .displayName("Updated Embedder")
        .build());
```

## Status Polling

Compare typed enums directly.

```java
Memory current = client.memories.get(memoryId);
MemoryProcessingStatus status = current.processingStatus();

if (status == MemoryProcessingStatus.COMPLETED) {
    System.out.println("Ready");
} else if (status == MemoryProcessingStatus.FAILED) {
    throw new IllegalStateException("Memory processing failed");
}
```

## Cleanup

```java
client.memories.delete(memoryId);
client.spaces.delete(spaceId);
client.llms.delete(llmId);
client.embedders.delete(embedderId);
```

## References

- Local examples: `java/src/examples/java/ai/pairsys/goodmem/client/examples/`
- Integration examples: `java/src/integrationTest/java/ai/pairsys/goodmem/client/`
- Published docs: `https://goodmem.dev/docs/reference/sdk/v2/java`
- Javadoc: `https://javadoc.io/doc/ai.pairsys/goodmem-java/latest/`
