#!/bin/bash
# Sync the claude/ tree to the public goodmem-claude-code-plugin repo.
#
# Usage:
#   ./publish.sh              # push a fast-forward snapshot to goodmem-plugin main
#   ./publish.sh --dry-run    # validate the snapshot and write access without pushing

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(git -C "$SCRIPT_DIR" rev-parse --show-toplevel 2>/dev/null || true)"
REMOTE="${GOODMEM_PLUGIN_REMOTE:-goodmem-plugin}"
BRANCH="${GOODMEM_PLUGIN_BRANCH:-main}"
dry_run="false"

usage() {
    cat <<'EOF'
Sync the claude/ tree to the goodmem-claude-code-plugin repo.

Usage:
  ./publish.sh [--dry-run]

Options:
  --dry-run    Validate the snapshot and remote write access; do not push.
  -h, --help   Show this help.
EOF
}

while [ $# -gt 0 ]; do
    case "$1" in
        --dry-run) dry_run="true" ;;
        -h|--help) usage; exit 0 ;;
        *)
            echo "Unknown option: $1"
            echo ""
            usage
            exit 1
            ;;
    esac
    shift
done

if [ -z "$REPO_ROOT" ]; then
    echo "ERROR: publish.sh must live inside a Git repository."
    exit 1
fi

cd "$REPO_ROOT"

SUBTREE_PREFIX="$(git -C "$SCRIPT_DIR" rev-parse --show-prefix)"
SUBTREE_PREFIX="${SUBTREE_PREFIX%/}"
if [ -z "$SUBTREE_PREFIX" ]; then
    echo "ERROR: unable to derive the Claude plugin prefix from $SCRIPT_DIR"
    exit 1
fi

source_tree="$(git rev-parse --verify "HEAD:${SUBTREE_PREFIX}" 2>/dev/null || true)"
if [ -z "$source_tree" ]; then
    echo "ERROR: HEAD does not contain the Claude plugin tree at ${SUBTREE_PREFIX}."
    exit 1
fi

echo "=== GoodMem Claude Plugin Snapshot Sync ==="
echo "Prefix: ${SUBTREE_PREFIX}"
echo "Remote: ${REMOTE} (${BRANCH})"

if ! git remote get-url "$REMOTE" >/dev/null 2>&1; then
    echo "ERROR: Remote '$REMOTE' not found."
    echo "Add it with:"
    echo "  git remote add $REMOTE git@github.com:PAIR-Systems-Inc/goodmem-claude-code-plugin.git"
    exit 1
fi

echo "Fetching ${REMOTE}/${BRANCH}..."
git fetch "$REMOTE" "$BRANCH"
remote_ref="refs/remotes/${REMOTE}/${BRANCH}"
remote_commit="$(git rev-parse "${remote_ref}^{commit}" 2>/dev/null || true)"
if [ -z "$remote_commit" ]; then
    echo "ERROR: unable to resolve ${REMOTE}/${BRANCH} after fetch."
    exit 1
fi
remote_tree="$(git rev-parse "${remote_commit}^{tree}")"

if [ "$source_tree" = "$remote_tree" ] && [ "$dry_run" != "true" ]; then
    echo "Claude plugin tree already matches ${REMOTE}/${BRANCH}; nothing to publish."
    exit 0
fi

source_commit="$(git rev-parse HEAD)"
snapshot_commit="$(
    printf 'Sync GoodMem Claude plugin snapshot\n\nSource-GoodMem-Commit: %s\n' "$source_commit" |
        git commit-tree "$source_tree" -p "$remote_commit"
)"

if [ "$source_tree" = "$remote_tree" ]; then
    echo "Claude plugin tree already matches ${REMOTE}/${BRANCH}; verifying write access anyway."
fi

push_args=(--no-verify)
if [ "$dry_run" = "true" ]; then
    push_args+=(--dry-run)
fi

echo "Publishing exact plugin-tree snapshot ${snapshot_commit}..."
if ! git push "${push_args[@]}" "$REMOTE" "${snapshot_commit}:refs/heads/${BRANCH}"; then
    echo ""
    echo "ERROR: snapshot push failed."
    echo "  Common causes:"
    echo "    * GOODMEM_CLAUDE_PLUGIN_REPO_TOKEN lacks contents:write access to"
    echo "      PAIR-Systems-Inc/goodmem-claude-code-plugin."
    echo "    * ${REMOTE}/${BRANCH} advanced after fetch; rerun after reviewing"
    echo "      the public plugin repository."
    echo "    * The public plugin repository has diverged from the GoodMem-generated"
    echo "      snapshot and needs explicit reconciliation."
    echo "  Never force-push this mirror. A real publish will hit the same failure."
    exit 1
fi

if [ "$dry_run" = "true" ]; then
    echo "Dry run complete; the public repository was not changed."
else
    echo "Claude plugin snapshot synced."
fi
