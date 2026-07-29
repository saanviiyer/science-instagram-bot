"""Render a 1080x1080 Instagram card (PNG) for a post.

Gradient background tuned per account + the article title + a source/branding
footer. Uses Pillow and macOS system fonts. Produces a fully post-ready image
so every draft has an image to publish (Instagram feed posts require one).

Note: the Graph API needs a *publicly hosted* image URL. These PNGs are written
locally; upload them (S3, Cloudinary, GitHub Pages, etc.) and put the URL in the
draft's `image_url` before publishing — or pass --image-url at publish time.
"""

import os
import textwrap

from PIL import Image, ImageDraw, ImageFont

SIZE = 1080
MARGIN = 90

# Per-account gradient (top color, bottom color) as RGB. Falls back to a neutral
# blue for anything unlisted.
PALETTES = {
    "chemistrynews":     ((14, 78, 74),  (6, 34, 48)),
    "biologynews":       ((22, 92, 52),  (7, 40, 30)),
    "physicsnews":       ((32, 44, 120), (10, 14, 52)),
    "quantumnews":       ((78, 26, 120), (18, 10, 52)),
    "environmentalnews": ((26, 96, 66),  (8, 42, 34)),
    "spacenews":         ((18, 22, 66),  (4, 6, 26)),
    "neuronews":         ((96, 32, 96),  (26, 10, 44)),
    "medicinenews":      ((150, 36, 52), (54, 12, 24)),
    "ainews":            ((20, 60, 110), (8, 20, 44)),
    "psychnews":         ((120, 60, 30), (48, 22, 14)),
    "mathnews":          ((40, 60, 80),  (12, 20, 30)),
    # institutions
    "researchatcaltech":  ((150, 60, 24), (54, 20, 8)),
    "researchatstanford": ((120, 24, 24), (48, 8, 8)),
    "researchatmit":      ((90, 20, 30),  (30, 8, 12)),
    "researchatharvard":  ((110, 20, 24), (40, 8, 10)),
    "researchatberkeley": ((16, 40, 92),  (6, 16, 44)),
}
DEFAULT_PALETTE = ((24, 48, 96), (8, 16, 40))

_FONT_BOLD = "/System/Library/Fonts/Supplemental/Arial Bold.ttf"
_FONT_REG = "/System/Library/Fonts/Supplemental/Arial.ttf"


def _font(path, size):
    try:
        return ImageFont.truetype(path, size)
    except OSError:
        return ImageFont.load_default()


def _gradient(top, bottom):
    # Build a 1px-wide vertical gradient, then stretch to full width — far
    # faster than per-pixel writes.
    strip = Image.new("RGB", (1, SIZE))
    sp = strip.load()
    for y in range(SIZE):
        t = y / (SIZE - 1)
        sp[0, y] = (
            int(top[0] + (bottom[0] - top[0]) * t),
            int(top[1] + (bottom[1] - top[1]) * t),
            int(top[2] + (bottom[2] - top[2]) * t),
        )
    return strip.resize((SIZE, SIZE))


def _fit_title(draw, title, font_path, max_width, start_size=76, min_size=40):
    """Pick the largest font size at which the wrapped title fits nicely."""
    for size in range(start_size, min_size - 1, -4):
        font = _font(font_path, size)
        avg_char = draw.textlength("x", font=font) or 1
        wrap_at = max(12, int(max_width / avg_char))
        lines = textwrap.wrap(title, width=wrap_at)
        if len(lines) <= 7:
            line_h = size + 14
            if len(lines) * line_h <= SIZE - 2 * MARGIN - 260:
                return font, lines, line_h
    font = _font(font_path, min_size)
    return font, textwrap.wrap(title, width=28)[:8], min_size + 14


def generate_card(account_key, display_name, title, source_label, out_path):
    top, bottom = PALETTES.get(account_key, DEFAULT_PALETTE)
    img = _gradient(top, bottom)
    draw = ImageDraw.Draw(img)

    # accent bar top-left
    draw.rectangle([MARGIN, MARGIN, MARGIN + 70, MARGIN + 10], fill=(255, 255, 255))
    badge_font = _font(_FONT_BOLD, 34)
    draw.text((MARGIN, MARGIN + 26), f"@{account_key}".upper(),
              font=badge_font, fill=(255, 255, 255))

    # title block, vertically centered-ish
    max_w = SIZE - 2 * MARGIN
    font, lines, line_h = _fit_title(draw, title, _FONT_BOLD, max_w)
    total_h = len(lines) * line_h
    y = (SIZE - total_h) // 2 - 40
    for line in lines:
        draw.text((MARGIN, y), line, font=font, fill=(255, 255, 255))
        y += line_h

    # footer: subject + source
    foot_font = _font(_FONT_REG, 30)
    footer = f"New in {display_name.replace(' News', '').replace(' Research', ' research')}"
    if source_label:
        footer += f"  ·  Source: {source_label}"
    draw.line([MARGIN, SIZE - MARGIN - 60, SIZE - MARGIN, SIZE - MARGIN - 60],
              fill=(255, 255, 255), width=2)
    draw.text((MARGIN, SIZE - MARGIN - 44), footer, font=foot_font,
              fill=(230, 230, 235))

    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    img.save(out_path, "PNG")
    return out_path
