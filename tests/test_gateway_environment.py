"""Check that the gateway in .mcp.json signs users in to the intended environment.

The plugin hardcodes the hosted gateway URL. A wrong host (for example a staging
deployment) would sign every user into the wrong GoodMem environment and store
their memories there, and nothing else in the repo would notice. This test
follows the OAuth flow as far as it can go without a browser:

1. ``/.well-known/oauth-protected-resource`` names the configured URL as the resource.
2. ``/.well-known/oauth-authorization-server`` is served by the gateway host and
   offers dynamic client registration, which Claude Code requires.
3. The sign-in redirect itself (``/authorize`` sending the browser to the intended
   environment's sign-in page) is checked by the scheduled GATEWAY-E2E probe in
   goodmem-cloud-provisioning, daily on both gateways. That check needs a registered OAuth
   client, and registering one per CI run left a record on the production gateway each time
   (review of #1815, 30 Oct), so it is not done here.

This file contacts the PRODUCTION gateway, so it is opt-in: nothing runs unless
``GOODMEM_GATEWAY_ENVIRONMENT_CHECK=1`` is set. The MCP integration scenario,
``clients_gen.sh`` and a bare ``pytest`` all collect this directory, and none of
them should turn red because the production gateway is unreachable, or contact it
at all. The dedicated clients-ci step sets the variable; every other caller sees
the file skip.

Run with:
  GOODMEM_GATEWAY_ENVIRONMENT_CHECK=1 python -m pytest clients/claude/tests/test_gateway_environment.py -v
"""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

import pytest

PLUGIN_DIR = Path(__file__).resolve().parent.parent
MCP_JSON = PLUGIN_DIR / ".mcp.json"
SERVER_NAME = "goodmem-gateway"
TIMEOUT = 15

pytestmark = [
    pytest.mark.gateway_environment,
    pytest.mark.skipif(
        os.environ.get("GOODMEM_GATEWAY_ENVIRONMENT_CHECK") != "1",
        reason="contacts the production gateway; opt in with GOODMEM_GATEWAY_ENVIRONMENT_CHECK=1",
    ),
]


def _get(url: str) -> tuple[int, dict, dict]:
    """GET without following redirects. Returns (status, headers, json-or-empty)."""

    class NoRedirect(urllib.request.HTTPRedirectHandler):
        def redirect_request(self, *args, **kwargs):
            return None

    opener = urllib.request.build_opener(NoRedirect)
    try:
        with opener.open(url, timeout=TIMEOUT) as res:
            body = res.read().decode("utf-8", "replace")
            headers = dict(res.headers)
            status = res.status
    except urllib.error.HTTPError as err:
        body = err.read().decode("utf-8", "replace")
        headers = dict(err.headers)
        status = err.code
    try:
        data = json.loads(body) if body.strip().startswith("{") else {}
    except json.JSONDecodeError:
        data = {}
    return status, headers, data


@pytest.fixture(scope="module")
def gateway_url() -> str:
    servers = json.loads(MCP_JSON.read_text())["mcpServers"]
    assert SERVER_NAME in servers, f"{SERVER_NAME} missing from {MCP_JSON}"
    url = servers[SERVER_NAME]["url"]
    assert url.startswith("https://"), f"gateway URL must be https: {url}"
    return url


@pytest.fixture(scope="module")
def gateway_origin(gateway_url: str) -> str:
    parts = urllib.parse.urlsplit(gateway_url)
    return f"{parts.scheme}://{parts.netloc}"


def test_mcp_endpoint_requires_auth(gateway_url: str) -> None:
    """The MCP endpoint must exist and demand a bearer token, not answer anonymously."""
    status, _, _ = _get(gateway_url)
    assert status in (401, 405), f"expected 401/405 from {gateway_url}, got {status}"


def test_protected_resource_metadata_names_the_configured_url(
    gateway_url: str, gateway_origin: str
) -> None:
    status, _, meta = _get(f"{gateway_origin}/.well-known/oauth-protected-resource")
    assert status == 200, f"no protected-resource metadata on {gateway_origin}"
    assert meta.get("resource") == gateway_url, (
        f"metadata resource {meta.get('resource')!r} != configured {gateway_url!r}"
    )
    assert gateway_origin in meta.get("authorization_servers", [])


def test_authorization_server_supports_claude_code(gateway_origin: str) -> None:
    status, _, meta = _get(f"{gateway_origin}/.well-known/oauth-authorization-server")
    assert status == 200
    assert meta.get("issuer") == gateway_origin
    assert meta.get("registration_endpoint"), "Claude Code needs dynamic client registration"
    assert "S256" in meta.get("code_challenge_methods_supported", [])
    assert "authorization_code" in meta.get("grant_types_supported", [])
