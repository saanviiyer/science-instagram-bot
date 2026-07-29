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


def publish(account_key, caption, image_url, confirm=False):
    """Publish (or dry-run) one image post to an account.

    Returns a result dict. Never posts unless credentials exist AND confirm=True.
    """
    ig_user_id, token = credentials(account_key)

    plan = {
        "account": account_key,
        "image_url": image_url,
        "caption_preview": caption[:120] + ("…" if len(caption) > 120 else ""),
        "has_credentials": bool(ig_user_id and token),
        "confirmed": bool(confirm),
    }

    if not image_url:
        plan.update(status="blocked", reason="Instagram feed posts require an image_url.")
        return plan
    if not (ig_user_id and token):
        plan.update(status="dry-run",
                    reason="No IG_USER_ID__/IG_TOKEN__ env vars for this account.")
        return plan
    if not confirm:
        plan.update(status="dry-run", reason="confirm=False (per-post approval required).")
        return plan

    # --- real publish ---
    container = _post(f"{GRAPH_BASE}/{ig_user_id}/media", {
        "image_url": image_url,
        "caption": caption,
        "access_token": token,
    })
    creation_id = container.get("id")
    if not creation_id:
        plan.update(status="error", reason="No creation_id", response=container)
        return plan

    result = _post(f"{GRAPH_BASE}/{ig_user_id}/media_publish", {
        "creation_id": creation_id,
        "access_token": token,
    })
    plan.update(status="published", creation_id=creation_id, media_id=result.get("id"),
                response=result)
    return plan
