#!/bin/bash
# Sync the claude/ subtree to the public goodmem-claude-code-plugin repo.
#
# Usage:
#   ./publish.sh              # push subtree to goodmem-plugin main
#   ./publish.sh --dry-run    # show what would be pushed, but don't push

set -euo pipefail

# Must run from the repo root for git subtree to work.
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "${REPO_ROOT}"

SUBTREE_PREFIX="clients/v2/claude"
REMOTE="goodmem-plugin"
BRANCH="main"

usage() {
    cat <<'EOF'
Sync the claude/ subtree to the goodmem-claude-code-plugin repo.

Usage:
  ./publish.sh [--dry-run]

Options:
  --dry-run    Show diff against remote; do not push.
  -h, --help   Show this help.
EOF
}

dry_run="false"

while [ $# -gt 0 ]; do
    case "${1}" in
        --dry-run) dry_run="true" ;;
        -h|--help) usage; exit 0 ;;
        *)
            echo "Unknown option: ${1}"
            echo ""
            usage
            exit 1
            ;;
    esac
    shift
done

echo "=== GoodMem Claude Plugin Subtree Sync ==="
echo "Prefix: ${SUBTREE_PREFIX}"
echo "Remote: ${REMOTE} (${BRANCH})"

# Verify the remote exists.
if ! git remote get-url "${REMOTE}" &>/dev/null; then
    echo "ERROR: Remote '${REMOTE}' not found."
    echo "Add it with:"
    echo "  git remote add ${REMOTE} git@github.com:PAIR-Systems-Inc/goodmem-claude-code-plugin.git"
    exit 1
fi

if [ "${dry_run}" = "true" ]; then
    echo ""
    echo "Fetching ${REMOTE}/${BRANCH}..."
    git fetch "${REMOTE}" "${BRANCH}"
    echo ""
    echo "Commits that would be pushed:"
    git log "${REMOTE}/${BRANCH}..HEAD" --oneline -- "${SUBTREE_PREFIX}"
    echo ""
    echo "Dry run complete."
    exit 0
fi

echo ""
echo "Pushing subtree to ${REMOTE} ${BRANCH}..."
git subtree push --prefix="${SUBTREE_PREFIX}" "${REMOTE}" "${BRANCH}"
echo ""
echo "Subtree synced."
