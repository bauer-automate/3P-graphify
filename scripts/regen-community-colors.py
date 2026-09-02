#!/usr/bin/env python3
"""Regenerate graphify.exporters.base.COMMUNITY_COLORS's tint/shade steps.

The palette is 8 validated dark-mode categorical hues (Claude Code's dataviz
skill, references/palette.md) as fixed anchors, each with two derived steps --
lighter tint and darker shade -- so a community-color cycle repeats every 24
communities instead of every 8, without inventing new, unvalidated hues. Run
this and paste the "flat 24" list into COMMUNITY_COLORS if the anchors ever
change (e.g. the dataviz skill re-orders or re-steps its default palette).
"""
from __future__ import annotations

ANCHORS = ["#3987e5", "#d95926", "#199e70", "#c98500", "#d55181", "#008300", "#9085e9", "#e66767"]
NAMES = ["blue", "orange", "aqua", "yellow", "magenta", "green", "violet", "red"]
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
TINT_FRAC = 0.35
SHADE_FRAC = 0.30


def hex_to_rgb(h: str) -> tuple[int, int, int]:
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))  # type: ignore[return-value]


def rgb_to_hex(rgb: tuple[float, float, float]) -> str:
    return "#" + "".join(f"{max(0, min(255, round(c))):02x}" for c in rgb)


def mix(rgb: tuple[int, int, int], target: tuple[int, int, int], frac: float) -> tuple[float, float, float]:
    return tuple(c + (t - c) * frac for c, t in zip(rgb, target))  # type: ignore[return-value]


def main() -> None:
    tier1 = ANCHORS
    tier2 = [rgb_to_hex(mix(hex_to_rgb(h), WHITE, TINT_FRAC)) for h in ANCHORS]
    tier3 = [rgb_to_hex(mix(hex_to_rgb(h), BLACK, SHADE_FRAC)) for h in ANCHORS]

    for label, tier in (("tier 1 (anchors)", tier1), ("tier 2 (+35% white)", tier2), ("tier 3 (+30% black)", tier3)):
        print(f"{label}:")
        for name, hexval in zip(NAMES, tier):
            print(f"  {name:8s} {hexval}")

    flat = tier1 + tier2 + tier3
    print("\nflat 24, tier-major order (paste into COMMUNITY_COLORS):")
    print(flat)


if __name__ == "__main__":
    main()
