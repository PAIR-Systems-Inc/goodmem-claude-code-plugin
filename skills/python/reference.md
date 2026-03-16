# GoodMem Python SDK Reference

## Setup

```python
from goodmem import Goodmem

client = Goodmem(
    base_url="http://localhost:8080",
    api_key="gm_...",
    timeout=30.0,  # seconds (default)
)

# Recommended: use as context manager
with Goodmem(base_url="...", api_key="gm_...") as client:
    ...

# Async variant
from goodmem import AsyncGoodmem

async with AsyncGoodmem(base_url="...", api_key="gm_...") as client:
    ...
```

Constructor parameters:
- `base_url` (str): GoodMem server URL
- `api_key` (str): GoodMem API key (prefix `gm_`), sent as `x-api-key` header
- `timeout` (float): HTTP timeout in seconds (default 30.0)
- `**kwargs`: Forwarded to `httpx.Client`

## API Reference

Namespaces: `client.embedders`, `client.rerankers`, `client.llms`, `client.spaces`, `client.memories`, `client.ocr`, `client.system`, `client.users`, `client.admin`, `client.apikeys`

### client.embedders

#### `embedders.create(**kwargs)`

Create a new embedder

Parameters:
- display_name (str): User-facing name of the embedder
- description (str, optional): Description of the embedder
- provider_type (ProviderType): Type of embedding provider
- endpoint_url (str): API endpoint URL
- api_path (str, optional): API path for embeddings request (defaults: Cohere /v2/embed, TEI /embed, others /embeddings)
- model_identifier (str): Model identifier
- dimensionality (int): Output vector dimensions
- distribution_type (DistributionType): Type of embedding distribution (DENSE or SPARSE)
- max_sequence_length (int, optional): Maximum input sequence length
- supported_modalities (list, optional, default=['TEXT']): Supported content modalities (defaults to TEXT if not provided)
- credentials: Structured credential payload describing how to authenticate with the provider. Required for SaaS providers such as COHERE, JINA, and VOYAGE; optional for local or proxy providers.
- labels (dict, optional): User-defined labels for categorization
- version (str, optional): Version information
- monitoring_endpoint (str, optional): Monitoring endpoint URL
- owner_id (str, optional): Optional owner ID. If not provided, derived from the authentication context. Requires CREATE_EMBEDDER_ANY permission if specified.
- embedder_id (str, optional): Optional client-provided UUID for idempotent creation. If not provided, server generates a new UUID. Returns ALREADY_EXISTS if ID is already in use.

#### `embedders.delete(id: str)`

Delete an embedder

Parameters:
- id (str): The unique identifier of the embedder to delete

#### `embedders.get(id: str)`

Get an embedder by ID

Parameters:
- id (str): The unique identifier of the embedder to retrieve

#### `embedders.list(labels=None, **kwargs)`

List embedders

Parameters:
- owner_id (str, optional): Filter embedders by owner ID. With LIST_EMBEDDER_ANY permission, omitting this shows all accessible embedders; providing it filters by that owner. With LIST_EMBEDDER_OWN permission, only your own embedders are shown regardless of this parameter.
- provider_type (ProviderType, optional): Filter embedders by provider type. Allowed values match the ProviderType schema.
- label.* (str, optional): Filter by label value. Multiple label filters can be specified (e.g., ?label.environment=production&label.team=nlp)

#### `embedders.update(id: str, request: UpdateEmbedderRequest | dict)`

Update an embedder

Parameters:
- id (str): The unique identifier of the resource to update.
- request (UpdateEmbedderRequest | dict): The update payload. Accepts a UpdateEmbedderRequest instance or a plain dict with the same fields. Only specified fields will be modified.

### client.rerankers

#### `rerankers.create(**kwargs)`

Create a new reranker

Parameters:
- display_name (str): User-facing name of the reranker
- description (str, optional): Description of the reranker
- provider_type (ProviderType): Type of reranking provider
- endpoint_url (str): API endpoint URL
- api_path (str, optional): API path for reranking request (defaults: Cohere /v2/rerank, Jina /v1/rerank, others /rerank)
- model_identifier (str): Model identifier
- supported_modalities (list, optional, default=['TEXT']): Supported content modalities (defaults to TEXT if not provided)
- credentials: Structured credential payload describing how to authenticate with the provider. Required for SaaS providers; optional for local deployments.
- labels (dict, optional): User-defined labels for categorization
- version (str, optional): Version information
- monitoring_endpoint (str, optional): Monitoring endpoint URL
- owner_id (str, optional): Optional owner ID. If not provided, derived from the authentication context. Requires CREATE_RERANKER_ANY permission if specified.
- reranker_id (str, optional): Optional client-provided UUID for idempotent creation. If not provided, server generates a new UUID. Returns ALREADY_EXISTS if ID is already in use.

#### `rerankers.delete(id: str)`

Delete a reranker

Parameters:
- id (str): The unique identifier of the reranker to delete

#### `rerankers.get(id: str)`

Get a reranker by ID

Parameters:
- id (str): The unique identifier of the reranker to retrieve

#### `rerankers.list(labels=None, **kwargs)`

List rerankers

Parameters:
- owner_id (str, optional): Filter rerankers by owner ID. With LIST_RERANKER_ANY permission, omitting this shows all accessible rerankers; providing it filters by that owner. With LIST_RERANKER_OWN permission, only your own rerankers are shown regardless of this parameter (PERMISSION_DENIED if set to another user).
- provider_type (ProviderType, optional): Filter rerankers by provider type. Allowed values match the ProviderType schema.
- label.* (str, optional): Filter by label value. Multiple label filters can be specified (e.g., ?label.environment=production&label.team=search)

#### `rerankers.update(id: str, request: UpdateRerankerRequest | dict)`

Update a reranker

Parameters:
- id (str): The unique identifier of the resource to update.
- request (UpdateRerankerRequest | dict): The update payload. Accepts a UpdateRerankerRequest instance or a plain dict with the same fields. Only specified fields will be modified.

### client.llms

#### `llms.create(**kwargs)`

Create a new LLM

Parameters:
- display_name (str): User-facing name of the LLM
- description (str, optional): Description of the LLM
- provider_type (LLMProviderType): Type of LLM provider
- endpoint_url (str): API endpoint base URL (OpenAI-compatible base, typically ends with /v1)
- api_path (str, optional, default='/chat/completions'): API path for chat/completions request (defaults to /chat/completions if not provided)
- model_identifier (str): Model identifier
- supported_modalities (list, optional, default=['TEXT']): Supported content modalities (defaults to TEXT if not provided)
- credentials: Structured credential payload describing how to authenticate with the provider. Omit for deployments that do not require credentials.
- labels (dict, optional): User-defined labels for categorization
- version (str, optional): Version information
- monitoring_endpoint (str, optional): Monitoring endpoint URL
- capabilities: LLM capabilities defining supported features and modes. Optional - server infers capabilities from model identifier if not provided.
- default_sampling_params: Default sampling parameters for generation requests
- max_context_length (int, optional): Maximum context window size in tokens
- client_config (dict, optional): Provider-specific client configuration as flexible JSON structure
- owner_id (str, optional): Optional owner ID. If not provided, derived from the authentication context. Requires CREATE_LLM_ANY permission if specified.
- llm_id (str, optional): Optional client-provided UUID for idempotent creation. If not provided, server generates a new UUID. Returns ALREADY_EXISTS if ID is already in use.

#### `llms.delete(id: str)`

Delete an LLM

Parameters:
- id (str): The unique identifier of the LLM to delete

#### `llms.get(id: str)`

Get an LLM by ID

Parameters:
- id (str): The unique identifier of the LLM to retrieve

#### `llms.list(labels=None, **kwargs)`

List LLMs

Parameters:
- owner_id (str, optional): Filter LLMs by owner ID. With LIST_LLM_ANY permission, omitting this shows all accessible LLMs; providing it filters by that owner. With LIST_LLM_OWN permission, only your own LLMs are shown regardless of this parameter.
- provider_type (LLMProviderType, optional): Filter LLMs by provider type. Allowed values match the LLMProviderType schema.
- label.* (str, optional): Filter by label value. Multiple label filters can be specified (e.g., ?label.environment=production&label.team=ai)

#### `llms.update(id: str, request: LLMUpdateRequest | dict)`

Update an LLM

Parameters:
- id (str): The unique identifier of the resource to update.
- request (LLMUpdateRequest | dict): The update payload. Accepts a LLMUpdateRequest instance or a plain dict with the same fields. Only specified fields will be modified.

### client.spaces

#### `spaces.create(**kwargs)`

Create a new Space

Parameters:
- name (str): The desired name for the space. Must be unique within the user's scope.
- labels (dict, optional): A set of key-value pairs to categorize or tag the space. Used for filtering and organizational purposes.
- space_embedders (list): List of embedder configurations to associate with this space. Each specifies an embedder ID and a relative default retrieval weight used when no per-request overrides are provided.
- public_read (bool, optional, default=False): Indicates if the space and its memories can be read by unauthenticated users or users other than the owner. Defaults to false.
- owner_id (str, optional): Optional owner ID. If not provided, derived from the authentication context. Requires CREATE_SPACE_ANY permission if specified.
- default_chunking_config (ChunkingConfiguration): Default chunking strategy for memories in this space
- space_id (str, optional): Optional client-provided UUID for idempotent creation. If not provided, server generates a new UUID. Returns ALREADY_EXISTS if ID is already in use.

#### `spaces.delete(id: str)`

Delete a space

Parameters:
- id (str): The unique identifier of the space to delete

#### `spaces.get(id: str)`

Get a space by ID

Parameters:
- id (str): The unique identifier of the space to retrieve

#### `spaces.list(labels=None, **kwargs)`

List spaces

Parameters:
- owner_id (str, optional): Filter spaces by owner ID. With LIST_SPACE_ANY permission and owner_id omitted, returns all visible spaces. Otherwise returns caller-owned spaces only. Specifying owner_id without LIST_SPACE_ANY returns PERMISSION_DENIED.
- name_filter (str, optional): Filter spaces by name using glob pattern matching
- max_results (int, optional, default=50): Maximum number of results to return in a single page (defaults to 50, clamped to [1, 1000])
- next_token (str, optional): Pagination token for retrieving the next set of results
- sort_by (str, optional, default='created_time'): Field to sort by: 'created_time', 'updated_time', or 'name' (default: 'created_time'). Unsupported values return INVALID_ARGUMENT.
- sort_order (SortOrder, optional, default='DESCENDING'): Sort order (ASCENDING or DESCENDING, default: DESCENDING)
- label.* (str, optional): Filter by label value. Multiple label filters can be specified (e.g., ?label.project=AI&label.team=NLP)

#### `spaces.update(id: str, request: UpdateSpaceRequest | dict)`

Update a space

Parameters:
- id (str): The unique identifier of the resource to update.
- request (UpdateSpaceRequest | dict): The update payload. Accepts a UpdateSpaceRequest instance or a plain dict with the same fields. Only specified fields will be modified.

### client.memories

#### `memories.batch_create(requests: list[MemoryCreationRequest])`

Create multiple memories in a batch

Parameters:
- requests (list): Array of memory creation requests.

#### `memories.batch_delete(requests, **kwargs)`

Delete memories in batch

Parameters:
- requests (list): Array of delete selectors

#### `memories.batch_get(memory_ids, include_content=None, include_processing_history=None, **kwargs)`

Get multiple memories by ID

Parameters:
- memory_ids (list): Array of memory IDs to retrieve
- include_content (bool, optional): Whether to include the original content in the response
- include_processing_history (bool, optional): Whether to include background job processing history for each memory

#### `memories.content(id: str)`

Download memory content

Parameters:
- id (str): The unique identifier of the memory to download

#### `memories.create(space_id=None, file_path=None, **kwargs)`

Create a new memory

Parameters:
- memory_id (str, optional): Optional client-provided UUID for the memory. If omitted, the server generates one. Returns ALREADY_EXISTS if the ID is already in use.
- space_id (str): ID of the space where this memory will be stored
- original_content (str, optional): Original content as plain text (use either this or original_content_b64)
- original_content_b64 (str, optional): Original content as base64-encoded binary data (use either this or original_content)
- original_content_ref (str, optional): Reference to external content location
- content_type (str): MIME type of the content
- metadata (dict, optional): Additional metadata for the memory
- chunking_config: Chunking strategy for this memory (if not provided, uses space default)
- extract_page_images (bool, optional): Optional hint to extract page images for eligible document types (for example, PDFs)
- file_field (str, optional): Optional multipart file field name to bind binary content; required when multiple files are uploaded in a batch multipart request.

#### `memories.delete(id: str)`

Delete a memory

Parameters:
- id (str): The unique identifier of the memory to delete

#### `memories.get(id: str, include_content=False, include_processing_history=False)`

Get a memory by ID

Parameters:
- id (str): The unique identifier of the memory to retrieve
- include_content (bool, optional, default=False): Whether to include the original content in the response (defaults to false). The snake_case alias include_content is also accepted.
- include_processing_history (bool, optional, default=False): Whether to include background job processing history in the response (defaults to false). The snake_case alias include_processing_history is also accepted.

#### `memories.list(space_id: str, **kwargs)`

List memories in a space

Parameters:
- space_id (str): The unique identifier of the space containing the memories
- include_content (bool, optional, default=False): Whether to include the original content in the response (defaults to false). The snake_case alias include_content is also accepted.
- include_processing_history (bool, optional, default=False): Whether to include background job processing history in the response (defaults to false). The snake_case alias include_processing_history is also accepted.
- status_filter (str, optional): Filter memories by processing status (PENDING, PROCESSING, COMPLETED, FAILED). The snake_case alias status_filter is also accepted.
- filter (str, optional): Optional metadata filter expression for list results
- max_results (int, optional, default=50): Maximum number of results per page (defaults to 50, clamped to [1, 500]). The snake_case alias max_results is also accepted.
- next_token (str, optional): Opaque pagination token for the next page. URL-safe Base64 without padding; do not parse or construct it. The snake_case alias next_token is also accepted.
- sort_by (str, optional): Field to sort by (e.g., 'created_at'). The snake_case alias sort_by is also accepted.
- sort_order (SortOrder, optional): Sort direction (ASCENDING or DESCENDING). The snake_case alias sort_order is also accepted.

#### `memories.pages(id: str, start_page_index=None, end_page_index=None, dpi=None, content_type=None, max_results=None, next_token=None)`

List memory page images

Parameters:
- id (str): Memory UUID
- start_page_index (int, optional): Optional lower bound for returned page indices, inclusive. The snake_case alias start_page_index is also accepted.
- end_page_index (int, optional): Optional upper bound for returned page indices, inclusive. The snake_case alias end_page_index is also accepted.
- dpi (int, optional): Optional rendition filter for page-image DPI.
- content_type (str, optional): Optional rendition filter for page-image MIME type, such as image/png. The snake_case alias content_type is also accepted.
- max_results (int, optional): Maximum number of results per page. The snake_case alias max_results is also accepted.
- next_token (str, optional): Opaque pagination token for the next page. The snake_case alias next_token is also accepted. Do not parse or construct it.

#### `memories.pages_image(id: str, page_index: int, dpi=None, content_type=None)`

Download memory page image content

Parameters:
- id (str): Memory UUID
- page_index (int): 0-based page index
- dpi (int, optional): Optional rendition filter. If omitted, the unique page-image rendition for the page is returned; if multiple renditions exist, specify dpi and/or content_type.
- content_type (str, optional): Optional rendition filter. MIME type of the desired page image, such as image/png. The snake_case alias content_type is also accepted.

#### `memories.retrieve(message: str, stream=True, **kwargs)`

Advanced semantic memory retrieval with JSON

Parameters:
- message (str): Primary query/message for semantic search.
- context (list, optional): Optional context items (text or binary) to provide additional context for the search.
- space_keys (list): List of spaces to search with optional per-embedder weight overrides.
- requested_size (int, optional): Maximum number of memories to retrieve.
- fetch_memory (bool, optional): Whether to include full Memory objects in the response.
- fetch_memory_content (bool, optional): Whether to include memory content in the response. Requires fetch_memory=true.
- hnsw: Optional request-level HNSW tuning overrides. Advanced usage; available on POST retrieve.
- post_processor: Optional post-processor configuration to transform retrieval results.

### client.ocr

#### `ocr.document(content, format=None, include_raw_json=None, include_markdown=None, start_page=None, end_page=None, **kwargs)`

Run OCR on a document or image

Parameters:
- content (str): Base64-encoded document bytes
- format: Input format hint (AUTO, PDF, TIFF, PNG, JPEG, BMP)
- include_raw_json (bool, optional): Include raw OCR JSON payload in the response
- include_markdown (bool, optional): Include markdown rendering in the response
- start_page (int, optional): 0-based inclusive start page
- end_page (int, optional): 0-based inclusive end page

### client.system

#### `system.info()`

Retrieve server build metadata

#### `system.init(**kwargs)`

Initialize the system

### client.users

#### `users.get(id=None, email=None)`

Get a user by ID

Parameters:
- id (str, optional): The unique identifier of the user to retrieve
- email (str, optional): The email address of the user to retrieve

#### `users.me()`

Get current user profile

### client.admin

#### `admin.drain(**kwargs)`

Request the server to enter drain mode

Parameters:
- timeout_sec (int, optional): Maximum seconds to wait for the server to quiesce before returning.
- reason (str, optional): Human-readable reason for initiating drain mode.
- wait_for_quiesce (bool, optional): If true, wait for in-flight requests to complete and the server to reach QUIESCED before responding.

### client.apikeys

#### `apikeys.create(**kwargs)`

Create a new API key

Parameters:
- labels (dict, optional): Key-value pairs of metadata associated with the API key. Used for organization and filtering.
- expires_at (int, optional): Expiration timestamp in milliseconds since epoch. If not provided, the key does not expire.
- api_key_id (str, optional): Optional client-provided UUID for idempotent creation. If not provided, server generates a new UUID. Returns ALREADY_EXISTS if ID is already in use.

#### `apikeys.delete(id: str)`

Delete an API key

Parameters:
- id (str): The unique identifier of the API key to delete

#### `apikeys.list(**kwargs)`

List API keys

#### `apikeys.update(id: str, request: UpdateApiKeyRequest | dict)`

Update an API key

Parameters:
- id (str): The unique identifier of the resource to update.
- request (UpdateApiKeyRequest | dict): The update payload. Accepts a UpdateApiKeyRequest instance or a plain dict with the same fields. Only specified fields will be modified.

## Convenience shortcuts

The SDK provides convenience parameters that simplify common patterns.

- **`embedders.create()`**: `api_key` -> `credentials` — Converts a plain API key string to the full `EndpointAuthentication` structure (i.e.
- **`llms.create()`**: `api_key` -> `credentials` — Converts a plain API key string to the full `EndpointAuthentication` structure (i.e.
- **`memories.batch_create()`**: `requests` — List of memory creation requests.
- **`memories.create()`**: `file_path` — Path to a local file to upload.
- **`memories.list()`**: `page_size` -> `max_results` — Number of results per page (defaults to 50, clamped to [1, 500] by the server).
- **`memories.list()`**: `max_items` — Maximum total number of items to return across all pages.
- **`memories.retrieve()`**: `space_ids` -> `space_keys` — A list of space UUID strings, converted to the `space_keys` structure the API requires.
- **`memories.retrieve()`**: `stream` — If `True` (default), returns a `RetrieveMemoryStream` context manager that yields events as they arrive from the server.
- **`memories.retrieve()`**: `llm_id` -> `post_processor.config.llm_id` — The ID of the LLM to process the retrieved memories, e.g., RAG.
- **`memories.retrieve()`**: `reranker_id` -> `post_processor.config.reranker_id` — The ID of the reranker to process the retrieved memories.
- **`memories.retrieve()`**: `llm_temp` -> `post_processor.config.llm_temp` — LLM temperature for post-processing.
- **`memories.retrieve()`**: `gen_token_budget` -> `post_processor.config.gen_token_budget` — Token budget for LLM post-processing.
- **`memories.retrieve()`**: `relevance_threshold` -> `post_processor.config.relevance_threshold` — Minimum relevance score for retrieved memories.
- **`memories.retrieve()`**: `max_results` -> `post_processor.config.max_results` — Maximum number of retrieved memories to return.
- **`memories.retrieve()`**: `prompt` -> `post_processor.config.prompt` — Custom prompt for LLM post-processing.
- **`memories.retrieve()`**: `sys_prompt` -> `post_processor.config.sys_prompt` — System prompt for LLM post-processing.
- **`memories.retrieve()`**: `chronological_resort` -> `post_processor.config.chronological_resort` — Re-sort retrieved memories chronologically after semantic ranking.
- **`rerankers.create()`**: `api_key` -> `credentials` — Converts a plain API key string to the full `EndpointAuthentication` structure (i.e.
- **`spaces.list()`**: `page_size` -> `max_results` — Number of results per page (defaults to 50, clamped to [1, 1000] by the server).
- **`spaces.list()`**: `max_items` — Maximum total number of items to return across all pages.

## Known model identifiers

Pass `model_identifier` to create methods. The SDK auto-infers `provider_type`, `endpoint_url`, `dimensionality`, etc.

**Embedders** (29):
`text-embedding-3-large`, `text-embedding-3-small`, `embed-v4.0`, `embed-english-v3.0`, `embed-english-light-v3.0`, `embed-multilingual-v3.0`, `embed-multilingual-light-v3.0`, `jina-embeddings-v4`, `jina-embeddings-v3`, `jina-embeddings-v2-base-en`, `jina-embeddings-v2-base-es`, `jina-embeddings-v2-base-de`, `jina-embeddings-v2-base-zh`, `jina-embeddings-v2-base-code`, `jina-clip-v1`, `jina-clip-v2`, `voyage-4-large`, `voyage-4`, `voyage-4-lite`, `voyage-code-3`, `voyage-3-large`, `voyage-3.5`, `voyage-3.5-lite`, `voyage-3`, `voyage-3-lite`, `voyage-finance-2`, `voyage-law-2`, `voyage-code-2`, `voyage-multilingual-2`

**LLMs** (34):
`gpt-5.2`, `gpt-5.2-pro`, `gpt-5.1`, `gpt-5`, `gpt-5-mini`, `gpt-5-nano`, `o3`, `o3-mini`, `o4-mini`, `gpt-4.1`, `gpt-4.1-mini`, `gpt-4.1-nano`, `gpt-4o`, `gpt-4o-mini`, `gpt-4-turbo`, `gpt-3.5-turbo`, `o1`, `o1-mini`, `o1-preview`, `command-a-03-2025`, `command-r7b-12-2024`, `command-a-translate-08-2025`, `command-a-reasoning-08-2025`, `command-a-vision-07-2025`, `command-r-08-2024`, `command-r-plus-08-2024`, `c4ai-aya-expanse-8b`, `c4ai-aya-expanse-32b`, `c4ai-aya-vision-8b`, `c4ai-aya-vision-32b`, `command-r-03-2024`, `command-r-plus-04-2024`, `command`, `command-light`

**Rerankers** (16):
`rerank-v4.0-pro`, `rerank-v4.0-fast`, `rerank-v3.5`, `rerank-english-v3.0`, `rerank-multilingual-v3.0`, `jina-reranker-v3`, `jina-reranker-v2-base-multilingual`, `jina-reranker-v1-base-en`, `jina-reranker-v1-turbo-en`, `jina-reranker-v1-tiny-en`, `rerank-2.5`, `rerank-2.5-lite`, `rerank-2`, `rerank-2-lite`, `rerank-1`, `rerank-lite-1`

## Commonly-used types

Import from `goodmem.types`:

- **Responses**: `EmbedderResponse`, `RerankerResponse`, `LLMResponse`, `Space`, `Memory`, `ApiKeyResponse`, `UserResponse`
- **Create requests**: `EmbedderCreationRequest`, `RerankerCreationRequest`, `LLMCreationRequest`, `SpaceCreationRequest`, `MemoryCreationRequest`
- **Update requests**: `UpdateEmbedderRequest`, `UpdateRerankerRequest`, `LLMUpdateRequest`, `UpdateSpaceRequest`, `UpdateApiKeyRequest`
- **Retrieval**: `RetrieveMemoryEvent`, `RetrievedItem`, `ChunkReference`
- **Configuration**: `ChunkingConfiguration`, `EndpointAuthentication`, `PostProcessor`, `SpaceEmbedderConfig`

## Common patterns

### Create with model auto-inference
```python
# Just pass model_identifier and api_key — provider, endpoint, dims are auto-inferred
embedder = client.embedders.create(
    display_name="My Embedder",
    model_identifier="text-embedding-3-large",
    api_key="sk-...",
)
```

### Update (two paths)
```python
# Option 1: typed request object
from goodmem.types import UpdateEmbedderRequest
client.embedders.update(id="...", request=UpdateEmbedderRequest(
    display_name="New Name",
))

# Option 2: plain dict
client.embedders.update(id="...", request={"display_name": "New Name"})
```

### Pagination
```python
# Iterate directly — auto-paginates
for space in client.spaces.list():
    print(space.space_id, space.name)

# Filter by labels
for emb in client.embedders.list(labels={"env": "prod"}):
    print(emb.display_name)
```

### Memory retrieval (streaming)
```python
# Streaming (default)
with client.memories.retrieve(
    message="What is GoodMem?",
    space_ids=["space-id"],
) as stream:
    for event in stream:
        if event.retrieved_item:
            chunk = event.retrieved_item.chunk
            print(chunk.chunk.chunk_text, chunk.relevance_score)

# Non-streaming (returns list)
events = client.memories.retrieve(
    message="What is GoodMem?",
    space_ids=["space-id"],
    stream=False,
)
```

### Retrieval with post-processing (RAG)
```python
with client.memories.retrieve(
    message="Summarize our knowledge about X",
    space_ids=["space-id"],
    llm_id="llm-id",           # enables LLM post-processing
    reranker_id="reranker-id",  # optional: rerank before LLM
    llm_temp=0.3,
) as stream:
    for event in stream:
        if event.retrieved_item:
            print(event.retrieved_item.chunk.chunk.chunk_text)
```

### File upload
```python
memory = client.memories.create(
    space_id="space-id",
    file_path="/path/to/document.pdf",
)
```

### Batch operations
```python
from goodmem.api.memories import MemoryCreationRequest

result = client.memories.batch_create(requests=[
    MemoryCreationRequest(space_id="...", original_content="First"),
    MemoryCreationRequest(space_id="...", original_content="Second"),
])
```

### Types import
```python
# All pydantic models available via short path
from goodmem.types import UpdateEmbedderRequest, EmbedderResponse, SpaceCreationRequest
```

## Errors

All errors inherit from `GoodMemError`. HTTP errors inherit from `APIError`.

| Status | Exception | Description |
|--------|-----------|-------------|
| 401 | `AuthenticationError` | 401 Unauthorized. |
| 403 | `PermissionError` | 403 Forbidden. |
| 404 | `NotFoundError` | 404 Not Found. |
| 409 | `ConflictError` | 409 Conflict (e.g., duplicate resource). |
| 422 | `ValidationError` | 422 Unprocessable Entity. |
| 429 | `RateLimitError` | 429 Too Many Requests. |
| 5xx | `ServerError` | 5xx Server Error |

```python
from goodmem.errors import NotFoundError, ConflictError

try:
    client.embedders.get(id="nonexistent")
except NotFoundError:
    print("Not found")
```
