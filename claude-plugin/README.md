# graphify — Claude Code plugin bundle

A ready-to-use Claude Code plugin carrying the graphify skill.

`skills/graphify/` is **GENERATED** by `python -m tools.skillgen` (platform key
`claude-plugin`) and guarded by CI (`python -m tools.skillgen --check`). Do not
hand-edit it; edit the fragments under `tools/skillgen/fragments/` (or, for the
frontmatter description, `tools/skillgen/platforms.toml`) and re-render.

The skill self-bootstraps the `graphifyy` CLI from PyPI on first use (Step 1 of
SKILL.md), so the plugin needs no install-time dependencies and works in
ephemeral cloud sessions and on local machines alike. Code is indexed with
local tree-sitter AST parsing — no API key required.

Two ways to use it:

1. **Copy into your own plugin** — copy `skills/graphify/` into your plugin's
   `skills/` directory. Keep the folder named `graphify`: Claude Code requires
   the skill folder name to match the frontmatter `name`.
2. **Use this directory as a plugin** — point Claude Code at this directory as
   a local plugin, or add the repo as a plugin marketplace (repo root carries
   `.claude-plugin/marketplace.json`) and install from it:
   ```
   /plugin marketplace add bastudent1337/graphify
   /plugin install graphify@graphify
   ```
