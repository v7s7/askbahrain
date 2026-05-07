"""Publish an image to Instagram via the free Graph API."""

import os
import time

import requests


GRAPH_BASE = "https://graph.facebook.com/v19.0"


def upload_image_to_imgbb(image_path: str, api_key: str) -> str:
    """Upload a local image to imgbb (free hosting) and return its public URL."""
    with open(image_path, "rb") as f:
        response = requests.post(
            "https://api.imgbb.com/1/upload",
            params={"key": api_key},
            files={"image": f},
            timeout=60,
        )
    response.raise_for_status()
    data = response.json()
    if not data.get("success"):
        raise RuntimeError(f"imgbb upload failed: {data}")
    return data["data"]["url"]


def publish_to_instagram(
    image_path: str,
    caption: str,
    user_id: str,
    access_token: str,
    imgbb_api_key: str,
) -> str:
    """
    Full publish flow:
      1. Upload image to imgbb to get a public URL.
      2. Create an Instagram media container.
      3. Publish the container.

    Returns the published media ID.
    """
    print("Uploading image to hosting service...")
    image_url = upload_image_to_imgbb(image_path, imgbb_api_key)
    print(f"Image hosted at: {image_url}")

    print("Creating Instagram media container...")
    container_resp = requests.post(
        f"{GRAPH_BASE}/{user_id}/media",
        params={
            "image_url": image_url,
            "caption": caption,
            "access_token": access_token,
        },
        timeout=60,
    )
    container_resp.raise_for_status()
    container_id = container_resp.json().get("id")
    if not container_id:
        raise RuntimeError(f"Failed to create container: {container_resp.json()}")
    print(f"Container created: {container_id}")

    # Instagram recommends a short wait before publishing
    time.sleep(2)

    print("Publishing to Instagram...")
    publish_resp = requests.post(
        f"{GRAPH_BASE}/{user_id}/media_publish",
        params={
            "creation_id": container_id,
            "access_token": access_token,
        },
        timeout=60,
    )
    publish_resp.raise_for_status()
    media_id = publish_resp.json().get("id")
    if not media_id:
        raise RuntimeError(f"Failed to publish: {publish_resp.json()}")

    print(f"Published! Media ID: {media_id}")
    return media_id
