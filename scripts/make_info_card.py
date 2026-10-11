"""Neofetch-style info card SVG. Edit LINES to change what it says."""
import os
from pathlib import Path
from xml.sax.saxutils import escape

ROOT = Path(__file__).resolve().parent.parent
STATIC = os.environ.get("STATIC") == "1"
W, H = 490, 400

KEY, VAL, DIM, ACCENT = "#79c0ff", "#c9d1d9", "#8b949e", "#7ee787"

# (key, value) rows; key=None draws a blank spacer, key="" a continuation line.
LINES = [
    ("Name", "Luis R"),
    ("Role", "Indie dev · apps, AI tools, systems"),
    (None, None),
    ("Now", "LegalPocket AI"),
    ("", "legal-document AI for iPhone"),
    (None, None),
    ("OSS", "AnyPS5 — PS5 executable porting"),
    ("", "jev-behavior-study — agent eval study"),
    (None, None),
    ("Stack", "Swift · SwiftUI · Metal"),
    ("", "TypeScript · Next.js · Python · Supabase"),
    ("Likes", "on-device ML, Apple silicon, sports data"),
]


def main():
    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" '
        f'font-family="ui-monospace,SFMono-Regular,Menlo,Consolas,monospace" font-size="13">',
        f'<rect width="{W}" height="{H}" rx="12" fill="#0d1117" stroke="#30363d"/>',
        f'<text x="20" y="20" fill="{ACCENT}" font-size="12">$ <tspan fill="{VAL}">neofetch</tspan></text>',
        f'<text x="24" y="54" font-size="15"><tspan fill="{ACCENT}" font-weight="bold">rinnecoder</tspan>'
        f'<tspan fill="{VAL}">@</tspan><tspan fill="{ACCENT}" font-weight="bold">github</tspan></text>',
        f'<rect x="24" y="62" width="176" height="1.5" fill="{DIM}"/>',
    ]
    y, step = 90, 19
    for i, (k, v) in enumerate(LINES):
        if k is None:
            y += step // 2
            continue
        key = f'<tspan fill="{KEY}" font-weight="bold">{escape(k)}</tspan>' if k else ""
        sep = f'<tspan fill="{DIM}">:</tspan>' if k else ""
        line = f'<text x="24" y="{y}">{key}{sep}<tspan x="118" fill="{VAL}">{escape(v)}</tspan></text>'
        if STATIC:
            out.append(line)
        else:
            b = 0.35 + 0.09 * i
            out.append(
                f'<g opacity="0">'
                f'<animate attributeName="opacity" from="0" to="1" begin="{b:.2f}s" dur="0.4s" fill="freeze"/>'
                f'<animateTransform attributeName="transform" type="translate" from="-12 0" to="0 0" begin="{b:.2f}s" dur="0.4s" fill="freeze"/>'
                f"{line}</g>"
            )
        y += step
    # Terminal colour swatches, neofetch style.
    colors = ["#0d1117", "#ff7b72", "#7ee787", "#d29922", "#79c0ff", "#d2a8ff", "#a5d6ff", "#c9d1d9"]
    for k, c in enumerate(colors):
        out.append(f'<rect x="{24 + k * 24}" y="{H - 34}" width="22" height="14" fill="{c}" stroke="#30363d"/>')
    if not STATIC:
        # Blinking block cursor after the swatches.
        out.append(
            f'<rect x="{24 + 8 * 24 + 8}" y="{H - 34}" width="9" height="14" fill="{ACCENT}">'
            '<animate attributeName="opacity" values="1;1;0;0" keyTimes="0;0.5;0.5;1" dur="1.1s" repeatCount="indefinite"/></rect>'
        )
    out.append("</svg>")
    (ROOT / "info-card.svg").write_text("\n".join(out) + "\n")
    print("wrote info-card.svg")


if __name__ == "__main__":
    main()
