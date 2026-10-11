"""Render data/contributions.json as an animated heatmap SVG (plays once, then freezes)."""
import json
import os
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PALETTE = ["#161b22", "#0e4429", "#006d32", "#26a641", "#39d353", "#69f0a0"]
STATIC = os.environ.get("STATIC") == "1"

W = 860
CELL, GAP = 12, 3
LEFT, TOP = 46, 56


def level(day, top):
    # GitHub's own 0-4 level, plus a sixth shade for the busiest 5% of days.
    if day["count"] and day["count"] >= top:
        return 5
    return day["level"]


def main():
    data = json.loads((ROOT / "data" / "contributions.json").read_text())
    days, st = data["days"], data["stats"]
    active = sorted(d["count"] for d in days if d["count"])
    top = active[int(len(active) * 0.95)] if active else 1

    first = date.fromisoformat(days[0]["date"])
    offset = (first.weekday() + 1) % 7  # GitHub weeks start on Sunday
    weeks = (len(days) + offset + 6) // 7
    grid_w = weeks * (CELL + GAP) - GAP
    left = LEFT + (W - LEFT - 24 - grid_w) // 2
    H = TOP + 7 * (CELL + GAP) + 64

    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" '
        f'font-family="ui-monospace,SFMono-Regular,Menlo,Consolas,monospace">',
        f'<rect width="{W}" height="{H}" rx="12" fill="#0d1117" stroke="#30363d"/>',
        f'<text x="24" y="32" fill="#7ee787" font-size="14">$ <tspan fill="#c9d1d9">git log --since="1 year ago" | heatmap</tspan></text>',
    ]
    # Month labels.
    seen = set()
    for i, d in enumerate(days):
        col = (i + offset) // 7
        m = d["date"][:7]
        if d["date"][8:] <= "07" and m not in seen:
            seen.add(m)
            label = date.fromisoformat(d["date"]).strftime("%b")
            out.append(f'<text x="{left + col * (CELL + GAP)}" y="{TOP - 8}" fill="#8b949e" font-size="11">{label}</text>')
    for row, name in ((1, "Mon"), (3, "Wed"), (5, "Fri")):
        out.append(f'<text x="{left - 34}" y="{TOP + row * (CELL + GAP) + 10}" fill="#8b949e" font-size="11">{name}</text>')

    for i, d in enumerate(days):
        idx = i + offset
        col, row = idx // 7, idx % 7
        x, y = left + col * (CELL + GAP), TOP + row * (CELL + GAP)
        fill = PALETTE[level(d, top)]
        cell = f'<rect x="{x}" y="{y}" width="{CELL}" height="{CELL}" rx="2.5" fill="{fill}"'
        if STATIC:
            out.append(cell + "/>")
            continue
        # Diagonal slide-down: delay grows with column + row.
        begin = 0.012 * col + 0.04 * row
        out.append(
            cell + ' opacity="0">'
            f'<animate attributeName="opacity" from="0" to="1" begin="{begin:.3f}s" dur="0.35s" fill="freeze"/>'
            f'<animateTransform attributeName="transform" type="translate" from="0 -8" to="0 0" begin="{begin:.3f}s" dur="0.35s" fill="freeze"/>'
            "</rect>"
        )

    fy = TOP + 7 * (CELL + GAP) + 30
    best = st["best_day"]
    best_label = date.fromisoformat(best["date"]).strftime("%b %d")
    out.append(
        f'<text x="24" y="{fy}" fill="#8b949e" font-size="12">'
        f'<tspan fill="#c9d1d9">{st["total"]:,}</tspan> contributions · '
        f'streak <tspan fill="#c9d1d9">{st["current_streak"]}d</tspan> · '
        f'longest <tspan fill="#c9d1d9">{st["longest_streak"]}d</tspan> · '
        f'best <tspan fill="#c9d1d9">{best["count"]}</tspan> on {best_label}</text>'
    )
    lx = W - 24 - 6 * (CELL + GAP) - 70
    out.append(f'<text x="{lx}" y="{fy}" fill="#8b949e" font-size="11">Less</text>')
    for k, color in enumerate(PALETTE):
        out.append(f'<rect x="{lx + 34 + k * (CELL + GAP)}" y="{fy - 10}" width="{CELL}" height="{CELL}" rx="2.5" fill="{color}"/>')
    out.append(f'<text x="{lx + 40 + 6 * (CELL + GAP)}" y="{fy}" fill="#8b949e" font-size="11">More</text>')
    out.append("</svg>")
    (ROOT / "contrib-heatmap.svg").write_text("\n".join(out) + "\n")
    print("wrote contrib-heatmap.svg")


if __name__ == "__main__":
    main()
