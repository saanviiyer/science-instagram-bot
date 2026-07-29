"""Publish a draft to Instagram via the Meta Graph API.

Instagram content publishing is a two-step flow:
  1. Create a media container:  POST /{ig_user_id}/media
       - image_url (REQUIRED — must be a publicly reachable URL), caption
  2. Publish the container:      POST /{ig_user_id}/media_publish

Hard requirements before this can run for real:
  * Each account is an Instagram *Business* or *Creator* account.
  * It is linked to a Facebook Page inside a Meta Business Suite portfolio.
  * You have a Meta developer app with the Instagram Graph API product and a
    long-lived access token with instagram_content_publish permission.
  * Every post needs an IMAGE. Instagram has no text-only feed post — you must
    supply a publicly hosted image_url per draft.

Credentials are read from the environment, never hard-coded:
  IG_USER_ID__<ACCOUNT>     e.g. IG_USER_ID__NEURONEWS
  IG_TOKEN__<ACCOUNT>       e.g. IG_TOKEN__NEURONEWS

Safety: publish() refuses to post unless BOTH credentials are present AND the
caller passes confirm=True. Without that it performs a dry run and returns what
*would* be sent. This is intentional — automated public posting stays behind an
explicit per-call approval.
"""

import json
import os
import urllib.parse
import urllib.request

GRAPH_VERSION = "v21.0"
GRAPH_BASE = f"https://graph.facebook.com/{GRAPH_VERSION}"


def _env_key(account_key):
    return account_key.upper().replace("-", "_")


def credentials(account_key):
    """Return (ig_user_id, token) from the environment, or (None, None)."""
    k = _env_key(account_key)
    return (
        os.environ.get(f"IG_USER_ID__{k}"),
        os.environ.get(f"IG_TOKEN__{k}"),
    )


def _post(url, params):
    data = urllib.parse.urlencode(params).encode()
    req = urllib.request.Request(url, data=data, method="POST")
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode())


def publish(account_key, caption, image_urls, confirm=False):
    """Publish (or dry-run) a post to an account.

    `image_urls` may be a single URL string or a list. One URL posts a single
    image; two or more posts a carousel. Never posts unless credentials exist
    AND confirm=True.
    """
    if isinstance(image_urls, str):
        image_urls = [image_urls]
    image_urls = [u for u in (image_urls or []) if u]

    ig_user_id, token = credentials(account_key)

    plan = {
        "account": account_key,
        "image_urls": image_urls,
        "slides": len(image_urls),
        "caption_preview": caption[:120] + ("…" if len(caption) > 120 else ""),
        "has_credentials": bool(ig_user_id and token),
        "confirmed": bool(confirm),
    }

    if not image_urls:
        plan.update(status="blocked", reason="Instagram feed posts require an image.")
        return plan
    if not (ig_user_id and token):
        plan.update(status="dry-run",
                    reason="No IG_USER_ID__/IG_TOKEN__ env vars for this account.")
        return plan
    if not confirm:
        plan.update(status="dry-run", reason="confirm=False (per-post approval required).")
        return plan

    # --- real publish ---
    if len(image_urls) == 1:
        container = _post(f"{GRAPH_BASE}/{ig_user_id}/media", {
            "image_url": image_urls[0],
            "caption": caption,
            "access_token": token,
        })
        creation_id = container.get("id")
    else:
        # carousel: one child container per slide, then a parent container
        child_ids = []
        for url in image_urls:
            child = _post(f"{GRAPH_BASE}/{ig_user_id}/media", {
                "image_url": url,
                "is_carousel_item": "true",
                "access_token": token,
            })
            if not child.get("id"):
                plan.update(status="error", reason="child container failed",
                            response=child)
                return plan
            child_ids.append(child["id"])
        parent = _post(f"{GRAPH_BASE}/{ig_user_id}/media", {
            "media_type": "CAROUSEL",
            "children": ",".join(child_ids),
            "caption": caption,
            "access_token": token,
        })
        creation_id = parent.get("id")

    if not creation_id:
        plan.update(status="error", reason="No creation_id")
        return plan

    result = _post(f"{GRAPH_BASE}/{ig_user_id}/media_publish", {
        "creation_id": creation_id,
        "access_token": token,
    })
    plan.update(status="published", creation_id=creation_id, media_id=result.get("id"),
                response=result)
    return plan
