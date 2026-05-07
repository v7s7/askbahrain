# Instagram Text Overlay Agent

Automatically overlays text on a template image and publishes it to Instagram — for free.

## How it works

1. You provide text + a template image
2. The agent renders the text on top of the image (Pillow)
3. The image is uploaded to [imgbb](https://imgbb.com) (free hosting) to get a public URL
4. The image is published to Instagram via the official **Graph API** (free)

## Setup

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Get your free credentials

#### Instagram Graph API (free)
You need an **Instagram Professional account** (Business or Creator — both free) connected to a **Facebook Page**.

1. Go to [developers.facebook.com](https://developers.facebook.com/) → Create App → Business type
2. Add the **Instagram Graph API** product
3. Connect your Instagram Professional account
4. Get your **Instagram User ID** and generate a **Long-Lived Access Token** (valid 60 days, renewable)

> Detailed guide: https://developers.facebook.com/docs/instagram-api/getting-started

#### imgbb API key (free)
1. Register at [imgbb.com](https://imgbb.com)
2. Go to https://api.imgbb.com/ → get your free API key

### 3. Configure

```bash
cp .env.example .env
# Edit .env with your credentials
```

### 4. Add your template image

Place your template image in the `templates/` folder:

```
templates/template.jpg   ← default template
```

Any JPG or PNG works. Recommended size: **1080×1080** (square) or **1080×1350** (portrait).

## Usage

```bash
# Basic usage
python agent.py --text "Your post text here"

# Use a custom template
python agent.py --text "Hello Bahrain!" --template templates/event.jpg

# Preview only (no Instagram publish)
python agent.py --text "Test post" --dry-run

# Custom font size and text position
python agent.py --text "Big text" --font-size 80 --vertical-pos 0.8

# White text (default) vs dark text
python agent.py --text "Dark text" --text-color "30,30,30"

# Custom Instagram caption
python agent.py --text "Overlay text" --caption "Full caption with hashtags #bahrain"
```

### All options

| Flag | Default | Description |
|---|---|---|
| `--text` | required | Text to overlay on image |
| `--template` | `templates/template.jpg` | Path to template image |
| `--caption` | same as text | Instagram caption |
| `--output` | `post.jpg` | Output filename in `output/` |
| `--font-size` | `60` | Font size in pixels |
| `--text-color` | `255,255,255` | Text color as R,G,B |
| `--vertical-pos` | `0.72` | Text vertical position (0=top, 1=bottom) |
| `--dry-run` | false | Generate image only, skip posting |

## Refreshing your access token

Instagram long-lived tokens expire after 60 days. Refresh before expiry:

```bash
curl -X GET "https://graph.facebook.com/v19.0/oauth/access_token \
  ?grant_type=fb_exchange_token \
  &client_id=YOUR_APP_ID \
  &client_secret=YOUR_APP_SECRET \
  &fb_exchange_token=YOUR_CURRENT_TOKEN"
```

## Project structure

```
askbahrain/
├── agent.py               # Main entry point (CLI)
├── image_processor.py     # Text-on-image rendering (Pillow)
├── instagram_publisher.py # Instagram Graph API + imgbb upload
├── templates/             # Put your template images here
├── output/                # Generated images (git-ignored)
├── .env.example           # Credential template
└── requirements.txt
```
