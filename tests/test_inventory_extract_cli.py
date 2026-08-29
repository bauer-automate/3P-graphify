"""End-to-end: `graphify extract` wires .graphifyignore `inventory:` scoping
through detect() -> graphify/inventory.py -> the merged graph (#7 item 1).
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

PYTHON = sys.executable
_KEY_VARS = ("GEMINI_API_KEY", "GOOGLE_API_KEY", "OPENAI_API_KEY", "OPENAI_BASE_URL",
             "ANTHROPIC_API_KEY", "MOONSHOT_API_KEY", "DEEPSEEK_API_KEY")


def _repo_with_sample_corpus(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "main.py").write_text("def hello():\n    return 1\n")
    samples = repo / "samples"
    samples.mkdir()
    (samples / "widget.py").write_text(
        "def internal_helper():\n    return 42\n\n\ndef another_one():\n    return 43\n"
    )
    (repo / ".graphifyignore").write_text("inventory: samples/**\n")
    return repo


def _run(repo: Path, *extra: str):
    import subprocess
    env = {k: v for k, v in os.environ.items() if k not in _KEY_VARS}
    env["GRAPHIFY_OUT"] = str(repo / "graphify-out")
    return subprocess.run(
        [PYTHON, "-m", "graphify", "extract", ".", *extra],
        cwd=repo, capture_output=True, text=True, env=env,
    )


def test_inventory_scoped_sample_gets_one_node_not_full_extraction(tmp_path):
    repo = _repo_with_sample_corpus(tmp_path)
    r = _run(repo)
    assert r.returncode == 0, f"extract should succeed with no LLM key needed: {r.stderr}"
    assert "1 inventory" in (r.stdout + r.stderr)

    graph = json.loads((repo / "graphify-out" / "graph.json").read_text())
    nodes = graph["nodes"]

    # main.py got full AST extraction: its function is a real node.
    assert any(n.get("label", "").startswith("hello") for n in nodes)

    # samples/widget.py got exactly one inventory node...
    inventory_nodes = [n for n in nodes if n.get("node_kind") == "inventory"]
    assert len(inventory_nodes) == 1
    assert inventory_nodes[0]["label"] == "widget.py"
    assert inventory_nodes[0]["source_file"].replace("\\", "/").endswith("samples/widget.py")

    # ...and neither of its internal functions was extracted.
    assert not any("internal_helper" in n.get("label", "") for n in nodes)
    assert not any("another_one" in n.get("label", "") for n in nodes)


def test_reclassifying_a_file_to_inventory_prunes_its_old_full_tier_nodes(tmp_path):
    """A file that previously had full AST extraction and is then scoped to
    inventory must lose its old per-symbol nodes on the next extract, not
    accumulate both — the graph reflects the current .graphifyignore, not
    every tier a file has ever been under."""
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "widget.py").write_text("def internal_helper():\n    return 42\n")

    first = _run(repo)
    assert first.returncode == 0, first.stderr
    graph = json.loads((repo / "graphify-out" / "graph.json").read_text())
    assert any("internal_helper" in n.get("label", "") for n in graph["nodes"])

    (repo / ".graphifyignore").write_text("inventory: widget.py\n")
    second = _run(repo)
    assert second.returncode == 0, second.stderr
    graph = json.loads((repo / "graphify-out" / "graph.json").read_text())
    assert not any("internal_helper" in n.get("label", "") for n in graph["nodes"])
    inventory_nodes = [n for n in graph["nodes"] if n.get("node_kind") == "inventory"]
    assert len(inventory_nodes) == 1
    assert inventory_nodes[0]["label"] == "widget.py"
