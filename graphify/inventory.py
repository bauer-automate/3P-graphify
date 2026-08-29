"""Inventory-only extraction (#7 item 1).

Paths matched by an ``inventory:`` directive in .graphifyignore (see
graphify.detect._parse_inventory_directive) get exactly one lightweight node
here instead of deep AST/semantic extraction: a name plus a cheap description
(YAML frontmatter, or the first body paragraph), at near-zero cost — no
tree-sitter parsing, no LLM call. Meant for corpora that should be
searchable/citable (a keyword surface) without the token burn of extracting
every internal symbol, e.g. a large sample/reference collection.
"""
from __future__ import annotations

from pathlib import Path

from graphify.detect import FileType, classify_file
from graphify.extractors.base import _make_id
from graphify.extractors.markdown import _parse_frontmatter, _split_frontmatter
from graphify.security import sanitize_metadata

_DESCRIPTION_MAX_CHARS = 280
_FRONTMATTER_EXTENSIONS = {".md", ".mdx", ".qmd", ".markdown"}


def _first_paragraph(text: str) -> str:
    """First non-empty, non-fence, non-heading paragraph of *text*, flattened
    to one line and capped at _DESCRIPTION_MAX_CHARS.

    Deliberately simple (no per-language comment/docstring awareness): the
    whole point of this tier is to stay cheap. A ``#``-prefixed line is
    treated as a heading and skipped, which is exactly right for Markdown and
    mostly harmless elsewhere (it can skip a leading shell/Python comment,
    leaving that file with a shorter or empty description rather than a
    misleading one).
    """
    para_lines: list[str] = []
    in_fence = False
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if line.startswith("```") or line.startswith("~~~"):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        if not line:
            if para_lines:
                break
            continue
        if line.startswith("#"):
            if para_lines:
                break
            continue
        para_lines.append(line)
    para = " ".join(para_lines).strip()
    if len(para) > _DESCRIPTION_MAX_CHARS:
        para = para[:_DESCRIPTION_MAX_CHARS].rsplit(" ", 1)[0] + "…"
    return para


def extract_inventory_node(path: Path) -> dict:
    """Return a single-node raw-extraction dict (same shape as an AST/semantic
    extractor's result) for one inventory-scoped file.

    A file that cannot be read as UTF-8 text (binary, permission error, bad
    encoding) still gets a name-only node — the point of this tier is that a
    corpus entry is never invisible, only unenriched.
    """
    str_path = str(path)
    ftype = classify_file(path)
    node: dict = {
        "id": _make_id(str_path),
        "label": path.name,
        "file_type": ftype.value if ftype is not None else FileType.DOCUMENT.value,
        "node_kind": "inventory",
        "source_file": str_path,
        "source_location": "L1",
        # Deterministic, no LLM call — merge/dedup must treat this like any
        # other AST-tier item (graphify.build._is_ast_tier).
        "_origin": "ast",
    }
    try:
        text = path.read_text(encoding="utf-8", errors="strict")
    except (OSError, UnicodeDecodeError, ValueError):
        return {"nodes": [node], "edges": [], "input_tokens": 0, "output_tokens": 0}

    description = ""
    body_text = text
    if path.suffix.lower() in _FRONTMATTER_EXTENSIONS:
        lines = text.splitlines()
        fm_lines, body_start = _split_frontmatter(lines)
        if fm_lines:
            frontmatter = sanitize_metadata(_parse_frontmatter(fm_lines))
            fm_description = frontmatter.get("description")
            if isinstance(fm_description, str) and fm_description.strip():
                description = fm_description.strip()[:_DESCRIPTION_MAX_CHARS]
            if frontmatter:
                node["frontmatter"] = frontmatter
        body_text = "\n".join(lines[body_start:])

    if not description:
        description = _first_paragraph(body_text)
    if description:
        node["description"] = description
    return {"nodes": [node], "edges": [], "input_tokens": 0, "output_tokens": 0}


def extract_inventory_corpus(paths: list[Path]) -> dict:
    """Run extract_inventory_node() over every path, merged into one raw dict
    (same {"nodes", "edges", "input_tokens", "output_tokens"} shape as
    ast_result/sem_result in the `extract` CLI command, so it can be combined
    with them the same way)."""
    nodes: list[dict] = []
    for path in paths:
        result = extract_inventory_node(path)
        nodes.extend(result["nodes"])
    return {"nodes": nodes, "edges": [], "input_tokens": 0, "output_tokens": 0}
