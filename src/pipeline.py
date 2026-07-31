"""CLI: fetch → draft → (optionally) publish science Instagram posts.

Usage:
  python -m src.pipeline draft --account neuronews --limit 3
  python -m src.pipeline draft --all --limit 2
  python -m src.pipeline list
  python -m src.pipeline publish --account neuronews --draft <draft_id> \
         --image-url https://.../card.png --confirm

Drafts are written to drafts/<account>/<date>_<n>.json and a human-readable
.md preview alongside. Nothing is posted unless you run `publish ... --confirm`
with credentials configured (see README).
"""

import argparse
import json
import os
import sys
from datetime import datetime, timezone

_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _PROJECT_ROOT)


def _load_dotenv():
    """Load .env so ANTHROPIC_API_KEY (and any tokens) are available without
    manually exporting them. Does not override real environment variables."""
    path = os.path.join(_PROJECT_ROOT, ".env")
    if not os.path.exists(path):
        return
    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, val = line.partition("=")
            os.environ.setdefault(key.strip(), val.strip().strip('"').strip("'"))


_load_dotenv()

from src import feeds, caption, publish

try:
    from src import cards
    _CARDS_OK = True
except ImportError:  # Pillow not installed — skip image cards gracefully
    _CARDS_OK = False

DRAFTS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "drafts")

# Active config is selected by --config (topics | institutions), default topics.
ACCOUNTS = {}
COMMON_TAGS = []
SOURCE_NAME = "Nature"
feed_urls = None


def _load_config(name):
    global ACCOUNTS, COMMON_TAGS, SOURCE_NAME, feed_urls
    if name == "institutions":
        from config import institutions as cfg
    else:
        from config import accounts as cfg
    ACCOUNTS = cfg.ACCOUNTS
    COMMON_TAGS = cfg.COMMON_TAGS
    SOURCE_NAME = getattr(cfg, "SOURCE_NAME", "Nature")
    feed_urls = cfg.feed_urls


def _today():
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def _slug(text, n=40):
    keep = "".join(c if c.isalnum() else "-" for c in text.lower())
    return "-".join(w for w in keep.split("-") if w)[:n]


def draft_account(account_key, limit, within_days, args_no_cards=False):
    cfg = ACCOUNTS[account_key]
    print(f"\n=== @{account_key} ({cfg['display_name']}) ===")
    articles = feeds.recent_articles(
        feed_urls(account_key), limit=limit, within_days=within_days
    )
    if not articles:
        print("  no recent articles found")
        return []

    out_dir = os.path.join(DRAFTS_DIR, account_key)
    os.makedirs(out_dir, exist_ok=True)
    drafts = []
    for i, art in enumerate(articles, 1):
        built = caption.build_caption(art, account_key, cfg, COMMON_TAGS,
                                      SOURCE_NAME, seed=i)
        draft = {
            "id": f"{_today()}_{i:02d}_{_slug(art['title'])}",
            "account": account_key,
            "title": art["title"],
            "source_url": art["link"],
            "published": art["published"].isoformat() if art["published"] else None,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "caption": built["caption"],
            "hashtags": built["hashtags"],
            "full_text": built["full_text"],
            "image_paths": [],   # local carousel slide PNGs (below)
            "image_urls": [],    # public URLs — filled after hosting
            "image_path": None,  # slide 1 (preview / single-image fallback)
            "image_url": None,   # slide 1 public URL
        }

        if _CARDS_OK and not args_no_cards:
            try:
                slides = cards.generate_carousel(
                    account_key, cfg["display_name"], art["title"],
                    caption.summarize(art.get("abstract", "")),
                    cfg["topic_line"], SOURCE_NAME, out_dir, draft["id"])
                draft["image_paths"] = slides
                draft["image_path"] = slides[0] if slides else None
            except Exception as exc:
                print(f"    ! card render failed: {exc}")

        json_path = os.path.join(out_dir, draft["id"] + ".json")
        md_path = os.path.join(out_dir, draft["id"] + ".md")
        with open(json_path, "w") as f:
            json.dump(draft, f, indent=2)
        with open(md_path, "w") as f:
            f.write(f"# {art['title']}\n\n")
            f.write(f"**Account:** @{account_key}  \n")
            f.write(f"**Source:** {art['link']}  \n")
            f.write(f"**Published:** {draft['published']}\n\n")
            for n, p in enumerate(draft["image_paths"], 1):
                f.write(f"![slide {n}]({os.path.basename(p)})\n\n")
            f.write("---\n\n")
            f.write(built["full_text"] + "\n")
        drafts.append(draft)
        print(f"  ✓ [{i}] {art['title'][:70]}")
    return drafts


def cmd_draft(args):
    within = None if args.within_days == 0 else args.within_days
    if args.all:
        keys = list(ACCOUNTS)
    elif args.account:
        keys = [args.account]
    else:
        print("specify --account <key> or --all")
        return
    total = 0
    for key in keys:
        if key not in ACCOUNTS:
            print(f"  ! unknown account: {key}")
            continue
        total += len(draft_account(key, args.limit, within, args.no_cards))
    print(f"\nDone. {total} draft(s) written under {DRAFTS_DIR}/")


def cmd_list(args):
    for key in ACCOUNTS:
        d = os.path.join(DRAFTS_DIR, key)
        if not os.path.isdir(d):
            continue
        drafts = sorted(f for f in os.listdir(d) if f.endswith(".json"))
        if drafts:
            print(f"@{key}:")
            for f in drafts:
                print(f"    {f[:-5]}")


def cmd_publish(args):
    path = os.path.join(DRAFTS_DIR, args.account, args.draft + ".json")
    if not os.path.exists(path):
        print(f"draft not found: {path}")
        return
    with open(path) as f:
        draft = json.load(f)
    if args.image_url:
        image_urls = [args.image_url]
    else:
        image_urls = draft.get("image_urls") or (
            [draft["image_url"]] if draft.get("image_url") else [])
    result = publish.publish(
        args.account, draft["full_text"], image_urls, confirm=args.confirm
    )
    print(json.dumps(result, indent=2))
    if result["status"] == "dry-run":
        print("\n(dry run — add credentials + --confirm to post for real)")


def _load_draft(path):
    with open(path) as f:
        return json.load(f)


def cmd_post_due(args):
    """Publish each account's freshest un-posted draft once its slot passed.

    Real posting requires per-account tokens AND opt-in (--confirm or
    AUTO_PUBLISH=1). Otherwise every account dry-runs. A draft is only marked
    posted on a real success, so nothing double-posts.
    """
    from config.schedule import POST_SLOTS

    confirm = args.confirm or os.environ.get("AUTO_PUBLISH") == "1"
    now = datetime.now()
    today = now.strftime("%Y-%m-%d")

    for account, hhmm in POST_SLOTS.items():
        if account not in ACCOUNTS:
            continue
        hh, mm = (int(x) for x in hhmm.split(":"))
        slot = now.replace(hour=hh, minute=mm, second=0, microsecond=0)
        if now < slot:
            continue

        d = os.path.join(DRAFTS_DIR, account)
        if not os.path.isdir(d):
            continue
        jsons = sorted(os.path.join(d, f) for f in os.listdir(d) if f.endswith(".json"))
        drafts = [(_load_draft(p), p) for p in jsons]

        if any((dr.get("posted_at") or "").startswith(today) for dr, _ in drafts):
            continue  # already posted today
        unposted = [(dr, p) for dr, p in drafts if not dr.get("posted_at")]
        if not unposted:
            continue

        draft, path = unposted[-1]  # freshest
        image_urls = draft.get("image_urls") or (
            [draft["image_url"]] if draft.get("image_url") else [])
        result = publish.publish(account, draft["full_text"], image_urls, confirm=confirm)
        print(f"[{hhmm}] @{account}: {result['status']}"
              + (f" ({result.get('reason')})" if result.get("reason") else ""))
        if result["status"] == "published":
            draft["posted_at"] = now.isoformat()
            draft["media_id"] = result.get("media_id")
            with open(path, "w") as f:
                json.dump(draft, f, indent=2)


def main():
    p = argparse.ArgumentParser(description="Science Instagram pipeline")
    p.add_argument("--config", choices=["topics", "institutions"], default="topics",
                   help="which account set to use (default: topics)")
    sub = p.add_subparsers(dest="cmd", required=True)

    d = sub.add_parser("draft", help="generate drafts from Nature feeds")
    d.add_argument("--account")
    d.add_argument("--all", action="store_true")
    d.add_argument("--limit", type=int, default=3)
    d.add_argument("--within-days", type=int, default=21,
                   help="max article age in days (0 = no limit)")
    d.add_argument("--no-cards", action="store_true",
                   help="skip PNG image-card generation")
    d.set_defaults(func=cmd_draft)

    l = sub.add_parser("list", help="list existing drafts")
    l.set_defaults(func=cmd_list)

    pub = sub.add_parser("publish", help="publish a draft (gated)")
    pub.add_argument("--account", required=True)
    pub.add_argument("--draft", required=True)
    pub.add_argument("--image-url")
    pub.add_argument("--confirm", action="store_true")
    pub.set_defaults(func=cmd_publish)

    pd = sub.add_parser("post-due",
                        help="publish accounts whose scheduled slot has passed")
    pd.add_argument("--confirm", action="store_true",
                    help="actually post (also enabled by AUTO_PUBLISH=1)")
    pd.set_defaults(func=cmd_post_due)

    args = p.parse_args()
    _load_config(args.config)
    args.func(args)


if __name__ == "__main__":
    main()
