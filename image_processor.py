"""Overlay text on a template image and save to the output directory."""

import os
import textwrap
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


OUTPUT_DIR = Path(__file__).parent / "output"
OUTPUT_DIR.mkdir(exist_ok=True)

# Pillow ships with a basic built-in font; we fall back to it when no TTF is found.
_FALLBACK_FONT_SIZE = 40
_DEFAULT_FONT_PATH = None  # set to a .ttf path to use a custom font


def _load_font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    if _DEFAULT_FONT_PATH and os.path.exists(_DEFAULT_FONT_PATH):
        return ImageFont.truetype(_DEFAULT_FONT_PATH, size)
    # Try common system fonts
    candidates = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
        "C:/Windows/Fonts/arial.ttf",
    ]
    for path in candidates:
        if os.path.exists(path):
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


def add_text_to_image(
    template_path: str,
    text: str,
    output_filename: str = "post.jpg",
    font_size: int = 60,
    text_color: tuple[int, int, int] = (255, 255, 255),
    shadow_color: tuple[int, int, int] = (0, 0, 0),
    max_width_ratio: float = 0.85,
    vertical_position: float = 0.72,
) -> str:
    """
    Draws `text` on top of `template_path` and saves the result.

    vertical_position: 0.0 = top, 1.0 = bottom of the image.
    Returns the absolute path of the saved image.
    """
    img = Image.open(template_path).convert("RGB")
    draw = ImageDraw.Draw(img)
    font = _load_font(font_size)

    img_w, img_h = img.size
    max_text_width = int(img_w * max_width_ratio)

    # Wrap text so it fits inside the image width
    wrapped = _wrap_text(draw, text, font, max_text_width)

    # Measure the full text block
    block_w, block_h = _measure_block(draw, wrapped, font)

    x = (img_w - block_w) // 2
    y = int(img_h * vertical_position) - block_h // 2

    _draw_text_block(draw, wrapped, font, x, y, text_color, shadow_color)

    out_path = str(OUTPUT_DIR / output_filename)
    img.save(out_path, quality=95)
    return out_path


def _wrap_text(
    draw: ImageDraw.ImageDraw, text: str, font: ImageFont.FreeTypeFont, max_width: int
) -> list[str]:
    words = text.split()
    lines: list[str] = []
    current = ""
    for word in words:
        test = f"{current} {word}".strip()
        w = draw.textlength(test, font=font)
        if w <= max_width:
            current = test
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


def _measure_block(
    draw: ImageDraw.ImageDraw, lines: list[str], font: ImageFont.FreeTypeFont
) -> tuple[int, int]:
    line_h = draw.textbbox((0, 0), "Ag", font=font)[3]
    spacing = int(line_h * 0.25)
    total_h = line_h * len(lines) + spacing * (len(lines) - 1)
    max_w = max(int(draw.textlength(line, font=font)) for line in lines)
    return max_w, total_h


def _draw_text_block(
    draw: ImageDraw.ImageDraw,
    lines: list[str],
    font: ImageFont.FreeTypeFont,
    x: int,
    y: int,
    color: tuple[int, int, int],
    shadow: tuple[int, int, int],
) -> None:
    line_h = draw.textbbox((0, 0), "Ag", font=font)[3]
    spacing = int(line_h * 0.25)
    offset = 3  # shadow offset in pixels

    for i, line in enumerate(lines):
        line_w = int(draw.textlength(line, font=font))
        # Center each line individually
        lx = x + (draw.textlength(lines[0], font=font) - line_w) // 2 if len(lines) > 1 else x
        ly = y + i * (line_h + spacing)
        # Draw shadow first
        draw.text((lx + offset, ly + offset), line, font=font, fill=shadow)
        draw.text((lx, ly), line, font=font, fill=color)
