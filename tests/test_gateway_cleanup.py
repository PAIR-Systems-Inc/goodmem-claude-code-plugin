"""Credential-free regression tests for gateway e2e memory cleanup."""

from unittest.mock import Mock, call
from urllib.error import URLError

import pytest

import test_gateway_e2e as e2e


def not_found(memory_id: str) -> tuple[bool, str]:
    return True, f'No memory with ID "{memory_id}" exists on this instance.'


@pytest.fixture
def gateway():
    gateway = object.__new__(e2e.Gateway)
    gateway.call = Mock()
    return gateway


def test_cleanup_verifies_deleted_memory_is_absent(gateway):
    gateway.call.side_effect = [(False, {"deleted": "memory"}), not_found("memory")]

    e2e._cleanup_memories(gateway, ["memory"])

    assert gateway.call.call_args_list == [
        call("goodmem_memories_delete", {"memory_id": "memory"}),
        call("goodmem_memories_get", {"memory_id": "memory"}),
    ]


@pytest.mark.parametrize("response", [
    (False, {"memory": {"memory_id": "memory"}}),
    (True, "The instance is not responding."),
    not_found("another-memory"),
])
def test_cleanup_rejects_a_surviving_memory_or_unrelated_error(gateway, response):
    gateway.call.side_effect = [(False, {"deleted": "memory"}), response]

    with pytest.raises(AssertionError, match="deletion was not verified"):
        e2e._cleanup_memories(gateway, ["memory"])


def test_cleanup_reports_all_failures_and_still_attempts_remaining_memories(gateway):
    gateway.call.side_effect = [
        (True, "Deletion is not permitted."),
        (False, {"deleted": "second"}), not_found("second"),
        URLError("connection refused"),
    ]

    with pytest.raises(AssertionError) as failure:
        e2e._cleanup_memories(gateway, ["first", "second", "third"])

    assert "first: AssertionError:" in str(failure.value)
    assert "third: URLError:" in str(failure.value)
    assert gateway.call.call_args_list == [
        call("goodmem_memories_delete", {"memory_id": "first"}),
        call("goodmem_memories_delete", {"memory_id": "second"}),
        call("goodmem_memories_get", {"memory_id": "second"}),
        call("goodmem_memories_delete", {"memory_id": "third"}),
    ]


def test_sweep_only_deletes_other_runs_suite_memories(gateway):
    gateway.call.side_effect = [
        (False, {"memories": [
            {"memory_id": "leftover", "metadata": {"suite": "claude-plugin-ci", "run": e2e.RUN + "-old"}},
            {"memory_id": "current", "metadata": {"suite": "claude-plugin-ci", "run": e2e.RUN}},
            {"memory_id": "unrelated", "metadata": {"suite": "another-suite"}},
            {"memory_id": "untagged", "metadata": None},
        ]}),
        (False, {"deleted": "leftover"}), not_found("leftover"),
    ]

    e2e._sweep_leftover_memories(gateway, "space")

    assert gateway.call.call_args_list == [
        call("goodmem_memories_list", {"space_id": "space", "all": True}),
        call("goodmem_memories_delete", {"memory_id": "leftover"}),
        call("goodmem_memories_get", {"memory_id": "leftover"}),
    ]


def test_sweep_reports_deletion_failure(gateway):
    gateway.call.side_effect = [
        (False, {"memories": [
            {"memory_id": "leftover", "metadata": {"suite": "claude-plugin-ci", "run": e2e.RUN + "-old"}},
        ]}),
        (True, "Deletion is not permitted."),
    ]

    with pytest.raises(AssertionError, match="gateway test memory cleanup failed"):
        e2e._sweep_leftover_memories(gateway, "space")


@pytest.mark.parametrize("failure_stage", ["creation", "processing"])
def test_saved_fixture_registers_cleanup_before_setup_can_fail(gateway, failure_stage):
    request = Mock(spec=pytest.FixtureRequest)
    responses = [(False, {"created": {"memory_id": "first"}})]
    ids = ["first"]
    if failure_stage == "processing":
        responses.append((False, {"created": {"memory_id": "second"}}))
        ids.append("second")
    responses.append((True, "Setup failed."))
    for memory_id in ids:
        responses.extend([(False, {"deleted": memory_id}), not_found(memory_id)])
    gateway.call.side_effect = responses
    fixture = e2e.saved.__wrapped__(gateway, "space", request)

    with pytest.raises(AssertionError, match="Setup failed"):
        next(fixture)
    request.addfinalizer.assert_called_once()
    request.addfinalizer.call_args.args[0]()

    deleted = [args.args[1]["memory_id"] for args in gateway.call.call_args_list
               if args.args[0] == "goodmem_memories_delete"]
    assert deleted == ids


def test_failed_memory_registers_cleanup_before_status_probe_can_fail(gateway, monkeypatch):
    request = Mock(spec=pytest.FixtureRequest)
    monkeypatch.setattr(e2e, "_instance", Mock(side_effect=[
        {"memoryId": "broken"}, AssertionError("Status probe failed."),
    ]))
    gateway.call.side_effect = [(False, {"deleted": "broken"}), not_found("broken")]

    with pytest.raises(AssertionError, match="Status probe failed"):
        e2e.test_failed_memory_in_a_searched_space_is_counted(gateway, "space", [], request)
    request.addfinalizer.assert_called_once()
    request.addfinalizer.call_args.args[0]()

    assert gateway.call.call_args_list == [
        call("goodmem_memories_delete", {"memory_id": "broken"}),
        call("goodmem_memories_get", {"memory_id": "broken"}),
    ]
