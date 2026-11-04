"""End-to-end tests of the plugin's gateway path, against a deployed GoodMem gateway.

CI cannot sign in through a browser, so these run with a gateway dev token
(goodmem-cloud-provisioning#5303): a pre-issued bearer bound to one scratch
instance, accepted on staging only. The scratch instance's own REST API is used
to plant a memory that fails processing and observe its status. Cleanup through
the gateway verifies that each deleted test memory is gone; failures fail the run.

Environment, all four required (the suite skips when any is missing):
  GOODMEM_GATEWAY_URL            the gateway's /mcp URL (CI: set in the gtool scenario)
  GOODMEM_GATEWAY_DEV_TOKEN      the dev token (Infisical GOODMEM_E2E_GATEWAY_DEV_TOKEN)
  GOODMEM_GATEWAY_INSTANCE_URL   the scratch instance's base URL (Infisical GOODMEM_E2E_GATEWAY_INSTANCE_URL)
  GOODMEM_GATEWAY_INSTANCE_KEY   that instance's gm_ API key (Infisical GOODMEM_E2E_GATEWAY_INSTANCE_KEY)
  GOODMEM_GATEWAY_EMBEDDER       optional; the embedder name for the suite's space (default: the first
                                 one not named "fake", which is right for the scratch instance)

gtool passes an absent Infisical secret through as the literal text ``${secret:NAME}``.
``_secret`` treats that as unset, so a missing secret skips the suite instead of sending
a placeholder bearer to the gateway and failing every test with a 401.

Isolation between runs: the token, the instance and one space, ``claude-plugin-ci``, are
shared by every run, and the gateway reports a failed memory once per space. So runs do not
overlap: the client integration job in clients-ci holds a concurrency group that queues them
(``queue: max``, first in first out). A space per run was the alternative and does not work
here: the gateway cannot delete spaces (console-only), and the edge in front of a resumed
staging instance admits only GET and POST (2026-10-30), so nothing the suite can reach would
ever remove them. Within the shared space every memory carries the run tag in its text and
metadata, every search asserts on it, and a run starts by deleting, through the gateway, suite
memories that an earlier run left behind (a cancelled run skips its teardown).
"""

from __future__ import annotations

import base64
import json
import os
import re
import time
import urllib.error
import urllib.request
import uuid
import warnings
from pathlib import Path

import pytest

PLUGIN_DIR = Path(__file__).resolve().parent.parent
SPACE_NAME = "claude-plugin-ci"
RUN = os.environ.get("GITHUB_RUN_ID") or uuid.uuid4().hex[:8]
RUN_TAG = f"[suite run {RUN}]"
MEMORIES = [
    f"Atlas Coffee roasts its house espresso blend to 215C. {RUN_TAG}",
    f"Cupping happens at 09:00 every day; anything scoring under 84 is flagged. {RUN_TAG}",
]


def _secret(name: str) -> str:
    """An environment value, with gtool's unresolved ``${secret:NAME}`` placeholder read as unset."""
    value = os.environ.get(name, "").strip()
    return "" if value.startswith("${") else value


GATEWAY = _secret("GOODMEM_GATEWAY_URL")
TOKEN = _secret("GOODMEM_GATEWAY_DEV_TOKEN")
INSTANCE_URL = _secret("GOODMEM_GATEWAY_INSTANCE_URL").rstrip("/")
INSTANCE_KEY = _secret("GOODMEM_GATEWAY_INSTANCE_KEY")
EMBEDDER = os.environ.get("GOODMEM_GATEWAY_EMBEDDER", "")

_MISSING = [
    name
    for name, value in (
        ("GOODMEM_GATEWAY_URL", GATEWAY),
        ("GOODMEM_GATEWAY_DEV_TOKEN", TOKEN),
        ("GOODMEM_GATEWAY_INSTANCE_URL", INSTANCE_URL),
        ("GOODMEM_GATEWAY_INSTANCE_KEY", INSTANCE_KEY),
    )
    if not value
]
pytestmark = pytest.mark.skipif(
    bool(_MISSING),
    reason=f"gateway e2e needs {', '.join(_MISSING)} (unset, or an unresolved ${{secret:NAME}} reference)",
)


class Gateway:
    """A minimal MCP streamable-HTTP client: initialize once, then tools/call."""

    def __init__(self, url: str, token: str):
        self.url, self.token, self.session, self.n = url, token, None, 0
        init = self._post({"jsonrpc": "2.0", "id": self._next(), "method": "initialize", "params": {
            "protocolVersion": "2025-06-18", "capabilities": {},
            "clientInfo": {"name": "claude-plugin-ci", "version": "0"}}})
        self.server_info = init["result"]["serverInfo"]
        self._post({"jsonrpc": "2.0", "method": "notifications/initialized"}, expect_reply=False)

    def _next(self) -> int:
        self.n += 1
        return self.n

    def _post(self, body: dict, expect_reply: bool = True) -> dict:
        headers = {"Content-Type": "application/json", "Accept": "application/json, text/event-stream",
                   "Authorization": "Bearer " + self.token, "MCP-Protocol-Version": "2025-06-18"}
        if self.session:
            headers["mcp-session-id"] = self.session
        request = urllib.request.Request(self.url, json.dumps(body).encode(), headers)
        try:
            with urllib.request.urlopen(request, timeout=120) as response:
                self.session = response.headers.get("mcp-session-id", self.session)
                raw = response.read().decode()
        except urllib.error.HTTPError as error:
            raise AssertionError(f"gateway HTTP {error.code} on {body.get('method')}: {error.read()[:300]!r}") from None
        if not expect_reply:
            return {}
        messages = [json.loads(line.removeprefix("data:"))
                    for line in raw.splitlines() if line.strip().startswith(("{", "data:"))]
        reply = next((m for m in messages if m.get("id") == body.get("id")), None)
        assert reply is not None, (
            f"{body.get('method')}: no reply carried request id {body.get('id')}; the gateway sent {raw[:300]!r}")
        assert "error" not in reply, f"{body.get('method')} failed: {reply['error']}"
        return reply

    def tools(self) -> dict[str, dict]:
        return {t["name"]: t for t in self._post({"jsonrpc": "2.0", "id": self._next(), "method": "tools/list"})["result"]["tools"]}

    def call(self, name: str, arguments: dict | None = None) -> tuple[bool, dict | str]:
        result = self._post({"jsonrpc": "2.0", "id": self._next(), "method": "tools/call",
                             "params": {"name": name, "arguments": arguments or {}}})["result"]
        structured = result.get("structuredContent")
        text = "".join(c.get("text", "") for c in result.get("content", []) if c.get("type") == "text")
        if structured is None:
            try:
                structured = json.loads(text)
            except ValueError:
                structured = text
        return bool(result.get("isError")), structured

    def ok(self, name: str, arguments: dict | None = None) -> dict:
        is_error, payload = self.call(name, arguments)
        assert not is_error, f"{name} returned an error: {str(payload)[:400]}"
        assert isinstance(payload, dict), f"{name} returned no structured result: {str(payload)[:200]}"
        return payload


def _instance(method: str, path: str, body: dict | None = None) -> dict:
    """One call to the scratch instance's REST API with the suite's key. GET and POST only: the
    edge in front of a resumed staging instance answers every other method itself, with a 404."""
    data = json.dumps(body).encode() if body is not None else None
    headers = {"x-api-key": INSTANCE_KEY}
    if data is not None:
        headers["Content-Type"] = "application/json"
    request = urllib.request.Request(INSTANCE_URL + path, data, headers, method=method)
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            raw = response.read()
    except urllib.error.HTTPError as error:
        hint = " (the instance is probably paused; resume it in the console)" if error.code == 503 else ""
        raise AssertionError(f"instance {method} {path} -> HTTP {error.code}{hint}: {error.read()[:300]!r}") from None
    return json.loads(raw) if raw.strip() else {}


def test_dev_token_has_the_gateway_bearer_shape():
    """The gateway refuses any bearer that is not 32 random bytes in unpadded base64url (43 characters)
    before looking it up, so a mis-pasted secret shows up here as a shape error, never as a 401 that
    could also mean the gateway was not restarted with it. The token itself is never printed."""
    assert len(TOKEN) == 43, f"GOODMEM_GATEWAY_DEV_TOKEN is {len(TOKEN)} characters; the gateway's bearer format is 43 (openssl rand 32 | basenc --base64url | tr -d '=')"
    try:
        decoded = base64.urlsafe_b64decode(TOKEN + "=")
    except ValueError:
        pytest.fail("GOODMEM_GATEWAY_DEV_TOKEN is not unpadded base64url")
    assert len(decoded) == 32, f"GOODMEM_GATEWAY_DEV_TOKEN decodes to {len(decoded)} bytes, not 32"


@pytest.fixture(scope="module")
def gateway() -> Gateway:
    gateway = Gateway(GATEWAY, TOKEN)
    is_error, payload = gateway.call("goodmem_ping")
    if is_error and "not responding" in str(payload):
        # The gateway's wording for a paused or unreachable instance (instance_errors.go). That is
        # the scratch instance's state, not the plugin's behaviour, so the suite steps aside loudly
        # instead of failing every PR's integration job until someone resumes it.
        warnings.warn(f"gateway e2e skipped: {str(payload)[:300]}", stacklevel=1)
        pytest.skip(f"the scratch instance behind the dev token is not responding: {str(payload)[:200]}")
    assert not is_error, f"goodmem_ping returned an error: {str(payload)[:400]}"
    return gateway


def _cleanup_memories(gateway: Gateway, memory_ids: list[str]) -> None:
    """Delete every supplied test memory, verify absence, and report all cleanup failures."""
    failures = []
    for memory_id in memory_ids:
        try:
            gateway.ok("goodmem_memories_delete", {"memory_id": memory_id})
            is_error, payload = gateway.call("goodmem_memories_get", {"memory_id": memory_id})
            expected = f'No memory with ID "{memory_id}" exists on this instance.'
            assert is_error and payload == expected, (
                f"deletion was not verified: expected not-found for {memory_id}, got {payload!r}")
        except Exception as error:
            # Cleanup is a final boundary: attempt every known test memory before failing.
            failures.append(f"{memory_id}: {type(error).__name__}: {error}")
    assert not failures, "gateway test memory cleanup failed:\n" + "\n".join(failures)


def _sweep_leftover_memories(gateway: Gateway, space: str) -> None:
    """Delete suite memories another run left in the shared space (a cancelled run skips its teardown).
    Runs are serialized by the job's concurrency group, so anything tagged with another run id is a leftover."""
    listed = gateway.ok("goodmem_memories_list", {"space_id": space, "all": True}).get("memories", [])
    leftovers = [memory["memory_id"] for memory in listed
                 if (memory.get("metadata") or {}).get("suite") == "claude-plugin-ci"
                 and (memory.get("metadata") or {}).get("run") != RUN]
    _cleanup_memories(gateway, leftovers)


@pytest.fixture(scope="module")
def space(gateway: Gateway) -> str:
    """The shared suite space: found by name, created once. Never deleted (see the module docstring)."""
    spaces = gateway.ok("goodmem_spaces_list").get("spaces", [])
    existing = next((s["space_id"] for s in spaces if s.get("name") == SPACE_NAME), None)
    if existing is None:
        # The scratch instance also carries staging's placeholder embedder, so name a real one.
        embedders = gateway.ok("goodmem_embedders_list").get("embedders", [])
        usable = [e for e in embedders if (e.get("name") == EMBEDDER if EMBEDDER else "fake" not in (e.get("name") or "").lower())]
        assert usable, f"no usable embedder on the instance (GOODMEM_GATEWAY_EMBEDDER={EMBEDDER!r}): {[e.get('name') for e in embedders]}"
        created = gateway.ok("goodmem_spaces_create", {"name": SPACE_NAME, "embedder_name": usable[0]["name"]})
        existing = (created.get("created") or created)["space_id"]
    _sweep_leftover_memories(gateway, existing)
    return existing


@pytest.fixture(scope="module")
def saved(gateway: Gateway, space: str, request: pytest.FixtureRequest):
    """Save the suite's memories, wait until each one is processed, delete them afterwards."""
    ids = []
    # Register before creation so partial setup and processing failures still clean up known IDs.
    request.addfinalizer(lambda: _cleanup_memories(gateway, ids))
    for text in MEMORIES:
        result = gateway.ok("goodmem_memories_create", {
            "space_id": space, "content": text,
            "metadata": {"suite": "claude-plugin-ci", "run": RUN, "topic": "coffee"}})
        ids.append((result.get("created") or result)["memory_id"])
    deadline = time.time() + 180
    status: dict[str, str | None] = {}
    while time.time() < deadline:
        # By id, not from a list page: a list shows one page, and a filling space pushes new ids off it.
        status = {i: gateway.ok("goodmem_memories_get", {"memory_id": i}).get("memory", {}).get("processing_status") for i in ids}
        if all(s == "COMPLETED" for s in status.values()):
            break
        assert "FAILED" not in status.values(), f"a memory failed processing: {status}"
        time.sleep(5)
    else:
        pytest.fail(f"memories did not finish processing within 180 s: {status}")
    yield ids


def test_gateway_identity_and_health(gateway: Gateway):
    assert gateway.server_info.get("name"), gateway.server_info
    me = gateway.ok("goodmem_users_me")
    assert me.get("user", {}).get("email"), me
    ping = gateway.ok("goodmem_ping")
    assert ping.get("server_version", "").startswith("server-"), ping


def test_skill_names_only_tools_the_gateway_serves(gateway: Gateway):
    """Every goodmem_* / search / fetch name in the skill's gateway section exists on the gateway."""
    skill = (PLUGIN_DIR / "skills" / "mcp" / "SKILL.md").read_text()
    section = skill[skill.index("## `goodmem-gateway`"):]
    section = section[: section.find("\n## ", 1)] if "\n## " in section[1:] else section
    named = set(re.findall(r"`(goodmem_[a-z_]+|search|fetch)`", section))
    served = set(gateway.tools())
    missing = sorted(named - served)
    assert not missing, f"the skill names tools the gateway does not serve: {missing}"
    assert {"goodmem_memories_retrieve", "goodmem_spaces_list", "goodmem_console_setup"} <= served


def test_list_spaces_includes_the_suite_space(gateway: Gateway, space: str):
    listed = [s["space_id"] for s in gateway.ok("goodmem_spaces_list")["spaces"] if s.get("name") == SPACE_NAME]
    assert space in listed, f"the suite space {space} is not listed under {SPACE_NAME}: {listed}"


def test_save_then_retrieve_scoped(gateway: Gateway, space: str, saved: list[str]):
    result = gateway.ok("goodmem_memories_retrieve", {
        "message": "what temperature is the espresso blend roasted to", "space_ids": [space], "requested_size": 5})
    texts = [item.get("text", "") for item in result.get("items", [])]
    assert any("215C" in t and RUN_TAG in t for t in texts), result
    assert not result.get("skipped_spaces"), result


def test_retrieve_with_metadata_filter(gateway: Gateway, space: str, saved: list[str]):
    result = gateway.ok("goodmem_memories_retrieve", {
        "message": "cupping", "space_ids": [space],
        "metadata_filter": "CAST(val('$.topic') AS TEXT) = 'coffee'"})
    assert any("Cupping" in item.get("text", "") and RUN_TAG in item.get("text", "") for item in result.get("items", [])), result


def test_retrieve_with_answer(gateway: Gateway, space: str, saved: list[str]):
    """With answer=true the gateway synthesizes an answer through the instance's LLM."""
    result = gateway.ok("goodmem_memories_retrieve", {"message": "when is cupping", "space_ids": [space], "answer": True})
    assert result.get("items"), result
    assert not result.get("synthesis_error"), f"the scratch instance's LLM did not synthesize: {result['synthesis_error']}"
    assert "09:00" in result.get("answer", ""), result


def test_search_and_fetch(gateway: Gateway, saved: list[str]):
    # Unscoped search spans every space on the instance; the run tag picks this run's memory.
    found = gateway.ok("search", {"query": f"espresso blend roasted {RUN_TAG}"})
    hit = next((r for r in found.get("results", []) if "215C" in r.get("text", "") and RUN_TAG in r.get("text", "")), None)
    assert hit, f"search did not return this run's espresso memory: {found}"
    fetched = gateway.ok("fetch", {"id": hit["id"]})
    assert "215C" in json.dumps(fetched), fetched


def test_nonexistent_space_is_skipped_not_fatal(gateway: Gateway, space: str, saved: list[str]):
    result = gateway.ok("goodmem_memories_retrieve", {
        "message": "espresso", "space_ids": [space, "00000000-0000-0000-0000-000000000000"]})
    assert result.get("items"), result
    skipped = {s["space_id"]: s.get("error", "") for s in result.get("skipped_spaces", [])}
    assert "00000000-0000-0000-0000-000000000000" in skipped, result
    assert "not found" in skipped["00000000-0000-0000-0000-000000000000"].lower()


def test_deleting_a_missing_memory_reports_not_found(gateway: Gateway):
    is_error, payload = gateway.call("goodmem_memories_delete", {"memory_id": str(uuid.uuid4())})
    assert is_error, payload
    assert "no memory" in str(payload).lower() or "not found" in str(payload).lower(), payload


def test_failed_memory_in_a_searched_space_is_counted(
    gateway: Gateway, space: str, saved: list[str], request: pytest.FixtureRequest
):
    """A memory that fails processing in a space that is still searchable shows up as failed_count.

    The gateway's failure diagnostic (failures.go) is throttled to one instance check per grant and
    space every 30 s, and it reports a failure ONCE, the first time it sees that memory id; later
    calls treat it as known and omit failed_count. So the wait for FAILED goes through the instance
    directly, not through gateway calls that would consume the one report, and the retrieve is
    retried past the throttle window. Runs are serialized by the job's concurrency group, so no
    other run can use the report up first.
    """
    # A PNG that does not decode fails in seconds. A malformed PDF is the wrong bait: on staging it
    # sat in PROCESSING for over three minutes (2026-10-27), the page-image pipeline never giving up.
    planted = _instance("POST", "/v1/memories", {
        "spaceId": space, "originalContentB64": base64.b64encode(b"notapng\x00\x01\x02").decode(),
        "contentType": "image/png", "metadata": {"suite": "claude-plugin-ci", "run": RUN, "broken": True}})["memoryId"]
    request.addfinalizer(lambda: _cleanup_memories(gateway, [planted]))
    status = None
    for _ in range(36):
        status = _instance("GET", f"/v1/memories/{planted}").get("processingStatus")
        if status == "FAILED":
            break
        time.sleep(5)
    assert status == "FAILED", f"planted memory ended as {status}"
    result = None
    for _ in range(10):  # the diagnostic's throttle is 30 s; the first unthrottled check after the failure reports it
        result = gateway.ok("goodmem_memories_retrieve", {"message": "espresso", "space_ids": [space]})
        assert result.get("items"), result
        if result.get("failed_count", 0) >= 1:
            break
        time.sleep(5)
    assert result.get("failed_count", 0) >= 1, f"retrieve never reported the failed memory within 50 s: {result}"
