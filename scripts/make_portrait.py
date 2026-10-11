"""Turn the current GitHub avatar into an animated ASCII-portrait SVG.

Skips all work when the avatar hash matches data/avatar.sha256, so the daily
workflow only pays for rembg/OpenCV when the profile picture actually changes.
Run with --check to just print changed=true|false (for the workflow).
"""
import hashlib
import io
import os
import sys
from itertools import groupby
from pathlib import Path
from xml.sax.saxutils import escape

import requests

USER = "RINNECODER"
ROOT = Path(__file__).resolve().parent.parent
HASH_FILE = ROOT / "data" / "avatar.sha256"
OUT = ROOT / "ascii-portrait.svg"

RAMP = " .`:-=+*cs#%@"
COLS, ROWS = 100, 53
W, H = 370, 400
PAD_X, PAD_TOP = 0, 30
CW = W / COLS
LH = (H - PAD_TOP - 12) / ROWS
STATIC = os.environ.get("STATIC") == "1"


def avatar_bytes():
    r = requests.get(f"https://github.com/{USER}.png?size=460", timeout=30)
    r.raise_for_status()
    return r.content


def prep(raw):
    """Remove background, boost local contrast, crop to the subject.

    Returns the colour crop, a contrast-boosted grayscale crop and the cutout mask.
    """
    import cv2
    import numpy as np
    from PIL import Image
    from rembg import new_session, remove

    img = Image.open(io.BytesIO(raw)).convert("RGB")
    cut = np.array(remove(img, session=new_session("u2net")))  # RGBA
    gray = cv2.cvtColor(cut[..., :3], cv2.COLOR_RGB2GRAY)
    # Mild CLAHE: stronger settings flatten a light face into the helmet.
    gray = cv2.createCLAHE(clipLimit=1.2, tileGridSize=(4, 4)).apply(gray)
    alpha = cut[..., 3]
    ys, xs = np.nonzero(alpha > 128)
    if len(xs):
        # Square crop around the subject with a small margin.
        cx, cy = (xs.min() + xs.max()) / 2, (ys.min() + ys.max()) / 2
        half = max(xs.max() - xs.min(), ys.max() - ys.min()) / 2 * 1.06
        box = [int(cx - half), int(cy - half), int(cx + half), int(cy + half)]
    else:
        box = [0, 0, gray.shape[1], gray.shape[0]]
    to_img = lambda a: Image.fromarray(a).crop(box)
    return to_img(cut[..., :3]), to_img(gray), to_img(alpha)


def tint(rgb):
    """The pixel's own hue, lifted so it stays readable on the dark panel."""
    import colorsys

    h, s, v = colorsys.rgb_to_hsv(*(c / 255 for c in rgb))
    r, g, b = colorsys.hsv_to_rgb(h, min(1, s * 1.25), 0.55 + 0.45 * v)
    # Quantize so neighbouring glyphs share a <tspan>.
    return "#" + "".join(f"{min(255, round(c * 255 / 24) * 24):02x}" for c in (r, g, b))


def to_ascii(images):
    """Light glyphs on a dark panel: bright pixels get dense glyphs.

    Returns rows of (glyph, colour) pairs.
    """
    import numpy as np

    color, gray, alpha = images
    rgb = np.array(color.resize((COLS, ROWS)))
    g = np.array(gray.resize((COLS, ROWS)), dtype=np.float32)
    a = np.array(alpha.resize((COLS, ROWS)), dtype=np.float32) / 255
    fg = g[a > 0.5]
    lo, hi = (np.percentile(fg, 2), np.percentile(fg, 98)) if fg.size else (0, 255)
    v = np.clip((g - lo) / max(hi - lo, 1), 0, 1) ** 1.4  # keep dark features sparse
    rows = []
    for vr, ar, cr in zip(v, a, rgb):
        # Background maps to spaces; subject pixels at least get a dot.
        rows.append([
            (" ", None) if al < 0.5 else (RAMP[max(1, int(x * (len(RAMP) - 1) + 0.5))], tint(c))
            for x, al, c in zip(vr, ar, cr)
        ])
    return rows


def svg(rows):
    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" '
        f'font-family="ui-monospace,SFMono-Regular,Menlo,Consolas,monospace">',
        "<defs>",
    ]
    for i in range(len(rows)):
        y = PAD_TOP + i * LH
        width = f'{W}' if STATIC else '0'
        out.append(f'<clipPath id="r{i}"><rect x="0" y="{y:.2f}" width="{width}" height="{LH + 0.5:.2f}">')
        if not STATIC:
            out.append(f'<animate attributeName="width" from="0" to="{W}" begin="{0.05 * i:.2f}s" dur="0.45s" fill="freeze"/>')
        out.append("</rect></clipPath>")
    out.append("</defs>")
    out.append(f'<rect width="{W}" height="{H}" rx="12" fill="#0d1117" stroke="#30363d"/>')
    out.append(f'<text x="16" y="20" fill="#7ee787" font-size="12">$ <tspan fill="#c9d1d9">cat avatar.png | ascii</tspan></text>')
    fs = LH * 1.05
    for i, row in enumerate(rows):
        if all(ch == " " for ch, _ in row):
            continue
        y = PAD_TOP + (i + 0.8) * LH
        out.append(
            f'<text x="{PAD_X}" y="{y:.2f}" font-size="{fs:.2f}" xml:space="preserve" '
            f'textLength="{W - 2 * PAD_X}" lengthAdjust="spacingAndGlyphs" clip-path="url(#r{i})">'
            + "".join(
                escape("".join(ch for ch, _ in run)) if col is None
                else f'<tspan fill="{col}">{escape("".join(ch for ch, _ in run))}</tspan>'
                for col, run in ((k, list(g)) for k, g in groupby(row, key=lambda p: p[1]))
            )
            + "</text>"
        )
        if not STATIC:
            b = 0.05 * i
            out.append(
                f'<rect y="{PAD_TOP + i * LH:.2f}" width="{CW * 1.2:.2f}" height="{LH:.2f}" fill="#7ee787" opacity="0">'
                f'<set attributeName="opacity" to="0.9" begin="{b:.2f}s"/>'
                f'<animate attributeName="x" from="0" to="{W}" begin="{b:.2f}s" dur="0.45s" fill="freeze"/>'
                f'<set attributeName="opacity" to="0" begin="{b + 0.45:.2f}s"/>'
                "</rect>"
            )
    out.append("</svg>")
    return "\n".join(out) + "\n"


def main():
    raw = avatar_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    old = HASH_FILE.read_text().strip() if HASH_FILE.exists() else ""
    changed = digest != old or not OUT.exists() or os.environ.get("FORCE") == "1"
    if "--check" in sys.argv:
        print(f"changed={'true' if changed else 'false'}")
        return
    if not changed:
        print("avatar unchanged; skipping")
        return
    OUT.write_text(svg(to_ascii(prep(raw))))
    HASH_FILE.parent.mkdir(exist_ok=True)
    HASH_FILE.write_text(digest + "\n")
    print("wrote ascii-portrait.svg")


if __name__ == "__main__":
    main()
