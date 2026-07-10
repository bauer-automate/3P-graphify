#!/bin/bash
set -euo pipefail

# graphify SessionStart hook — Claude Code on the web only.
#
# This repo is graphify's own source, so instead of depending on a published
# PyPI release, install the CLI in editable mode straight from the checkout:
# the `graphify` command then always tracks whatever commit is checked out,
# with no reinstall step needed when the source changes between sessions.
#
# Also builds/refreshes graphify-out/graph.json so graphify query/explain/path
# (and the graphify skill) work immediately, with no manual first build.
if [ "${CLAUDE_CODE_REMOTE:-}" != "true" ]; then
  exit 0
fi

PROJECT_DIR="${CLAUDE_PROJECT_DIR:-$PWD}"
cd "$PROJECT_DIR"

export PATH="$HOME/.local/bin:$PATH"
if [ -n "${CLAUDE_ENV_FILE:-}" ]; then
  echo "export PATH=\"$HOME/.local/bin:\$PATH\"" >> "$CLAUDE_ENV_FILE"
fi

if ! command -v uv >/dev/null 2>&1; then
  curl -LsSf https://astral.sh/uv/install.sh | sh
  export PATH="$HOME/.local/bin:$PATH"
fi

uv tool install --editable "$PROJECT_DIR"

# Re-register the Claude Code skill + PreToolUse hook + CLAUDE.md section.
# Idempotent (prints "already configured" when nothing changed). SKILL.md and
# the PreToolUse hook live under the gitignored .claude/skills + settings, so
# this regenerates them fresh every session rather than relying on git.
graphify install --project --platform claude

# Build or refresh the knowledge graph. --code-only keeps this fully local
# (tree-sitter AST, no LLM/API key). `graphify update` is the fast
# incremental path for a container that already has a graph from an earlier
# session; a missing graph means this container needs the initial build.
if [ -f "$PROJECT_DIR/graphify-out/graph.json" ]; then
  graphify update "$PROJECT_DIR"
else
  graphify "$PROJECT_DIR" --code-only
  graphify cluster-only "$PROJECT_DIR" --no-label --no-viz
fi
