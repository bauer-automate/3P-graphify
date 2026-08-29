from __future__ import annotations

import json

import networkx as nx
from networkx.readwrite import json_graph

import graphify.__main__ as mainmod


def _write_graph(tmp_path):
    graph = nx.Graph()
    graph.add_node("a1", label="alpha", source_file="pkg/alpha.py", source_location="L1", community=0)
    graph.add_node("a2", label="alpha_helper", source_file="pkg/helper.py", source_location="L1", community=0)
    graph.add_node("b1", label="beta", source_file="pkg/beta.py", source_location="L1", community=1)
    graph.add_edge("a1", "a2", relation="calls", confidence="EXTRACTED")
    graph_path = tmp_path / "graph.json"
    graph_path.write_text(json.dumps(json_graph.node_link_data(graph, edges="links")), encoding="utf-8")
    return graph_path


def test_files_cli_community_mode_lists_deduped_source_files(monkeypatch, tmp_path, capsys):
    graph_path = _write_graph(tmp_path)
    monkeypatch.setattr(mainmod, "_check_skill_version", lambda _: None)
    monkeypatch.setattr(mainmod.sys, "argv", ["graphify", "files", "0", "--graph", str(graph_path)])

    mainmod.main()

    out = capsys.readouterr().out
    assert "Reading list for Community 0" in out
    assert "pkg/alpha.py" in out
    assert "pkg/helper.py" in out
    assert "pkg/beta.py" not in out


def test_files_cli_label_mode_lists_neighborhood_files(monkeypatch, tmp_path, capsys):
    graph_path = _write_graph(tmp_path)
    monkeypatch.setattr(mainmod, "_check_skill_version", lambda _: None)
    monkeypatch.setattr(mainmod.sys, "argv", ["graphify", "files", "alpha", "--graph", str(graph_path)])

    mainmod.main()

    out = capsys.readouterr().out
    assert "Reading list for alpha" in out
    assert "pkg/alpha.py" in out
    assert "pkg/helper.py" in out  # one hop away, within the default depth=2
    assert "pkg/beta.py" not in out


def test_files_cli_ranks_neighborhood_files_by_hop_distance():
    """A file whose closest member node is 1 hop from the seed must sort
    before a file whose closest member is 2 hops away, even if the farther
    file's nodes have higher degree."""
    from graphify.serve import _reading_list_text

    G = nx.Graph()
    G.add_node("seed", source_file="seed.py")
    G.add_node("near", source_file="near.py")
    G.add_node("far", source_file="far.py")
    G.add_node("far_hub1", source_file="far.py")
    G.add_node("far_hub2", source_file="far.py")
    G.add_edge("seed", "near")
    G.add_edge("near", "far")
    # Pad far.py's degree so a pure-degree ranking (ignoring hop distance)
    # would incorrectly put it ahead of near.py.
    for extra in ("far_hub1", "far_hub2"):
        G.add_edge("far", extra)

    text = _reading_list_text(G, {"seed", "near", "far", "far_hub1", "far_hub2"}, seeds=["seed"])
    assert text.index("near.py") < text.index("far.py")


def test_files_cli_unknown_community_errors(monkeypatch, tmp_path, capsys):
    graph_path = _write_graph(tmp_path)
    monkeypatch.setattr(mainmod, "_check_skill_version", lambda _: None)
    monkeypatch.setattr(mainmod.sys, "argv", ["graphify", "files", "99", "--graph", str(graph_path)])

    raised = False
    try:
        mainmod.main()
    except SystemExit as exc:
        raised = True
        assert exc.code == 1
    assert raised
    assert "community 99 not found" in capsys.readouterr().err


def test_files_cli_unknown_label_errors(monkeypatch, tmp_path, capsys):
    graph_path = _write_graph(tmp_path)
    monkeypatch.setattr(mainmod, "_check_skill_version", lambda _: None)
    monkeypatch.setattr(mainmod.sys, "argv", ["graphify", "files", "doesnotexist", "--graph", str(graph_path)])

    raised = False
    try:
        mainmod.main()
    except SystemExit as exc:
        raised = True
        assert exc.code == 1
    assert raised
    assert "no node matching" in capsys.readouterr().err
