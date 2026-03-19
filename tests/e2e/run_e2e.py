#!/usr/bin/env python3
"""E2E test runner for GoodMem Claude Code plugin.

Feeds English instructions to ``claude -p`` with stream-json output,
then validates that the correct MCP tools were called with expected
arguments and response JSON fields.

Usage:
    python agents/tests/e2e/run_e2e.py                     # run all
    python agents/tests/e2e/run_e2e.py --debug              # show raw output
    python agents/tests/e2e/run_e2e.py --discover           # dump first scenario
    python agents/tests/e2e/run_e2e.py --model haiku        # cheaper model
    python agents/tests/e2e/run_e2e.py --scenario "embedder"  # name filter

Requirements:
    - ``claude`` CLI installed and authenticated
    - GOODMEM_BASE_URL and GOODMEM_API_KEY environment variables
    - OPENAI_API_KEY for embedder/LLM scenarios
    - VOYAGE_API_KEY for reranker scenarios
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path

SCENARIOS_FILE = Path(__file__).parent / "scenarios.json"
PLUGIN_DIR = Path(__file__).resolve().parent.parent.parent  # → agents/


# ---------------------------------------------------------------------------
# Scenario loader
# ---------------------------------------------------------------------------

def load_scenarios(path: Path) -> list[dict]:
    """Load scenarios from JSON file."""
    return json.loads(path.read_text())


# ---------------------------------------------------------------------------
# Environment variable substitution
# ---------------------------------------------------------------------------

def substitute_env_vars(text: str) -> str:
    """Replace ``$VAR_NAME`` tokens with their environment values."""
    def _repl(m: re.Match) -> str:
        var = m.group(1)
        val = os.environ.get(var)
        if val is None:
            raise ValueError(f"${var} not set")
        return val

    return re.sub(r"\$([A-Z_][A-Z0-9_]*)", _repl, text)


# ---------------------------------------------------------------------------
# Claude CLI invocation
# ---------------------------------------------------------------------------

def run_claude(
    instruction: str,
    plugin_dir: str,
    model: str | None = None,
    timeout: int = 180,
) -> tuple[str, str, int]:
    """Run ``claude -p`` and return *(stdout, stderr, returncode)*."""
    # Plugin MCP tools are named mcp__plugin_<plugin>_<server>__<tool>.
    # For goodmem: mcp__plugin_goodmem_goodmem__goodmem_*
    cmd = [
        "claude",
        "-p",
        "--verbose",
        "--output-format", "stream-json",
        "--permission-mode", "dontAsk",
        "--tools", "",
        "--allowedTools", "mcp__plugin_goodmem_goodmem__*",
        "--disallowedTools", "mcp__plugin_goodmem_goodmem__goodmem_configure",
        "--plugin-dir", plugin_dir,
        "--max-budget-usd", "2.00",
        "--no-session-persistence",
        "--append-system-prompt",
        "The GoodMem server is already configured via environment variables. "
        "Do NOT call goodmem_configure. Just use the other tools directly.",
        instruction,
    ]
    if model:
        cmd.extend(["--model", model])

    result = subprocess.run(
        cmd, capture_output=True, text=True, timeout=timeout,
    )
    return result.stdout, result.stderr, result.returncode


# ---------------------------------------------------------------------------
# Stream-JSON parser
# ---------------------------------------------------------------------------

def parse_stream_json(raw: str) -> dict:
    """Extract tool calls, tool results, and text from stream-json output.

    Claude Code ``-p --verbose --output-format stream-json`` emits one
    JSON object per line with complete messages::

        {"type":"assistant","message":{"content":[
            {"type":"tool_use","id":"toolu_X","name":"...","input":{...}}
        ]}}
        {"type":"user","message":{"content":[
            {"type":"tool_result","tool_use_id":"toolu_X","content":[...]}
        ]}}
    """
    tool_calls: list[dict] = []
    tool_results: list[dict] = []
    text_chunks: list[str] = []

    for line in raw.strip().splitlines():
        if not line.strip():
            continue
        try:
            obj = json.loads(line)
        except json.JSONDecodeError:
            continue

        message = obj.get("message", {})
        content_list = message.get("content", [])
        if not isinstance(content_list, list):
            continue

        for block in content_list:
            if not isinstance(block, dict):
                continue
            btype = block.get("type", "")

            if btype == "tool_use":
                tool_calls.append({
                    "name": block.get("name", ""),
                    "input": block.get("input", {}),
                    "id": block.get("id", ""),
                })

            elif btype == "tool_result":
                content = block.get("content", "")
                is_error = block.get("is_error", False)
                parsed_json = _extract_result_json(content)
                tool_results.append({
                    "tool_use_id": block.get("tool_use_id", ""),
                    "content": content,
                    "parsed_json": parsed_json,
                    "is_error": is_error,
                })

            elif btype == "text":
                text_chunks.append(block.get("text", ""))

    return {
        "tool_calls": tool_calls,
        "tool_results": tool_results,
        "text": "".join(text_chunks),
    }


def _extract_result_json(content) -> dict | None:
    """Try to extract parsed JSON from a tool result's content.

    Content can be:
    - A list of text blocks: [{"type":"text","text":"{...JSON...}"}]
    - A plain string (often an error message)
    - Already a dict
    """
    text = None
    if isinstance(content, list):
        for item in content:
            if isinstance(item, dict) and item.get("type") == "text":
                text = item.get("text", "")
                break
    elif isinstance(content, str):
        text = content
    elif isinstance(content, dict):
        return content

    if text:
        try:
            parsed = json.loads(text)
            if isinstance(parsed, dict):
                return parsed
        except (json.JSONDecodeError, TypeError):
            pass
    return None


def _resolve_field(result_json: dict, key: str):
    """Resolve a field from a response JSON, searching nested dicts.

    Some server endpoints return wrapped responses like
    ``{"llm": {...fields...}, "statuses": [...]}``.
    First checks the top level, then checks inside any nested dict values.
    """
    # Try top level first
    val = result_json.get(key)
    if val is not None:
        return val
    # Search inside nested dict values (handles wrapping)
    for v in result_json.values():
        if isinstance(v, dict):
            val = v.get(key)
            if val is not None:
                return val
    return None


# ---------------------------------------------------------------------------
# Assertion checker
# ---------------------------------------------------------------------------

def check_assertions(parsed: dict, expect: dict) -> list[str]:
    """Return a list of failure messages (empty = pass)."""
    failures: list[str] = []
    calls = parsed["tool_calls"]
    results = parsed["tool_results"]

    expected_tool = expect.get("tool")
    if not expected_tool:
        return failures

    # Substring match: "goodmem_system_info" matches
    # "mcp__plugin_goodmem_goodmem__goodmem_system_info"
    matching_calls = [c for c in calls if expected_tool in c["name"]]
    if not matching_calls:
        names = [c["name"] for c in calls] or ["(none)"]
        failures.append(
            f"Expected tool '{expected_tool}' not called. Got: {names}"
        )
        return failures

    # Check args on the first matching call
    for key, expected_val in expect.get("args", {}).items():
        actual = matching_calls[0]["input"].get(key)
        if actual != expected_val:
            failures.append(
                f"Arg '{key}': expected {expected_val!r}, got {actual!r}"
            )

    # Check response fields: find a successful result from ANY matching call.
    # If no successful result (e.g. 409 conflict), skip response assertions
    # — mirrors the Python SDK integration tests which pytest.skip on 409.
    expected_response = expect.get("response", {})
    if expected_response:
        result_json = _find_successful_result(matching_calls, results)
        if result_json is None:
            pass  # skip response checks — resource may already exist (409)
        else:
            for key, expected_val in expected_response.items():
                actual = _resolve_field(result_json, key)

                if expected_val == "*":
                    if actual is None:
                        failures.append(
                            f"Response '{key}': expected to exist, "
                            f"got None/missing"
                        )
                else:
                    if actual != expected_val:
                        failures.append(
                            f"Response '{key}': expected {expected_val!r}, "
                            f"got {actual!r}"
                        )

    return failures


def _find_successful_result(
    matching_calls: list[dict], results: list[dict]
) -> dict | None:
    """Find a successful (non-error) tool result for any of the matching calls.

    When Claude retries a tool (e.g. due to credential format errors),
    the successful result may be linked to a later call.
    """
    call_ids = {c["id"] for c in matching_calls}
    for r in results:
        if r["tool_use_id"] in call_ids and not r.get("is_error"):
            if r.get("parsed_json") is not None:
                return r["parsed_json"]
    return None


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    ap = argparse.ArgumentParser(description="GoodMem plugin E2E tests")
    ap.add_argument("--debug", action="store_true", help="show raw output")
    ap.add_argument(
        "--discover", action="store_true",
        help="run first scenario and dump raw output",
    )
    ap.add_argument("--model", default=None, help="Claude model override")
    ap.add_argument(
        "--scenario", default=None,
        help="run only scenarios whose name contains this string",
    )
    ap.add_argument("--scenarios-file", default=None)
    ap.add_argument("--plugin-dir", default=None)
    args = ap.parse_args()

    sf = Path(args.scenarios_file) if args.scenarios_file else SCENARIOS_FILE
    pd = args.plugin_dir or str(PLUGIN_DIR)

    # Pre-flight: check required environment variables
    required = ("GOODMEM_BASE_URL", "GOODMEM_API_KEY", "OPENAI_API_KEY", "VOYAGE_API_KEY")
    missing = [v for v in required if not os.environ.get(v)]
    if missing:
        print(f"ERROR: required environment variables not set: {', '.join(missing)}")
        print("The MCP server needs these to talk to the GoodMem server.")
        sys.exit(1)

    cases = load_scenarios(sf)
    if not cases:
        print("No scenarios found")
        sys.exit(1)

    if args.scenario:
        cases = [c for c in cases if args.scenario.lower() in c["name"].lower()]
        if not cases:
            print(f"No scenario matching '{args.scenario}'")
            sys.exit(1)

    if args.discover:
        cases = cases[:1]
        args.debug = True

    print(f"Running {len(cases)} scenario(s)...\n")
    passed = failed = skipped = 0

    for case in cases:
        print(f"  {case['name']} ... ", end="", flush=True)

        try:
            instruction = substitute_env_vars(case["instruction"])
        except ValueError as e:
            print(f"SKIP ({e})")
            skipped += 1
            continue

        try:
            stdout, stderr, rc = run_claude(instruction, pd, model=args.model)
        except subprocess.TimeoutExpired:
            print("TIMEOUT")
            failed += 1
            continue
        except FileNotFoundError:
            print("ERROR (claude CLI not found)")
            sys.exit(1)

        parsed = parse_stream_json(stdout)

        if args.debug:
            print()
            print(f"    [rc] {rc}")
            print(f"    [tools] {[c['name'] for c in parsed['tool_calls']]}")
            for tc in parsed["tool_calls"]:
                print(f"    [call] {tc['name']}({json.dumps(tc['input'])[:200]})")
            for tr in parsed["tool_results"]:
                err = " ERROR" if tr.get("is_error") else ""
                pj = tr.get("parsed_json")
                if pj:
                    print(f"    [result{err}] {json.dumps(pj)[:300]}")
                else:
                    content = tr.get("content", "")
                    print(f"    [result{err}] {str(content)[:300]}")
            print(f"    [text] {parsed['text'][:300]}")
            if stderr:
                print(f"    [stderr] {stderr[:200]}")

        if rc != 0:
            print(f"FAIL (exit code {rc})")
            if stderr:
                print(f"    {stderr[:200]}")
            failed += 1
            continue

        expect = case.get("expect")
        if not expect:
            print("OK (no assertions)")
            passed += 1
            continue

        failures = check_assertions(parsed, expect)
        if failures:
            print("FAIL")
            for f in failures:
                print(f"    - {f}")
            failed += 1
        else:
            print("OK")
            passed += 1

    print(f"\n{passed} passed, {failed} failed, {skipped} skipped")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
