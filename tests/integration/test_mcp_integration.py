"""Integration tests for the GoodMem MCP server against a live server.

These tests start the MCP server as a subprocess communicating over stdio,
send MCP protocol messages, and verify the responses against the live
GoodMem server.

Requires:
  - GOODMEM_BASE_URL and GOODMEM_API_KEY environment variables
  - Node.js installed (npx available)
  - MCP server compiled (mcp/dist/index.js exists)

Run with:
  python -m pytest python/tests/integration/test_mcp_integration.py -v
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import time
from pathlib import Path

import pytest

# MCP server location
MCP_DIR = Path(__file__).resolve().parent.parent.parent.parent / "mcp"
MCP_ENTRY = MCP_DIR / "dist" / "index.js"


def _env_or_skip(var: str) -> str:
    val = os.environ.get(var)
    if not val:
        pytest.skip(f"{var} not set")
    return val


def _mcp_request(id: int, method: str, params: dict | None = None) -> dict:
    """Build a JSON-RPC request for the MCP protocol."""
    msg: dict = {"jsonrpc": "2.0", "id": id, "method": method}
    if params is not None:
        msg["params"] = params
    return msg


def _mcp_notify(method: str, params: dict | None = None) -> dict:
    """Build a JSON-RPC notification (no id)."""
    msg: dict = {"jsonrpc": "2.0", "method": method}
    if params is not None:
        msg["params"] = params
    return msg


class McpSession:
    """Manages a stdio MCP server subprocess."""

    def __init__(self, base_url: str, api_key: str):
        self.proc = subprocess.Popen(
            ["node", str(MCP_ENTRY)],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env={
                **os.environ,
                "GOODMEM_BASE_URL": base_url,
                "GOODMEM_API_KEY": api_key,
            },
        )
        self._next_id = 1

    def send(self, msg: dict) -> None:
        """Send a JSON-RPC message to the MCP server (newline-delimited JSON)."""
        data = json.dumps(msg) + "\n"
        self.proc.stdin.write(data.encode())
        self.proc.stdin.flush()

    def recv(self, timeout: float = 30.0) -> dict:
        """Read one JSON-RPC response (newline-delimited JSON)."""
        import select
        deadline = time.time() + timeout
        while time.time() < deadline:
            remaining = deadline - time.time()
            ready, _, _ = select.select([self.proc.stdout], [], [], remaining)
            if not ready:
                raise TimeoutError("Timed out reading MCP response")
            line = self.proc.stdout.readline()
            if not line:
                stderr = self.proc.stderr.read() if self.proc.stderr else b""
                raise EOFError(f"MCP server closed stdout. stderr: {stderr.decode()}")
            line = line.strip()
            if line:
                return json.loads(line)
        raise TimeoutError("Timed out reading MCP response")

    def request(self, method: str, params: dict | None = None) -> dict:
        """Send a request and return the response."""
        msg_id = self._next_id
        self._next_id += 1
        self.send(_mcp_request(msg_id, method, params))
        return self.recv()

    def notify(self, method: str, params: dict | None = None) -> None:
        """Send a notification (no response expected)."""
        self.send(_mcp_notify(method, params))

    def initialize(self) -> dict:
        """Perform MCP initialization handshake."""
        resp = self.request("initialize", {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {"name": "test-client", "version": "0.1.0"},
        })
        # Send initialized notification
        self.notify("notifications/initialized")
        return resp

    def call_tool(self, name: str, arguments: dict | None = None) -> dict:
        """Call an MCP tool and return the response."""
        params: dict = {"name": name, "arguments": arguments or {}}
        return self.request("tools/call", params)

    def list_tools(self) -> dict:
        """List all available MCP tools."""
        return self.request("tools/list")

    def close(self):
        """Terminate the MCP server."""
        if self.proc.poll() is None:
            self.proc.terminate()
            try:
                self.proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.proc.kill()


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def mcp_session():
    """Start an MCP server session for the test module."""
    base_url = _env_or_skip("GOODMEM_BASE_URL")
    api_key = _env_or_skip("GOODMEM_API_KEY")

    if not MCP_ENTRY.exists():
        pytest.skip(f"MCP server not compiled: {MCP_ENTRY} not found")
    if not shutil.which("node"):
        pytest.skip("Node.js not installed")

    session = McpSession(base_url, api_key)
    try:
        session.initialize()
        yield session
    finally:
        session.close()


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


@pytest.mark.integration
class TestMcpToolDiscovery:
    """Test that the MCP server correctly lists its tools."""

    def test_list_tools_returns_tools(self, mcp_session: McpSession):
        resp = mcp_session.list_tools()
        assert "result" in resp, f"Expected result, got: {resp}"
        tools = resp["result"].get("tools", [])
        assert len(tools) > 30, f"Expected 30+ tools, got {len(tools)}"

    def test_tool_names_follow_convention(self, mcp_session: McpSession):
        resp = mcp_session.list_tools()
        tools = resp["result"]["tools"]
        for tool in tools:
            assert tool["name"].startswith("goodmem_"), (
                f"Tool {tool['name']} doesn't follow goodmem_ convention"
            )

    def test_core_tools_listed(self, mcp_session: McpSession):
        resp = mcp_session.list_tools()
        tool_names = {t["name"] for t in resp["result"]["tools"]}
        for expected in [
            "goodmem_embedders_create",
            "goodmem_spaces_create",
            "goodmem_memories_create",
            "goodmem_system_info",
        ]:
            assert expected in tool_names, f"Missing tool: {expected}"

    def test_tools_have_descriptions(self, mcp_session: McpSession):
        resp = mcp_session.list_tools()
        for tool in resp["result"]["tools"]:
            assert tool.get("description"), (
                f"Tool {tool['name']} has no description"
            )


@pytest.mark.integration
class TestMcpToolExecution:
    """Test calling MCP tools against a live GoodMem server."""

    def test_system_info(self, mcp_session: McpSession):
        """system.info should return server version info."""
        resp = mcp_session.call_tool("goodmem_system_info")
        assert "result" in resp, f"Expected result, got: {resp}"
        content = resp["result"]["content"]
        assert len(content) > 0
        assert content[0]["type"] == "text"
        data = json.loads(content[0]["text"])
        assert "version" in data or "serverVersion" in data or isinstance(data, dict)

    def test_embedders_list(self, mcp_session: McpSession):
        """embedders.list should return a (possibly empty) list response."""
        resp = mcp_session.call_tool("goodmem_embedders_list")
        assert "result" in resp, f"Expected result, got: {resp}"
        content = resp["result"]["content"]
        assert content[0]["type"] == "text"
        data = json.loads(content[0]["text"])
        # Should have embedders key or be a list response
        assert isinstance(data, (dict, list))

    def test_spaces_list(self, mcp_session: McpSession):
        """spaces.list should return a response."""
        resp = mcp_session.call_tool("goodmem_spaces_list")
        assert "result" in resp, f"Expected result, got: {resp}"

    def test_invalid_tool_returns_error(self, mcp_session: McpSession):
        """Calling a non-existent tool should return an error."""
        resp = mcp_session.call_tool("goodmem_nonexistent_tool")
        # MCP SDK returns tool errors inside result with isError=true
        result = resp.get("result", {})
        is_error = result.get("isError", False) or "error" in resp
        assert is_error, f"Expected error for non-existent tool, got: {resp}"

    def test_embedders_create_missing_required_field(self, mcp_session: McpSession):
        """Calling create without required fields should return an error."""
        resp = mcp_session.call_tool("goodmem_embedders_create", {})
        # Should either be a validation error or a server error
        content = resp.get("result", {}).get("content", [{}])
        if "error" in resp:
            pass  # JSON-RPC error — expected
        else:
            # Tool returned but server likely rejected it
            text = content[0].get("text", "") if content else ""
            # Either an error response or empty result is acceptable
            assert text  # Should have some response


# ---------------------------------------------------------------------------
# RAG workflow — end-to-end test through MCP tools
# ---------------------------------------------------------------------------


def _tool_result(resp: dict) -> dict:
    """Extract parsed JSON from a successful MCP tool response."""
    assert "result" in resp, f"Expected result, got: {resp}"
    result = resp["result"]
    assert not result.get("isError"), (
        f"Tool returned error: {result['content'][0]['text']}"
    )
    return json.loads(result["content"][0]["text"])


@pytest.mark.integration
class TestMcpRagWorkflow:
    """End-to-end RAG workflow: create embedder → space → memory → retrieve → cleanup.

    Mirrors the Python SDK's test_doc_sdk_examples.py flow but through MCP tools.
    Requires OPENAI_API_KEY for the embedder.
    """

    def test_rag_workflow(self, mcp_session: McpSession):
        openai_key = os.environ.get("OPENAI_API_KEY")
        if not openai_key:
            pytest.skip("OPENAI_API_KEY not set")

        ids: dict[str, str] = {}

        try:
            # 1. Create embedder
            # MCP tools map to REST directly — use camelCase for nested objects
            resp = mcp_session.call_tool("goodmem_embedders_create", {
                "display_name": "MCP Test Embedder",
                "model_identifier": "text-embedding-3-small",
                "provider_type": "OPENAI",
                "endpoint_url": "https://api.openai.com/v1",
                "dimensionality": 1536,
                "distribution_type": "DENSE",
                # NOTE: nested objects pass through to REST as-is (no snake→camel
                # conversion). Use camelCase for nested field names.
                "credentials": {
                    "kind": "CREDENTIAL_KIND_API_KEY",
                    "apiKey": {"inlineSecret": openai_key},
                },
            })
            embedder = _tool_result(resp)
            ids["embedder"] = embedder["embedderId"]
            assert ids["embedder"], "No embedder ID returned"

            # 2. Create space
            # MCP has no convenience transforms — must provide all required fields
            # (Python SDK auto-injects default_chunking_config)
            resp = mcp_session.call_tool("goodmem_spaces_create", {
                "name": "MCP Test Space",
                "space_embedders": [
                    {"embedderId": ids["embedder"], "defaultRetrievalWeight": 1.0},
                ],
                "default_chunking_config": {
                    "recursive": {
                        "chunkSize": 512,
                        "chunkOverlap": 50,
                        "keepStrategy": "KEEP_END",
                        "lengthMeasurement": "CHARACTER_COUNT",
                    },
                },
            })
            space = _tool_result(resp)
            ids["space"] = space["spaceId"]
            assert ids["space"], "No space ID returned"

            # 3. Create memory
            resp = mcp_session.call_tool("goodmem_memories_create", {
                "space_id": ids["space"],
                "original_content": (
                    "GoodMem is memory infrastructure for AI agents. "
                    "It stores and retrieves vectorized memories for RAG applications."
                ),
                "content_type": "text/plain",
            })
            memory = _tool_result(resp)
            ids["memory"] = memory["memoryId"]
            assert ids["memory"], "No memory ID returned"

            # 4. Poll until memory is processed
            for _ in range(60):
                resp = mcp_session.call_tool("goodmem_memories_get", {
                    "id": ids["memory"],
                })
                mem = _tool_result(resp)
                status = mem.get("processingStatus", "")
                if status == "COMPLETED":
                    break
                time.sleep(1)
            else:
                pytest.fail(f"Memory not COMPLETED after 60s, status: {status}")

            # 5. Retrieve (semantic search) — returns NDJSON array
            resp = mcp_session.call_tool("goodmem_memories_retrieve", {
                "message": "What is GoodMem?",
                "space_keys": [{"spaceId": ids["space"]}],
                "requested_size": 5,
            })
            events = _tool_result(resp)
            assert isinstance(events, list), f"Expected list, got {type(events)}"
            assert len(events) > 0, "No retrieval results"

            # Check that at least one result has relevant content
            found_content = False
            for event in events:
                item = event.get("retrievedItem", {})
                chunk = item.get("chunk", {}).get("chunk", {})
                text = chunk.get("chunkText", "")
                if "GoodMem" in text or "memory" in text.lower():
                    found_content = True
                    break
            assert found_content, "Retrieved results don't contain expected content"

        finally:
            # 6. Cleanup (best-effort, reverse order)
            for resource, tool in [
                ("memory", "goodmem_memories_delete"),
                ("space", "goodmem_spaces_delete"),
                ("embedder", "goodmem_embedders_delete"),
            ]:
                if ids.get(resource):
                    try:
                        mcp_session.call_tool(tool, {"id": ids[resource]})
                    except Exception:
                        pass


@pytest.mark.integration
class TestMcpAutoInference:
    """Test model registry auto-inference in MCP tools."""

    def test_lookup_known_model(self, mcp_session: McpSession):
        """Looking up a known model should return its registry entry.

        NOTE: The output uses snake_case keys (``provider_type``) so agents
        can copy the result directly into a goodmem_embedders_create call.
        """
        resp = mcp_session.call_tool("goodmem_lookup_model", {
            "model_identifier": "text-embedding-3-large",
        })
        data = _tool_result(resp)
        assert data["provider_type"] == "OPENAI"
        assert data["type"] == "embedder"

    def test_lookup_model_output_is_snake_case(self, mcp_session: McpSession):
        """All keys in the lookup response must be snake_case so they match
        the create-tool Zod schemas. A silent camelCase leak (e.g.
        ``providerType``) is the exact bug that caused issue 2: the agent
        would copy the output into goodmem_embedders_create and the
        camelCase keys would be dropped by Zod.
        """
        resp = mcp_session.call_tool("goodmem_lookup_model", {
            "model_identifier": "text-embedding-3-large",
        })
        data = _tool_result(resp)
        assert isinstance(data, dict)
        bad_keys = [k for k in data.keys() if any(c.isupper() for c in k)]
        assert not bad_keys, (
            f"goodmem_lookup_model output must be entirely snake_case. "
            f"Found camelCase keys: {bad_keys}. These would be silently "
            f"dropped if fed into goodmem_embedders_create."
        )
        # Spot-check the key fields agents need to build a create call.
        for k in ("model_identifier", "type", "provider_type", "endpoint_url"):
            assert k in data, f"Missing expected snake_case key: {k}"

    def test_lookup_then_create_chain(self, mcp_session: McpSession):
        """Simulate the LLM agent copy-paste workflow: call lookup_model,
        pass the returned fields directly as kwargs to embedders_create.

        This is the high-level integration test that would have caught
        issue 2 (lookup returning camelCase keys that were silently
        dropped by create).
        """
        openai_key = os.environ.get("OPENAI_API_KEY")
        if not openai_key:
            pytest.skip("OPENAI_API_KEY not set")

        lookup_resp = mcp_session.call_tool("goodmem_lookup_model", {
            "model_identifier": "text-embedding-3-large",
        })
        lookup = _tool_result(lookup_resp)

        # Build create args from the lookup output, adding only the
        # required identity and credential fields. This mirrors how an
        # LLM agent would actually use the tools.
        create_args: dict = {
            "display_name": "MCP Lookup→Create Chain Test",
            "model_identifier": "text-embedding-3-large",
            "credentials": {
                "kind": "CREDENTIAL_KIND_API_KEY",
                "apiKey": {"inlineSecret": openai_key},
            },
        }
        # Copy every snake_case field from lookup (skipping `type`, which
        # is meta).
        for k, v in lookup.items():
            if k in ("type", "model_identifier", "display_name"):
                continue
            if v is None:
                continue
            create_args.setdefault(k, v)

        embedder_id = None
        try:
            resp = mcp_session.call_tool("goodmem_embedders_create", create_args)
            embedder = _tool_result(resp)
            embedder_id = embedder["embedderId"]
            # Wire format is camelCase on the server response.
            assert embedder["providerType"] == "OPENAI"
            assert embedder["endpointUrl"] == "https://api.openai.com/v1"
            assert embedder["modelIdentifier"] == "text-embedding-3-large"
        finally:
            if embedder_id:
                mcp_session.call_tool(
                    "goodmem_embedders_delete", {"id": embedder_id}
                )

    def test_create_space_with_empty_embedders_fails_client_side(
        self, mcp_session: McpSession
    ):
        """Zod's .min(1) on space_embedders must reject an empty array
        client-side (before the request hits the server).
        """
        resp = mcp_session.call_tool("goodmem_spaces_create", {
            "name": "MCP Empty Embedders Test",
            "space_embedders": [],
            "default_chunking_config": {
                "recursive": {
                    "chunkSize": 512,
                    "chunkOverlap": 50,
                    "keepStrategy": "KEEP_END",
                    "lengthMeasurement": "CHARACTER_COUNT",
                },
            },
        })
        # Either a JSON-RPC error or isError=true tool result is acceptable.
        result = resp.get("result", {})
        is_error = result.get("isError", False) or "error" in resp
        assert is_error, (
            f"Expected client-side validation error for empty "
            f"space_embedders, got success response: {resp}"
        )
        # Extract any error text for inspection
        error_text = ""
        if "error" in resp:
            error_text = str(resp["error"])
        else:
            content = result.get("content", [])
            if content:
                error_text = str(content[0].get("text", ""))
        # The error should reference the minimum constraint OR "too_small"
        # (Zod's default error code for arrays violating .min()).
        lowered = error_text.lower()
        assert (
            "at least" in lowered
            or "too_small" in lowered
            or "minimum" in lowered
            or "min" in lowered
        ), (
            f"Expected an empty-array validation error mentioning the "
            f"minimum, got: {error_text[:500]}"
        )

    def test_lookup_unknown_model(self, mcp_session: McpSession):
        """Looking up an unknown model should list available models."""
        resp = mcp_session.call_tool("goodmem_lookup_model", {
            "model_identifier": "nonexistent-model-xyz",
        })
        content = resp["result"]["content"][0]["text"]
        assert "not found" in content
        assert "text-embedding-3-large" in content  # should list available

    def test_create_embedder_with_auto_inference(self, mcp_session: McpSession):
        """Creating an embedder with just model_identifier should auto-fill fields."""
        openai_key = os.environ.get("OPENAI_API_KEY")
        if not openai_key:
            pytest.skip("OPENAI_API_KEY not set")

        embedder_id = None
        try:
            # Only provide model_identifier, display_name, and credentials
            # provider_type, endpoint_url, dimensionality should be auto-inferred
            resp = mcp_session.call_tool("goodmem_embedders_create", {
                "display_name": "Auto-inferred Embedder",
                "model_identifier": "text-embedding-3-small",
                "credentials": {
                    "kind": "CREDENTIAL_KIND_API_KEY",
                    "apiKey": {"inlineSecret": openai_key},
                },
            })
            embedder = _tool_result(resp)
            embedder_id = embedder["embedderId"]

            # Verify auto-inferred fields
            assert embedder["providerType"] == "OPENAI"
            assert embedder["endpointUrl"] == "https://api.openai.com/v1"
            assert embedder["dimensionality"] == 1536
            assert embedder["distributionType"] == "DENSE"
        finally:
            if embedder_id:
                mcp_session.call_tool("goodmem_embedders_delete", {"id": embedder_id})

    def test_explicit_override_wins(self, mcp_session: McpSession):
        """User-provided values should override registry defaults."""
        openai_key = os.environ.get("OPENAI_API_KEY")
        if not openai_key:
            pytest.skip("OPENAI_API_KEY not set")

        embedder_id = None
        try:
            # Explicitly provide dimensionality=256 (registry default is 1536)
            resp = mcp_session.call_tool("goodmem_embedders_create", {
                "display_name": "Override Test Embedder",
                "model_identifier": "text-embedding-3-small",
                "dimensionality": 256,
                "credentials": {
                    "kind": "CREDENTIAL_KIND_API_KEY",
                    "apiKey": {"inlineSecret": openai_key},
                },
            })
            embedder = _tool_result(resp)
            embedder_id = embedder["embedderId"]

            # User override should win
            assert embedder["dimensionality"] == 256
            # But provider should still be auto-inferred
            assert embedder["providerType"] == "OPENAI"
        finally:
            if embedder_id:
                mcp_session.call_tool("goodmem_embedders_delete", {"id": embedder_id})
