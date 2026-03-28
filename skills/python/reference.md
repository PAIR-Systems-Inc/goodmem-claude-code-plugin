# GoodMem Python SDK Reference

## Setup

```python
from goodmem import Goodmem

client = Goodmem(
    base_url="http://localhost:8080",
    api_key="gm_...",
)

# Recommended: use as context manager
with Goodmem(base_url="...", api_key="gm_...") as client:
    ...

# Async variant
from goodmem import AsyncGoodmem

async with AsyncGoodmem(base_url="...", api_key="gm_...") as client:
    ...
```

Two modes (mutually exclusive):
1. `Goodmem(base_url='...', api_key='gm_...')` — SDK builds everything
2. `Goodmem(http_client=httpx.Client(base_url='...', headers={'x-api-key': 'gm_...'}))` — full control

Constructor parameters:
- `base_url` (str): GoodMem server URL. Mutually exclusive with `http_client`.
- `api_key` (str): GoodMem API key (prefix `gm_`), sent as `x-api-key` header. Mutually exclusive with `http_client`.
- `timeout` (float, default 30.0): HTTP timeout in seconds. Mutually exclusive with `http_client`.
- `verify` (bool | str, default True): SSL certificate verification. Pass `False` to skip, or a file path to a CA bundle. Mutually exclusive with `http_client`.
- `http_client` (httpx.Client): Pre-configured httpx client with base URL and auth headers. Mutually exclusive with all other params.

Package metadata:
- `goodmem.__version__` — SDK package version (e.g., `"0.1.5"`)
- `goodmem.__based_on_goodmem_commit__` — GoodMem server commit hash this SDK was generated from. Useful for debugging version mismatches between SDK and server.

## API Reference

Namespaces: `client.embedders`, `client.rerankers`, `client.llms`, `client.spaces`, `client.memories`, `client.ocr`, `client.system`, `client.users`, `client.admin`, `client.apikeys`

### client.embedders

#### `embedders.create(display_name: str, model_identifier: str, api_key=None, api_path=None, credentials=None, description=None, dimensionality=None, distribution_type="DENSE", embedder_id=None, endpoint_url=None, labels=None, max_sequence_length=None, monitoring_endpoint=None, owner_id=None, provider_type=None, supported_modalities=None, version=None) -> EmbedderResponse`

Create a new embedder

Parameters:
- `display_name` (str): User-facing name of the embedder
- `model_identifier` (str): The string that identifies the embedder. Usually the model identifier assigned by HuggingFace or the LLM provider, e.g., `"text-embedding-3-small"`...
- `api_key` (str, optional): Converts a plain API key string to the full `EndpointAuthentication` structure (i.e. `{"kind": "CREDENTIAL_KIND_API_KEY", "api_key": {"inline_secre...
- `api_path` (str, optional): API path for embeddings request (defaults: Cohere /v2/embed, TEI /embed, others /embeddings)
- `credentials` (EndpointAuthentication, optional): Structured credential payload describing how to authenticate with the provider.
- `description` (str, optional): Description of the embedder
- `dimensionality` (int, optional): Output vector dimensions. Auto-inferred from `model_identifier` for known models (using `dimensions.default` from the model registry); required whe...
- `distribution_type` (DistributionType, optional, default="DENSE"): The distribution type of the embedder's vector output. Defaults to `"DENSE"` when not specified.
- `embedder_id` (str, optional): Optional client-provided UUID for idempotent creation. If not provided, server generates a new UUID. Returns ALREADY_EXISTS if ID is already in use.
- `endpoint_url` (str, optional): Base URL for the embedding endpoint. Auto-inferred from `provider_type` for known providers.
- `labels` (dict[str, str], optional): User-defined labels for categorization
- `max_sequence_length` (int, optional): Maximum token length accepted by the model. Auto-inferred from `model_identifier` for known models; required when `model_identifier` is not in the ...
- `monitoring_endpoint` (str, optional): Monitoring endpoint URL
- `owner_id` (str, optional): Optional owner ID. If not provided, derived from the authentication context. Requires CREATE_EMBEDDER_ANY permission if specified.
- `provider_type` (ProviderType, optional): Provider backend — one of `"OPENAI"`, `"COHERE"`, `"VOYAGE"`, `"JINA"`, `"VLLM"`, `"TEI"`, `"LLAMA_CPP"`. Use `"OPENAI"` for OpenAI-compatible endp...
- `supported_modalities` (list[Modality], optional): Modalities supported by this embedder (e.g. `["TEXT"]`). Auto-inferred from `model_identifier` for known models; required when `model_identifier` i...
- `version` (str, optional): Version information

#### `embedders.get(id: str) -> EmbedderResponse`

Get an embedder by ID

Parameters:
- `id` (str): The UUID of the embedder to retrieve

#### `embedders.list(labels=None, owner_id=None, provider_type=None) -> list[EmbedderResponse]`

List embedders

Parameters:
- `labels` (dict[str, str], optional): Filters to match embedders by labels attached via create/update. You can verify these labels in `EmbedderResponse.labels`. Example: `labels={"env":...
- `owner_id` (str, optional): Filter embedders by owner ID. With LIST_EMBEDDER_ANY permission, omitting this shows all accessible embedders; providing it filters by that owner. ...
- `provider_type` (ProviderType, optional): Filter embedders by provider type. Allowed values match the ProviderType schema.

#### `embedders.update(id: str, request: UpdateEmbedderRequest | dict) -> EmbedderResponse`

Update an embedder

Parameters:
- `id` (str): The unique identifier of the resource to update.
- `request` (UpdateEmbedderRequest | dict): The update payload. Accepts a `UpdateEmbedderRequest` instance or a plain dict with the same fields. Only specified fields will be modified.

#### `embedders.delete(id: str) -> None`

Delete an embedder

Parameters:
- `id` (str): The UUID of the embedder to delete

### client.rerankers

#### `rerankers.create(display_name: str, model_identifier: str, api_key=None, api_path=None, credentials=None, description=None, endpoint_url=None, labels=None, monitoring_endpoint=None, owner_id=None, provider_type=None, reranker_id=None, supported_modalities=None, version=None) -> RerankerResponse`

Create a new reranker

Parameters:
- `display_name` (str): User-facing name of the reranker
- `model_identifier` (str): When a known model, auto-fills `provider_type`, `endpoint_url`, and `supported_modalities` for 16 registered models.
- `api_key` (str, optional): Converts a plain API key string to the full `EndpointAuthentication` structure (i.e. `{"kind": "CREDENTIAL_KIND_API_KEY", "api_key": {"inline_secre...
- `api_path` (str, optional): API path for reranking request (defaults: Cohere `/v2/rerank`, Jina `/v1/rerank`, others `/rerank`).
- `credentials` (EndpointAuthentication, optional): Structured credential payload describing how to authenticate with the provider.
- `description` (str, optional): Description of the reranker
- `endpoint_url` (str, optional): Base URL for the reranking endpoint. Auto-inferred from `provider_type` for known providers; required when `model_identifier` is not in the registry.
- `labels` (dict[str, str], optional): User-defined labels for categorization
- `monitoring_endpoint` (str, optional): Monitoring endpoint URL
- `owner_id` (str, optional): Optional owner ID. If not provided, derived from the authentication context. Requires CREATE_RERANKER_ANY permission if specified.
- `provider_type` (ProviderType, optional): Provider backend (e.g. `"COHERE"`, `"JINA"`). Auto-inferred from `model_identifier` for known models; required when `model_identifier` is not in th...
- `reranker_id` (str, optional): Optional client-provided UUID for idempotent creation. If not provided, server generates a new UUID. Returns ALREADY_EXISTS if ID is already in use.
- `supported_modalities` (list[Modality], optional): Modalities supported by this reranker (e.g. `["TEXT"]`). Auto-inferred from `model_identifier` for known models; defaults to `["TEXT"]` on the serv...
- `version` (str, optional): Version information

#### `rerankers.get(id: str) -> RerankerResponse`

Get a reranker by ID

Parameters:
- `id` (str): The UUID of the reranker to retrieve

#### `rerankers.list(labels=None, owner_id=None, provider_type=None) -> list[RerankerResponse]`

List rerankers

Parameters:
- `labels` (dict[str, str], optional): Filters to match rerankers by labels attached via create/update. You can verify these labels in `RerankerResponse.labels`. Example: `labels={"env":...
- `owner_id` (str, optional): Filter rerankers by owner ID. With LIST_RERANKER_ANY permission, omitting this shows all accessible rerankers; providing it filters by that owner. ...
- `provider_type` (ProviderType, optional): Filter rerankers by provider type. Allowed values match the ProviderType schema.

#### `rerankers.update(id: str, request: UpdateRerankerRequest | dict) -> RerankerResponse`

Update a reranker

Parameters:
- `id` (str): The unique identifier of the resource to update.
- `request` (UpdateRerankerRequest | dict): The update payload. Accepts a `UpdateRerankerRequest` instance or a plain dict with the same fields. Only specified fields will be modified.

#### `rerankers.delete(id: str) -> None`

Delete a reranker

Parameters:
- `id` (str): The UUID of the reranker to delete

### client.llms

#### `llms.create(display_name: str, model_identifier: str, api_key=None, api_path=None, capabilities=None, client_config=None, credentials=None, default_sampling_params=None, description=None, endpoint_url=None, labels=None, llm_id=None, max_context_length=None, monitoring_endpoint=None, owner_id=None, provider_type=None, supported_modalities=None, version=None) -> CreateLLMResponse`

Create a new LLM

Parameters:
- `display_name` (str): User-facing name of the LLM
- `model_identifier` (str): When a known model, auto-fills `provider_type`, `endpoint_url`, `max_context_length`, and `supported_modalities` for 34 registered models.
- `api_key` (str, optional): Converts a plain API key string to the full `EndpointAuthentication` structure (i.e. `{"kind": "CREDENTIAL_KIND_API_KEY", "api_key": {"inline_secre...
- `api_path` (str, optional): API path for chat/completions request (defaults to `/chat/completions` if not provided).
- `capabilities` (LLMCapabilities, optional): LLM capabilities defining supported features and modes. Optional — server infers capabilities from model identifier if not provided.
- `client_config` (dict[str, Any], optional): Provider-specific client configuration as flexible JSON structure
- `credentials` (EndpointAuthentication, optional): Structured credential payload describing how to authenticate with the provider.
- `default_sampling_params` (LLMSamplingParams, optional): Default sampling parameters for generation requests
- `description` (str, optional): Description of the LLM
- `endpoint_url` (str, optional): Base URL for the LLM endpoint (OpenAI-compatible base, typically ends with `/v1`). Auto-inferred from `provider_type` for known providers; required...
- `labels` (dict[str, str], optional): User-defined labels for categorization
- `llm_id` (str, optional): Optional client-provided UUID for idempotent creation. If not provided, server generates a new UUID. Returns ALREADY_EXISTS if ID is already in use.
- `max_context_length` (int, optional): Maximum context window size in tokens. Auto-inferred from `model_identifier` for known models; recommended when `model_identifier` is not in the re...
- `monitoring_endpoint` (str, optional): Monitoring endpoint URL
- `owner_id` (str, optional): Optional owner ID. If not provided, derived from the authentication context. Requires CREATE_LLM_ANY permission if specified.
- `provider_type` (LLMProviderType, optional): Provider backend — one of `"OPENAI"`, `"LITELLM_PROXY"`, `"OPEN_ROUTER"`, `"VLLM"`, `"OLLAMA"`, `"LLAMA_CPP"`, `"CUSTOM_OPENAI_COMPATIBLE"`. Use `"...
- `supported_modalities` (list[Modality], optional): Modalities supported by this LLM (e.g. `["TEXT"]`). Auto-inferred from `model_identifier` for known models; defaults to `["TEXT"]` on the server if...
- `version` (str, optional): Version information

#### `llms.get(id: str) -> LLMResponse`

Get an LLM by ID

Parameters:
- `id` (str): The UUID of the LLM to retrieve

#### `llms.list(labels=None, owner_id=None, provider_type=None) -> list[LLMResponse]`

List LLMs

Parameters:
- `labels` (dict[str, str], optional): Filters to match LLMs by labels attached via create/update. You can verify these labels in `LLMResponse.labels`. Example: `labels={"env":"prod", "t...
- `owner_id` (str, optional): Filter LLMs by owner ID. With LIST_LLM_ANY permission, omitting this shows all accessible LLMs; providing it filters by that owner. With LIST_LLM_O...
- `provider_type` (LLMProviderType, optional): Filter LLMs by provider type. Allowed values match the LLMProviderType schema.

#### `llms.update(id: str, request: LLMUpdateRequest | dict) -> LLMResponse`

Update an LLM

Parameters:
- `id` (str): The unique identifier of the resource to update.
- `request` (LLMUpdateRequest | dict): The update payload. Accepts a `LLMUpdateRequest` instance or a plain dict with the same fields. Only specified fields will be modified.

#### `llms.delete(id: str) -> None`

Delete an LLM

Parameters:
- `id` (str): The UUID of the LLM to delete

### client.spaces

#### `spaces.create(name: str, space_embedders: list[SpaceEmbedderConfig], default_chunking_config={'recursive': {'chunkSize': 512, 'chunkOverlap': 64, 'keepStrategy': 'KEEP_END', 'lengthMeasurement': 'CHARACTER_COUNT'}}, labels=None, owner_id=None, public_read=None, space_id=None) -> Space`

Create a new Space

Parameters:
- `name` (str): The desired name for the space. Must be unique within the user's scope.
- `space_embedders` (list[SpaceEmbedderConfig]): List of embedder configurations to associate with this space. At least one embedder configuration is required. Each specifies an embedder ID and a ...
- `default_chunking_config` (ChunkingConfiguration, optional, default={'recursive': {'chunkSize': 512, 'chunkOverlap': 64, 'keepStrategy': 'KEEP_END', 'lengthMeasurement': 'CHARACTER_COUNT'}}): Default strategy to chunk any memory ingested into this space. Can be overriden by per-memory chunking strategy.
- `labels` (dict[str, str], optional): A set of key-value pairs to categorize or tag the space. Used for filtering and organizational purposes.
- `owner_id` (str, optional): Optional owner ID. If not provided, derived from the authentication context. Requires CREATE_SPACE_ANY permission if specified.
- `public_read` (bool, optional): Indicates if the space and its memories can be read by unauthenticated users or users other than the owner. Defaults to false.
- `space_id` (str, optional): Optional client-provided UUID for idempotent creation. If not provided, server generates a new UUID. Returns ALREADY_EXISTS if ID is already in use.

#### `spaces.get(id: str) -> Space`

Get a space by ID

Parameters:
- `id` (str): The UUID of the space to retrieve

#### `spaces.list(labels=None, name_filter=None, owner_id=None, sort_by=None, sort_order=None, page_size=None, max_items=None, next_token=None) -> Page[Space]`

List spaces

Parameters:
- `labels` (dict[str, str], optional): Filters to match spaces by labels attached via create/update. You can verify these labels in `Space.labels`. Example: `labels={"env":"prod", "team"...
- `name_filter` (str, optional): Filter spaces by name using glob pattern matching.
- `owner_id` (str, optional): Filter spaces by owner ID. With LIST_SPACE_ANY permission and ownerId omitted, returns all visible spaces. Otherwise returns caller-owned spaces on...
- `sort_by` (str, optional): Field to sort by: `'created_time'`, `'updated_time'`, or `'name'` (default: `'created_time'`). Unsupported values return INVALID_ARGUMENT.
- `sort_order` (SortOrder, optional): Sort order (`ASCENDING` or `DESCENDING`, default: `DESCENDING`).
- `page_size` (int, optional): Number of results per page.
- `max_items` (int, optional): Total number of items to return across all pages.
- `next_token` (str, optional): Opaque pagination token to resume from a previous page's `next_token`.

#### `spaces.update(id: str, request: UpdateSpaceRequest | dict) -> Space`

Update a space

Parameters:
- `id` (str): The unique identifier of the resource to update.
- `request` (UpdateSpaceRequest | dict): The update payload. Accepts a `UpdateSpaceRequest` instance or a plain dict with the same fields. Only specified fields will be modified.

#### `spaces.delete(id: str) -> None`

Delete a space

Parameters:
- `id` (str): The UUID of the space to delete

### client.memories

#### `memories.create(space_id: str, chunking_config=None, content_type=None, extract_page_images=None, memory_id=None, metadata=None, original_content=None, original_content_b64=None, original_content_ref=None, file_path=None) -> Memory`

Create a new memory

Parameters:
- `space_id` (str): ID of the space where this memory will be stored
- `chunking_config` (ChunkingConfiguration, optional): Chunking strategy for this memory (if not provided, uses space default)
- `content_type` (str, optional): MIME type of the content. Auto-inferred as `"text/plain"` for `original_content`, or from the file extension for `file_path`. Required when using `...
- `extract_page_images` (bool, optional): Optional hint to extract page images for eligible document types (for example, PDFs)
- `memory_id` (str, optional): Optional client-provided UUID for the memory. If omitted, the server generates one. Returns ALREADY_EXISTS if the ID is already in use.
- `metadata` (dict[str, Any], optional): Metadata for the memory. Any JSON-serializable dict. Can be nested. Can be used for filtering in memory list operation. (e.g. `{"author": "John Doe...
- `original_content` (str, optional): Original content as plain text. Mutually exclusive with `file_path` and `original_content_b64`.
- `original_content_b64` (str, optional): Original content as base64-encoded binary data. Mutually exclusive with `file_path` and `original_content`.
- `original_content_ref` (str, optional): Reference to external content location. Functions as a metadata field. Does not make Goodmem download the content from the URL and use it to create...
- `file_path` (str, optional): Path to a local file to upload. Mutually exclusive with `original_content` and `original_content_b64`.

#### `memories.retrieve(message: str, chronological_resort=True, context=None, fetch_memory=None, fetch_memory_content=None, gen_token_budget=512, hnsw=None, llm_id=None, llm_temp=0.3, max_results=10, post_processor=None, prompt=None, relevance_threshold=None, requested_size=None, reranker_id=None, space_ids=None, space_keys=None, sys_prompt=None, stream=True) -> RetrieveMemoryStream | list[RetrieveMemoryEvent]`

Advanced semantic memory retrieval with JSON

Parameters:
- `message` (str): Primary query/message for semantic search.
- `chronological_resort` (bool, optional, default=True): Re-sort retrieved memories chronologically after semantic ranking. Only applies when `llm_id` or `reranker_id` is set.
- `context` (list[ContextItem], optional): Optional context items (text or binary) to provide additional context for the search.
- `fetch_memory` (bool, optional): If `True`, memory definition events are streamed. Set to `False` to skip them.
- `fetch_memory_content` (bool, optional): If `True`, includes the raw content of each memory in the response. Only applicable when `fetch_memory` is `True`.
- `gen_token_budget` (int, optional, default=512): Token budget for LLM post-processing. Must be positive. If the token budget is insufficient, the server will return an error. Only applies when `ll...
- `hnsw` (HnswOptions, optional): Optional request-level HNSW tuning overrides. Advanced usage; available on POST retrieve.
- `llm_id` (str, optional): The ID of the LLM to process the retrieved memories, e.g., RAG. Assembles the nested `PostProcessor` structure automatically. If unset, no LLM will...
- `llm_temp` (float, optional, default=0.3): LLM temperature for post-processing. Valid range is 0.0-2.0. Only applies when `llm_id` is set.
- `max_results` (int, optional, default=10): Maximum number of retrieved memories to return. Must be positive. Only applies when `llm_id` or `reranker_id` is set.
- `post_processor` (PostProcessor, optional): Optional post-processor configuration to transform retrieval results.
- `prompt` (str, optional): Custom prompt for LLM post-processing. If unset, the server's default prompt is used. Only applies when `llm_id` is set.
- `relevance_threshold` (float, optional): Minimum relevance score for retrieved memories. Only applies when `reranker_id` is set.
- `requested_size` (int, optional): Maximum number of memories to retrieve.
- `reranker_id` (str, optional): The ID of the reranker to process the retrieved memories. If unset, no reranker will be used.
- `space_ids` (list[str], optional): A list of space UUID strings, converted to the `space_keys` structure the API requires.
- `space_keys` (list[SpaceKey], optional): Full space configuration for retrieval — a list of `SpaceKey` dicts, each with a required `space_id` and optional `embedder_weights` (per-embedder ...
- `sys_prompt` (str, optional): System prompt for LLM post-processing. If unset, the server's default system prompt is used. Only applies when `llm_id` is set.
- `stream` (bool, optional, default=True): If True (default), returns a streaming context manager. If False, returns a list.

#### `memories.get(id: str, include_content=None, include_processing_history=None) -> Memory`

Get a memory by ID

Parameters:
- `id` (str): The UUID of the memory to retrieve
- `include_content` (bool, optional): Whether to include the original content in the response (defaults to false). The snake_case alias include_content is also accepted.
- `include_processing_history` (bool, optional): Whether to include background job processing history in the response (defaults to false). The snake_case alias include_processing_history is also a...

#### `memories.content(id: str) -> bytes`

Download memory content

Parameters:
- `id` (str): The UUID of the memory to download

#### `memories.pages(id: str, content_type=None, dpi=None, end_page_index=None, max_results=None, next_token=None, start_page_index=None) -> Page[MemoryPageImage]`

List memory page images

Parameters:
- `id` (str): Memory UUID
- `content_type` (str, optional): Optional rendition filter for page-image MIME type, such as image/png. The snake_case alias content_type is also accepted.
- `dpi` (int, optional): Optional rendition filter for page-image DPI.
- `end_page_index` (int, optional): Optional upper bound for returned page indices, inclusive. The snake_case alias end_page_index is also accepted.
- `max_results` (int, optional): Maximum number of results per page. The snake_case alias max_results is also accepted.
- `next_token` (str, optional): Opaque pagination token for the next page. The snake_case alias next_token is also accepted. Do not parse or construct it.
- `start_page_index` (int, optional): Optional lower bound for returned page indices, inclusive. The snake_case alias start_page_index is also accepted.

#### `memories.pages_image(id: str, page_index: int, content_type=None, dpi=None) -> bytes`

Download memory page image content

Parameters:
- `id` (str): Memory UUID
- `page_index` (int): 0-based page index
- `content_type` (str, optional): Optional rendition filter. MIME type of the desired page image, such as image/png. The snake_case alias content_type is also accepted.
- `dpi` (int, optional): Optional rendition filter. If omitted, the unique page-image rendition for the page is returned; if multiple renditions exist, specify dpi and/or c...

#### `memories.list(space_id: str, filter=None, include_content=None, include_processing_history=None, sort_by=None, sort_order=None, status_filter=None, page_size=None, max_items=None, next_token=None) -> Page[Memory]`

List memories in a space

Parameters:
- `space_id` (str): The UUID of the space containing the memories
- `filter` (str, optional): Metadata filter expression for list results. See [Metadata Filters Guide](../../../../how-to/metadata-filters) and [Filter Expressions Reference](....
- `include_content` (bool, optional): Whether to include the original content in the response (defaults to false). The snake_case alias include_content is also accepted.
- `include_processing_history` (bool, optional): Whether to include background job processing history in the response (defaults to false). The snake_case alias include_processing_history is also a...
- `sort_by` (str, optional): Field to sort by (e.g., 'created_at'). The snake_case alias sort_by is also accepted.
- `sort_order` (SortOrder, optional): Sort direction (ASCENDING or DESCENDING). The snake_case alias sort_order is also accepted.
- `status_filter` (str, optional): Filter memories by processing status (PENDING, PROCESSING, COMPLETED, FAILED). The snake_case alias status_filter is also accepted.
- `page_size` (int, optional): Number of results per page.
- `max_items` (int, optional): Total number of items to return across all pages.
- `next_token` (str, optional): Opaque pagination token to resume from a previous page's `next_token`.

#### `memories.delete(id: str) -> None`

Delete a memory

Parameters:
- `id` (str): The UUID of the memory to delete

#### `memories.batch_create(requests: list[MemoryCreationRequest]) -> BatchMemoryResponse`

Create multiple memories in a batch

Parameters:
- `requests` (list[MemoryCreationRequest]): List of memory creation requests. Import via `from goodmem.api.memories import MemoryCreationRequest`. Unlike the raw `JsonMemoryCreationRequest`, ...

#### `memories.batch_get(memory_ids: list[str], include_content=None, include_processing_history=None) -> BatchMemoryResponse`

Get multiple memories by ID

Parameters:
- `memory_ids` (list[str]): Array of memory IDs to retrieve
- `include_content` (bool, optional): Whether to include the original content in the response
- `include_processing_history` (bool, optional): Whether to include background job processing history for each memory

#### `memories.batch_delete(requests: list[BatchDeleteMemorySelectorRequest]) -> BatchMemoryResponse`

Delete memories in batch

Parameters:
- `requests` (list[BatchDeleteMemorySelectorRequest]): Array of delete selectors

### client.ocr

#### `ocr.document(content: str, end_page=None, format=None, include_markdown=None, include_raw_json=None, start_page=None) -> OcrDocumentResponse`

Run OCR on a document or image

Parameters:
- `content` (str): Base64-encoded document bytes
- `end_page` (int, optional): 0-based inclusive end page
- `format` (OcrInputFormat, optional): Input format hint (AUTO, PDF, TIFF, PNG, JPEG, BMP)
- `include_markdown` (bool, optional): Include markdown rendering in the response
- `include_raw_json` (bool, optional): Include raw OCR JSON payload in the response
- `start_page` (int, optional): 0-based inclusive start page

### client.system

#### `system.info() -> SystemInfoResponse`

Retrieve server build metadata

#### `system.init() -> SystemInitResponse`

Initialize the system

### client.users

#### `users.get(email=None, id=None) -> UserResponse`

Get a user by ID

Parameters:
- `email` (str, optional): The user's email address. Mutually exclusive with `id` — exactly one must be provided.
- `id` (str, optional): The user's UUID. Mutually exclusive with `email` — exactly one must be provided.

#### `users.me() -> UserResponse`

Get current user profile

### client.admin

#### `admin.drain(reason=None, timeout_sec=None, wait_for_quiesce=None) -> AdminDrainResponse`

Request the server to enter drain mode

Parameters:
- `reason` (str, optional): Human-readable reason for initiating drain mode.
- `timeout_sec` (int, optional): Maximum seconds to wait for the server to quiesce before returning.
- `wait_for_quiesce` (bool, optional): If true, wait for in-flight requests to complete and the server to reach QUIESCED before responding.

#### `admin.background_jobs.purge(older_than: str, dry_run=None, limit=None, statuses=None) -> AdminPurgeJobsResponse`

Purge completed background jobs

Parameters:
- `older_than` (str): ISO-8601 timestamp cutoff; only terminal jobs older than this instant are eligible.
- `dry_run` (bool, optional): If true, report purge counts without deleting any rows.
- `limit` (int, optional): Maximum number of jobs to purge in this request.
- `statuses` (list[str], optional): Optional terminal background job statuses to target for purging.

#### `admin.license.reload() -> AdminReloadLicenseResponse`

Reload the active license from disk

### client.apikeys

#### `apikeys.create(api_key_id=None, expires_at=None, labels=None) -> CreateApiKeyResponse`

Create a new API key

Parameters:
- `api_key_id` (str, optional): Optional client-provided UUID for idempotent creation. If not provided, server generates a new UUID. Returns ALREADY_EXISTS if ID is already in use.
- `expires_at` (int, optional): Expiration timestamp in milliseconds since epoch. If not provided, the key does not expire.
- `labels` (dict[str, str], optional): Key-value pairs of metadata associated with the API key. Used for organization and filtering.

#### `apikeys.list() -> list[ApiKeyResponse]`

List API keys

#### `apikeys.update(id: str, request: UpdateApiKeyRequest | dict) -> ApiKeyResponse`

Update an API key

Parameters:
- `id` (str): The unique identifier of the resource to update.
- `request` (UpdateApiKeyRequest | dict): The update payload. Accepts a `UpdateApiKeyRequest` instance or a plain dict with the same fields. Only specified fields will be modified.

#### `apikeys.delete(id: str) -> None`

Delete an API key

Parameters:
- `id` (str): The UUID of the API key to delete

## Convenience shortcuts

The SDK provides convenience parameters that simplify common patterns.

- **`embedders.create()`**: `api_key` -> `credentials` — Converts a plain API key string to the full `EndpointAuthentication` structure (i.e. `{"kind": "CREDENTIAL_KIND_API_KEY", "api_key": {"inline_secret": "sk-..."}}`). Most SaaS/cloud and/or proprietary providers (e.g., OpenAI, Cohere, Jina, Voyage, OpenRouter, Gemini) require an API key.
- **`llms.create()`**: `api_key` -> `credentials` — Converts a plain API key string to the full `EndpointAuthentication` structure (i.e. `{"kind": "CREDENTIAL_KIND_API_KEY", "api_key": {"inline_secret": "sk-..."}}`).
- **`memories.batch_create()`**: `requests` — List of memory creation requests. Import via `from goodmem.api.memories import MemoryCreationRequest`. Unlike the raw `JsonMemoryCreationRequest`, `content_type` is optional and auto-inferred for text content.
- **`memories.create()`**: `file_path` — Path to a local file to upload. Mutually exclusive with `original_content` and `original_content_b64`.
- **`memories.list()`**: `page_size` -> `max_results` — Number of results per page (defaults to 50, clamped to [1, 500] by the server). A smaller value will reduce the latency of each page — so you get items faster each page, but increase the number of requests made to the server. Use `max_items` to cap total results.
- **`memories.list()`**: `max_items` — Maximum total number of items to return across all pages. When set, iteration stops after this many items. If left unset, all pages will be fetched.
- **`memories.retrieve()`**: `space_ids` -> `space_keys` — A list of space UUID strings, converted to the `space_keys` structure the API requires.
- **`memories.retrieve()`**: `stream` — If `True` (default), returns a `RetrieveMemoryStream` context manager that yields events as they arrive from the server. If `False`, collects all events and returns a plain `list[RetrieveMemoryEvent]`.
- **`memories.retrieve()`**: `llm_id` -> `post_processor.config.llm_id` — The ID of the LLM to process the retrieved memories, e.g., RAG. Assembles the nested `PostProcessor` structure automatically. If unset, no LLM will be used. Setting `llm_id` or `reranker_id` activates post-processing; the remaining post-processor params below (`llm_temp`, `gen_token_budget`, etc.) only take effect when at least one is set.
- **`memories.retrieve()`**: `reranker_id` -> `post_processor.config.reranker_id` — The ID of the reranker to process the retrieved memories. If unset, no reranker will be used.
- **`memories.retrieve()`**: `llm_temp` -> `post_processor.config.llm_temp` — LLM temperature for post-processing. Valid range is 0.0-2.0. Only applies when `llm_id` is set.
- **`memories.retrieve()`**: `gen_token_budget` -> `post_processor.config.gen_token_budget` — Token budget for LLM post-processing. Must be positive. If the token budget is insufficient, the server will return an error. Only applies when `llm_id` is set.
- **`memories.retrieve()`**: `relevance_threshold` -> `post_processor.config.relevance_threshold` — Minimum relevance score for retrieved memories. Only applies when `reranker_id` is set.
- **`memories.retrieve()`**: `max_results` -> `post_processor.config.max_results` — Maximum number of retrieved memories to return. Must be positive. Only applies when `llm_id` or `reranker_id` is set.
- **`memories.retrieve()`**: `prompt` -> `post_processor.config.prompt` — Custom prompt for LLM post-processing. If unset, the server's default prompt is used. Only applies when `llm_id` is set.
- **`memories.retrieve()`**: `sys_prompt` -> `post_processor.config.sys_prompt` — System prompt for LLM post-processing. If unset, the server's default system prompt is used. Only applies when `llm_id` is set.
- **`memories.retrieve()`**: `chronological_resort` -> `post_processor.config.chronological_resort` — Re-sort retrieved memories chronologically after semantic ranking. Only applies when `llm_id` or `reranker_id` is set.
- **`rerankers.create()`**: `api_key` -> `credentials` — Converts a plain API key string to the full `EndpointAuthentication` structure (i.e. `{"kind": "CREDENTIAL_KIND_API_KEY", "api_key": {"inline_secret": "sk-..."}}`).
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

Import from `goodmem.models`:

- **Responses**: `EmbedderResponse`, `RerankerResponse`, `LLMResponse`, `Space`, `Memory`, `ApiKeyResponse`, `UserResponse`
- **Create requests**: `EmbedderCreationRequest`, `RerankerCreationRequest`, `LLMCreationRequest`, `SpaceCreationRequest`
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
from goodmem.models.update_embedder_request import UpdateEmbedderRequest
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

# Get first page
page = client.spaces.list(page_size=10)
saved_token = page.next_token

# Later: resume from saved_token
for space in client.spaces.list(next_token=saved_token):
    print(space.space_id, space.name)
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
            ref = event.retrieved_item.chunk
            print(ref.chunk.chunk_text, ref.relevance_score)

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

## Errors

All errors inherit from `GoodMemError`. HTTP errors inherit from `APIError`.

| Status | Exception | Description |
|--------|-----------|-------------|
| 400 | `BadRequestError` | 400 Bad Request. |
| 401 | `AuthenticationError` | 401 Unauthorized. |
| 403 | `PermissionDeniedError` | 403 Forbidden. |
| 404 | `NotFoundError` | 404 Not Found. |
| 409 | `ConflictError` | 409 Conflict (e.g., duplicate resource). |
| 422 | `UnprocessableEntityError` | 422 Unprocessable Entity. |
| 429 | `RateLimitError` | 429 Too Many Requests. |
| 5xx | `InternalServerError` | 5xx Server Error. |

```python
from goodmem.errors import NotFoundError, ConflictError

try:
    client.embedders.get(id="nonexistent")
except NotFoundError:
    print("Not found")
```
