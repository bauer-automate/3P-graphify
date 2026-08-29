from __future__ import annotations

from pathlib import Path

from graphify.extractors.base import _make_id
from graphify.inventory import extract_inventory_corpus, extract_inventory_node


def test_frontmatter_description_wins_over_first_paragraph(tmp_path):
    p = tmp_path / "sample.md"
    p.write_text(
        "---\n"
        "description: A tiny worked example of X.\n"
        "---\n"
        "\n"
        "This body paragraph must not be used since frontmatter wins.\n",
        encoding="utf-8",
    )

    result = extract_inventory_node(p)
    [node] = result["nodes"]
    assert node["description"] == "A tiny worked example of X."
    assert node["frontmatter"]["description"] == "A tiny worked example of X."
    assert node["label"] == "sample.md"
    assert node["file_type"] == "document"
    assert node["node_kind"] == "inventory"
    assert node["source_file"] == str(p)
    assert node["_origin"] == "ast"
    assert result["edges"] == []
    assert result["input_tokens"] == 0 and result["output_tokens"] == 0


def test_falls_back_to_first_body_paragraph_when_no_frontmatter_description(tmp_path):
    p = tmp_path / "sample.md"
    p.write_text(
        "# Title\n"
        "\n"
        "This is the first real paragraph of the sample.\n"
        "It continues on a second line.\n"
        "\n"
        "This second paragraph must not be picked.\n",
        encoding="utf-8",
    )

    result = extract_inventory_node(p)
    [node] = result["nodes"]
    assert node["description"] == (
        "This is the first real paragraph of the sample. It continues on a second line."
    )
    assert "frontmatter" not in node


def test_first_paragraph_extraction_works_on_plain_text_too(tmp_path):
    p = tmp_path / "notes.txt"
    p.write_text("Just a plain note with no frontmatter at all.\n", encoding="utf-8")

    result = extract_inventory_node(p)
    [node] = result["nodes"]
    assert node["description"] == "Just a plain note with no frontmatter at all."
    assert node["file_type"] == "document"


def test_code_sample_gets_code_file_type_and_best_effort_description(tmp_path):
    p = tmp_path / "sample.py"
    p.write_text("def add(a, b):\n    return a + b\n", encoding="utf-8")

    result = extract_inventory_node(p)
    [node] = result["nodes"]
    assert node["file_type"] == "code"
    assert node["label"] == "sample.py"
    # No blank line separates the two source lines, so they form one paragraph.
    assert node["description"] == "def add(a, b): return a + b"


def test_unreadable_binary_file_still_gets_a_name_only_node(tmp_path):
    p = tmp_path / "icon.png"
    p.write_bytes(b"\x89PNG\r\n\x1a\n" + bytes(range(256)))

    result = extract_inventory_node(p)
    [node] = result["nodes"]
    assert node["label"] == "icon.png"
    assert node["file_type"] == "image"
    assert "description" not in node
    assert "frontmatter" not in node


def test_heading_only_file_gets_no_description_key(tmp_path):
    p = tmp_path / "empty.md"
    p.write_text("# Just a title\n", encoding="utf-8")

    result = extract_inventory_node(p)
    [node] = result["nodes"]
    assert "description" not in node


def test_long_paragraph_is_truncated_with_ellipsis(tmp_path):
    p = tmp_path / "long.md"
    long_line = " ".join(f"word{i}" for i in range(200))
    p.write_text(long_line + "\n", encoding="utf-8")

    result = extract_inventory_node(p)
    [node] = result["nodes"]
    assert len(node["description"]) <= 281  # 280 + the ellipsis char
    assert node["description"].endswith("…")


def test_node_id_is_deterministic_and_matches_make_id(tmp_path):
    p = tmp_path / "a.md"
    p.write_text("hello\n", encoding="utf-8")

    first = extract_inventory_node(p)["nodes"][0]["id"]
    second = extract_inventory_node(p)["nodes"][0]["id"]
    assert first == second == _make_id(str(p))


def test_extract_inventory_corpus_merges_multiple_files(tmp_path):
    a = tmp_path / "a.md"
    b = tmp_path / "b.md"
    a.write_text("First file.\n", encoding="utf-8")
    b.write_text("Second file.\n", encoding="utf-8")

    result = extract_inventory_corpus([a, b])
    labels = {n["label"] for n in result["nodes"]}
    assert labels == {"a.md", "b.md"}
    assert len(result["nodes"]) == 2
