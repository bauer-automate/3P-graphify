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
# Obsidian exporters. A graph can carry far more communities than any chart's
# identity channel is meant to hold (Claude Code's dataviz skill: 8 hues fixed
# order, a 9th series folds into "Other" rather than inventing a new hue) --
# but folding isn't available here, every community needs *some* color, and
# unlike a bar/line chart, a node-link diagram doesn't lean on color alone for
# identity: graph position/clustering and the on-hover/legend label carry it
# too, so exact pairwise distinctness matters less than in a standard chart.
# The compromise: keep the 8 validated dark-mode categorical hues below
# (Claude Code dataviz skill references/palette.md, its documented default,
# CVD-checked) as fixed anchors, and add two more steps per hue -- lighter
# tint and darker shade -- so reused hues read as "same family, different
# depth" instead of colliding outright. 24 slots means the old 10-color cycle
# repeating every 10 communities (community 0 and 10 rendered pixel-identical)
# now repeats every 24. Tints/shades are computed, not eyeballed: mix each
# anchor 35% toward white (tier 2) / 30% toward black (tier 3); see
# scripts/regen-community-colors.py to reproduce or re-derive.
COMMUNITY_COLORS = [
    # tier 1 -- anchors, as published (blue, orange, aqua, yellow, magenta, green, violet, red)
    "#3987e5", "#d95926", "#199e70", "#c98500", "#d55181", "#008300", "#9085e9", "#e66767",
    # tier 2 -- same 8 hues, +35% toward white
    "#7eb1ee", "#e69372", "#6ac0a2", "#dcb059", "#e48ead", "#59ae59", "#b7b0f1", "#ef9c9c",
    # tier 3 -- same 8 hues, +30% toward black
    "#285ea0", "#983e1b", "#126f4e", "#8d5d00", "#95395a", "#005c00", "#655da3", "#a14848",
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
