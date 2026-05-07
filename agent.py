#!/usr/bin/env python3
"""
Instagram Text Overlay Agent
-----------------------------
Usage:
  python agent.py --text "Your post text here" --template templates/my_template.jpg

Run `python agent.py --help` for all options.
"""

import argparse
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

from image_processor import add_text_to_image
from instagram_publisher import publish_to_instagram

load_dotenv()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Overlay text on an image and post to Instagram.")
    parser.add_argument("--text", required=True, help="Text to overlay on the image")
    parser.add_argument(
        "--template",
        default="templates/template.jpg",
        help="Path to the template image (default: templates/template.jpg)",
    )
    parser.add_argument(
        "--caption",
        default=None,
        help="Instagram caption (defaults to the text + DEFAULT_CAPTION from .env)",
    )
    parser.add_argument(
        "--output",
        default="post.jpg",
        help="Output filename inside the output/ directory (default: post.jpg)",
    )
    parser.add_argument(
        "--font-size",
        type=int,
        default=60,
        help="Font size for the overlay text (default: 60)",
    )
    parser.add_argument(
        "--text-color",
        default="255,255,255",
        help="RGB text color as R,G,B (default: 255,255,255 = white)",
    )
    parser.add_argument(
        "--vertical-pos",
        type=float,
        default=0.72,
        help="Vertical position of text: 0.0=top, 1.0=bottom (default: 0.72)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Generate the image but do NOT publish to Instagram",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    template = args.template
    if not Path(template).exists():
        sys.exit(f"Template not found: {template}\nPlace your image in the templates/ folder.")

    text_color = tuple(int(c) for c in args.text_color.split(","))

    print(f"Generating image with text: {args.text!r}")
    output_path = add_text_to_image(
        template_path=template,
        text=args.text,
        output_filename=args.output,
        font_size=args.font_size,
        text_color=text_color,
        vertical_position=args.vertical_pos,
    )
    print(f"Image saved to: {output_path}")

    if args.dry_run:
        print("Dry-run mode — skipping Instagram publish.")
        return

    user_id = os.getenv("INSTAGRAM_USER_ID")
    access_token = os.getenv("INSTAGRAM_ACCESS_TOKEN")
    imgbb_key = os.getenv("IMGBB_API_KEY")
    default_caption = os.getenv("DEFAULT_CAPTION", "")

    missing = [k for k, v in {
        "INSTAGRAM_USER_ID": user_id,
        "INSTAGRAM_ACCESS_TOKEN": access_token,
        "IMGBB_API_KEY": imgbb_key,
    }.items() if not v]
    if missing:
        sys.exit(
            f"Missing environment variables: {', '.join(missing)}\n"
            "Copy .env.example to .env and fill in your credentials."
        )

    caption = args.caption or f"{args.text}\n\n{default_caption}".strip()

    media_id = publish_to_instagram(
        image_path=output_path,
        caption=caption,
        user_id=user_id,
        access_token=access_token,
        imgbb_api_key=imgbb_key,
    )
    print(f"\nDone! Instagram media ID: {media_id}")


if __name__ == "__main__":
    main()
