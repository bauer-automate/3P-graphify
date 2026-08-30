"""Shared constants/helpers for the graphify exporters package.

Symbols used by more than one exporter live here so each exporter module can be
split out of graphify/export.py without a circular import (export.py and the
per-format modules both import from here, never from each other).
"""
from __future__ import annotations

import json
import re
from pathlib import Path

# Categorical palette for community coloring, shared by the HTML, SVG, and
# Obsidian exporters. Moved verbatim from graphify/export.py.
COMMUNITY_COLORS = [
    "#4E79A7", "#F28E2B", "#E15759", "#76B7B2", "#59A14F",
    "#EDC948", "#B07AA1", "#FF9DA7", "#9C755F", "#BAB0AC",
]

# User-authored spec that pins specific communities to a hex color, overriding
# the auto-assigned COMMUNITY_COLORS cycle above. Lives at the project root,
# sibling to .graphifyignore/.graphifyrc (not inside graphify-out/, which is
# regenerated wholesale on every rebuild).
COLOR_SPEC_FILENAME = ".graphifycolors.json"

_HEX_COLOR_RE = re.compile(r"^#[0-9A-Fa-f]{6}$")


def load_color_overrides(root: Path) -> dict[str, str]:
    """Load ``{community-id-or-label: "#rrggbb"}`` overrides from
    ``<root>/.graphifycolors.json``.

    Missing file => {}. A malformed file or an individual bad entry is a
    warning, not a raise — a typo in a hand-authored styling spec must not
    break a graph rebuild. Keys are matched against a community's numeric id
    (as a string) first, then its current label, by resolve_community_color().
    """
    spec_path = root / COLOR_SPEC_FILENAME
    if not spec_path.is_file():
        return {}
    try:
        raw = json.loads(spec_path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        print(f"[graphify] warning: could not read {spec_path}: {exc}")
        return {}
    if not isinstance(raw, dict):
        print(f"[graphify] warning: {spec_path} must be a JSON object of "
              f'{{"community id or label": "#rrggbb"}}; ignoring')
        return {}

    overrides: dict[str, str] = {}
    for key, val in raw.items():
        if isinstance(val, str) and _HEX_COLOR_RE.match(val):
            overrides[str(key)] = val
        else:
            print(f"[graphify] warning: {spec_path}: ignoring {key!r} -> {val!r} "
                  f'(expected a "#rrggbb" hex color)')
    return overrides


def resolve_community_color(
    cid: int,
    community_labels: dict[int, str] | None,
    overrides: dict[str, str] | None,
) -> str:
    """Return the color for community *cid*.

    A user override wins when its key matches the community's numeric id
    (as a string) or its current label; otherwise falls back to the next
    color in the auto-assigned COMMUNITY_COLORS cycle.
    """
    if overrides:
        color = overrides.get(str(cid))
        if color is None and community_labels:
            label = community_labels.get(cid)
            if label:
                color = overrides.get(label)
        if color:
            return color
    return COMMUNITY_COLORS[cid % len(COMMUNITY_COLORS)]
