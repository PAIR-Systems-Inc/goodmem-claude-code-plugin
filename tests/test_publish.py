from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest

_PUBLISH_SCRIPT = Path(__file__).resolve().parents[1] / "publish.sh"
_TOP_LEVEL_PUBLISH_SCRIPT = Path(__file__).resolve().parents[2] / "publish.sh"


@pytest.fixture
def plugin_prefix() -> str:
    return "clients/claude"


def _run(repo: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        [*args],
        cwd=repo,
        check=False,
        capture_output=True,
        text=True,
    )
    if check and result.returncode != 0:
        raise AssertionError(
            f"command failed ({result.returncode}): {' '.join(args)}\n"
            f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
        )
    return result


def _git(repo: Path, *args: str, check: bool = True) -> str:
    return _run(repo, "git", *args, check=check).stdout.strip()


def _commit(repo: Path, message: str) -> str:
    _git(repo, "add", "-A")
    _git(repo, "commit", "-qm", message)
    return _git(repo, "rev-parse", "HEAD")


def _setup_repositories(tmp_path: Path, plugin_prefix: str) -> tuple[Path, Path, str]:
    outer = tmp_path / "outer"
    remote = tmp_path / "plugin.git"
    outer.mkdir()
    _git(outer, "init", "-q", "-b", "main")
    _git(outer, "config", "user.name", "Publisher Test")
    _git(outer, "config", "user.email", "publisher-test@example.invalid")

    plugin = outer / plugin_prefix
    plugin.mkdir(parents=True)
    shutil.copy2(_PUBLISH_SCRIPT, plugin / "publish.sh")
    top_level_publish = outer / "clients" / "publish.sh"
    top_level_publish.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(_TOP_LEVEL_PUBLISH_SCRIPT, top_level_publish)
    (plugin / "README.md").write_text("plugin v1\n")
    (outer / "OUTER_ONLY.md").write_text("must never enter the public plugin tree\n")
    _commit(outer, "initial monorepo")

    source_tree = _git(outer, "rev-parse", f"HEAD:{plugin_prefix}")
    seed = _run(
        outer,
        "git",
        "commit-tree",
        source_tree,
        check=True,
    )
    seed_commit = seed.stdout.strip()

    _git(tmp_path, "init", "--bare", "-q", str(remote))
    _git(outer, "push", "-q", str(remote), f"{seed_commit}:refs/heads/main")
    _git(outer, "remote", "add", "goodmem-plugin", str(remote))
    return outer, remote, seed_commit


def _remote_head(remote: Path) -> str:
    return _git(remote, "rev-parse", "refs/heads/main")


def test_unchanged_tree_is_a_noop(tmp_path: Path, plugin_prefix: str) -> None:
    outer, remote, before = _setup_repositories(tmp_path, plugin_prefix)

    result = _run(outer, f"./{plugin_prefix}/publish.sh", "--dry-run")

    assert "verifying write access anyway" in result.stdout
    assert "Dry run complete" in result.stdout
    assert _remote_head(remote) == before


def test_top_level_dispatch_works_from_documented_cwd(tmp_path: Path, plugin_prefix: str) -> None:
    outer, remote, before = _setup_repositories(tmp_path, plugin_prefix)

    result = _run(outer, "./clients/publish.sh", "claude", "--dry-run")

    assert "Claude Plugin Snapshot Sync" in result.stdout
    assert "Dry run complete" in result.stdout
    assert _remote_head(remote) == before


def test_dry_run_checks_push_without_changing_remote(tmp_path: Path, plugin_prefix: str) -> None:
    outer, remote, before = _setup_repositories(tmp_path, plugin_prefix)
    (outer / plugin_prefix / "README.md").write_text("plugin updated\n")
    _commit(outer, "update plugin")

    result = _run(outer, f"./{plugin_prefix}/publish.sh", "--dry-run")

    assert "Dry run complete" in result.stdout
    assert _remote_head(remote) == before


def test_real_publish_is_fast_forward_and_exact_tree(tmp_path: Path, plugin_prefix: str) -> None:
    outer, remote, before = _setup_repositories(tmp_path, plugin_prefix)
    (outer / plugin_prefix / "README.md").write_text("plugin updated\n")
    _commit(outer, "update plugin")
    source_tree = _git(outer, "rev-parse", f"HEAD:{plugin_prefix}")

    _run(outer, f"./{plugin_prefix}/publish.sh")

    after = _remote_head(remote)
    assert after != before
    assert _git(remote, "rev-parse", f"{after}^") == before
    assert _git(remote, "rev-parse", f"{after}^{{tree}}") == source_tree
    names = _git(remote, "ls-tree", "-r", "--name-only", after).splitlines()
    assert "README.md" in names
    assert "publish.sh" in names
    assert "OUTER_ONLY.md" not in names


def test_missing_remote_fails_for_dry_run_and_real_publish(
    tmp_path: Path,
    plugin_prefix: str,
) -> None:
    outer, _, _ = _setup_repositories(tmp_path, plugin_prefix)
    _git(outer, "remote", "remove", "goodmem-plugin")

    dry_run = _run(outer, f"./{plugin_prefix}/publish.sh", "--dry-run", check=False)
    real = _run(outer, f"./{plugin_prefix}/publish.sh", check=False)

    assert dry_run.returncode != 0
    assert "not found" in dry_run.stdout
    assert real.returncode != 0
    assert "not found" in real.stdout


def test_push_failure_reports_actionable_diagnostics(
    tmp_path: Path,
    plugin_prefix: str,
) -> None:
    outer, remote, _ = _setup_repositories(tmp_path, plugin_prefix)
    hook = remote / "hooks" / "pre-receive"
    hook.write_text("#!/bin/sh\nexit 1\n")
    hook.chmod(0o755)
    (outer / plugin_prefix / "README.md").write_text("plugin updated\n")
    _commit(outer, "update plugin")

    result = _run(outer, f"./{plugin_prefix}/publish.sh", check=False)

    assert result.returncode != 0
    assert "GOODMEM_CLAUDE_PLUGIN_REPO_TOKEN" in result.stdout
    assert "Never force-push this mirror" in result.stdout


def test_missing_head_prefix_fails_before_remote_access(tmp_path: Path, plugin_prefix: str) -> None:
    outer, _, _ = _setup_repositories(tmp_path, plugin_prefix)
    script = (outer / plugin_prefix / "publish.sh").read_bytes()
    shutil.rmtree(outer / plugin_prefix)
    _commit(outer, "remove plugin tree")
    (outer / plugin_prefix).mkdir(parents=True)
    script_path = outer / plugin_prefix / "publish.sh"
    script_path.write_bytes(script)
    script_path.chmod(0o755)

    result = _run(outer, f"./{plugin_prefix}/publish.sh", "--dry-run", check=False)

    assert result.returncode != 0
    assert "HEAD does not contain" in result.stdout
