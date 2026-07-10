```bash
# Detect the correct Python interpreter (handles uv tool, pipx, venv, system installs)
PYTHON=""
GRAPHIFY_BIN=$(which graphify 2>/dev/null)
# 1. uv tool installs — most reliable on modern Mac/Linux. Use `uv tool dir`
# (prints the install directory only) rather than `uv tool run --from`, which
# silently downloads graphifyy into uv's ephemeral cache and would make this
# probe "succeed" even when graphify isn't actually installed anywhere,
# skipping the real install below and leaving no console script on PATH.
if [ -z "$PYTHON" ] && command -v uv >/dev/null 2>&1; then
    _UV_DIR=$(uv tool dir 2>/dev/null)
    _UV_PY="$_UV_DIR/graphifyy/bin/python"
    if [ -n "$_UV_DIR" ] && [ -x "$_UV_PY" ] && "$_UV_PY" -c "import graphify" 2>/dev/null; then
        PYTHON="$_UV_PY"
    fi
fi
# 2. Read shebang from graphify binary (pipx and direct pip installs)
if [ -z "$PYTHON" ] && [ -n "$GRAPHIFY_BIN" ]; then
    _SHEBANG=$(head -1 "$GRAPHIFY_BIN" | tr -d '#!')
    case "$_SHEBANG" in
        *[!a-zA-Z0-9/_.@-]*) ;;
        *) "$_SHEBANG" -c "import graphify" 2>/dev/null && PYTHON="$_SHEBANG" ;;
    esac
fi
# 3. Fall back to python3
if [ -z "$PYTHON" ]; then PYTHON="python3"; fi
if ! "$PYTHON" -c "import graphify" 2>/dev/null; then
    if command -v uv >/dev/null 2>&1; then
        uv tool install --upgrade graphifyy -q 2>&1 | tail -3
        hash -r 2>/dev/null || true
        _UV_DIR=$(uv tool dir 2>/dev/null)
        _UV_PY="$_UV_DIR/graphifyy/bin/python"
        if [ -n "$_UV_DIR" ] && [ -x "$_UV_PY" ]; then PYTHON="$_UV_PY"; fi
    else
        "$PYTHON" -m pip install graphifyy -q 2>/dev/null \
          || "$PYTHON" -m pip install graphifyy -q --break-system-packages 2>&1 | tail -3
        hash -r 2>/dev/null || true
    fi
fi
# Write interpreter path for all subsequent steps (persists across invocations)
mkdir -p graphify-out
"$PYTHON" -c "import sys; open('graphify-out/.graphify_python', 'w', encoding='utf-8').write(sys.executable)"
# Save scan root so `graphify update` (no args) knows where to look next time
echo "$(cd INPUT_PATH && pwd)" > graphify-out/.graphify_root
```

If the import succeeds, print nothing and move straight to Step 2.

**In every subsequent bash block, replace `python3` with `$(cat graphify-out/.graphify_python)` to use the correct interpreter.**
