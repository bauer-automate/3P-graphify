When `graphify-out/graph.json` already exists and the user asks a question about the corpus, answer from the graph rather than rebuilding it.

If graphify's MCP tools (`query_graph`, `get_node`, `get_neighbors`, `shortest_path`, `get_community`, `god_nodes`, `graph_stats`) are available in your toolset, call them directly — they serve the same already-loaded graph in-process, with no CLI process spawned per call, which matters once a session issues many queries. Otherwise:

```bash
graphify query "<question>"
```

Before traversal, expand the question against the graph's own vocabulary so a wording mismatch does not collapse the answer to noise. If neither the MCP tools nor the `graphify query` CLI are available, fall back to an inline NetworkX traversal of `graphify-out/graph.json`. Answer using only what the graph output contains, and quote `source_location` when citing a specific fact. For that vocab-expansion step, the BFS/DFS traversal modes, the `--budget` cap, the NetworkX fallback, `save-result` feedback, and the `/graphify path` and `/graphify explain` flows, see `references/query.md`.
