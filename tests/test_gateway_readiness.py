"""Credential-free regression tests for hosted gateway readiness setup."""

import io
from unittest.mock import Mock, call
from urllib.error import HTTPError, URLError

import pytest
import test_gateway_e2e as e2e

WAKING = (
    'Your GoodMem Cloud instance "test-instance" (https://example.invalid)'
    ' was paused and is still waking up. Nothing was sent to it; try again in a minute.'
)


@pytest.fixture
def clock(monkeypatch):
    class Clock:
        now = 0.0

        def sleep(self, delay):
            self.now += delay

    clock = Clock()
    clock.sleep = Mock(side_effect=clock.sleep)
    monkeypatch.setattr(e2e.time, "monotonic", lambda: clock.now)
    monkeypatch.setattr(e2e.time, "sleep", clock.sleep)
    return clock


@pytest.fixture
def gateway(monkeypatch):
    gateway = Mock(spec=e2e.Gateway)
    monkeypatch.setattr(e2e, "Gateway", Mock(return_value=gateway))
    return gateway


def test_ready_instance_needs_one_ping(gateway, clock):
    gateway.call.return_value = (False, {"healthy": True})

    assert e2e.gateway.__wrapped__() is gateway

    gateway.call.assert_called_once_with("goodmem_ping", timeout=120.0)
    clock.sleep.assert_not_called()


def test_cold_instance_can_become_ready_after_first_gateway_wake_budget(gateway, clock):
    def ping(name, *, timeout):
        assert name == "goodmem_ping"
        if gateway.call.call_count == 1:
            clock.now += 66
            return True, WAKING
        clock.now += 14
        return False, {"healthy": True}

    gateway.call.side_effect = ping

    assert e2e.gateway.__wrapped__() is gateway

    assert clock.now == 85
    assert gateway.call.call_args_list == [
        call("goodmem_ping", timeout=120.0),
        call("goodmem_ping", timeout=109.0),
    ]
    clock.sleep.assert_called_once_with(5.0)


def test_persistent_wake_fails_at_budget_with_last_response(gateway, clock):
    def ping(name, *, timeout):
        clock.now += min(66, timeout)
        return True, WAKING

    gateway.call.side_effect = ping

    with pytest.raises(AssertionError, match="readiness timed out after 180s") as error:
        e2e.gateway.__wrapped__()

    assert WAKING in str(error.value)
    assert "3 ping attempts" in str(error.value)
    assert clock.now == 180
    assert gateway.call.call_args_list == [
        call("goodmem_ping", timeout=120.0),
        call("goodmem_ping", timeout=109.0),
        call("goodmem_ping", timeout=38.0),
    ]
    assert clock.sleep.call_args_list == [call(5.0), call(5.0)]


def test_late_poll_does_not_start_another_ping(gateway, clock):
    gateway.call.return_value = (True, WAKING)

    def late_sleep(delay):
        clock.now += 181

    clock.sleep.side_effect = late_sleep
    with pytest.raises(AssertionError, match="readiness timed out"):
        e2e.gateway.__wrapped__()

    gateway.call.assert_called_once()


@pytest.mark.parametrize("payload", [
    "Authentication failed.",
    "The instance has been deleted.",
    "An unrelated tool is still waking up.",
    {"error": WAKING},
])
def test_other_tool_errors_fail_without_retry(gateway, clock, payload):
    gateway.call.return_value = (True, payload)

    with pytest.raises(AssertionError, match="goodmem_ping returned an error"):
        e2e.gateway.__wrapped__()

    gateway.call.assert_called_once()
    clock.sleep.assert_not_called()


@pytest.mark.parametrize("error", [
    HTTPError("https://example.invalid", 401, "Unauthorized", {}, None),
    HTTPError("https://example.invalid", 403, "Forbidden", {}, None),
    URLError("connection refused"),
    TimeoutError("ping timed out"),
])
def test_transport_and_auth_errors_are_not_retried(gateway, clock, error):
    gateway.call.side_effect = error

    with pytest.raises(type(error)) as raised:
        e2e.gateway.__wrapped__()

    assert raised.value is error
    gateway.call.assert_called_once()
    clock.sleep.assert_not_called()


def test_existing_not_responding_skip_is_preserved(gateway, clock):
    gateway.call.return_value = (True, "The instance is not responding.")

    with pytest.warns(UserWarning), pytest.raises(pytest.skip.Exception):
        e2e.gateway.__wrapped__()

    gateway.call.assert_called_once()
    clock.sleep.assert_not_called()


def test_ping_timeout_reaches_http_transport(monkeypatch):
    gateway = object.__new__(e2e.Gateway)
    gateway.url, gateway.token, gateway.session, gateway.n = (
        "https://example.invalid/mcp", "test-token", None, 0
    )
    response = io.BytesIO(
        b'{"jsonrpc":"2.0","id":1,"result":{"isError":false,"structuredContent":{"healthy":true}}}'
    )
    response.headers = {}
    urlopen = Mock(return_value=response)
    monkeypatch.setattr(e2e.urllib.request, "urlopen", urlopen)

    assert gateway.call("goodmem_ping", timeout=38.0) == (False, {"healthy": True})
    assert urlopen.call_args.kwargs == {"timeout": 38.0}
