"""Host card images on GitHub Pages so each post gets a public image_url.

Uses THIS project's own repo (the git repo at the project root, e.g.
github.com/<user>/science-instagram-bot) and serves card images from its
`docs/` folder via GitHub Pages.

Flow:
  1. Copy every draft PNG into `docs/cards/<account>/`.
  2. Write the resulting public URL back into each draft's `image_url`.
  3. Commit + push; enable Pages (main branch, /docs) via `gh` if available.

Public URL pattern (Pages serves /docs as the site root):
  https://<GITHUB_USER>.github.io/<repo>/cards/<account>/<file>.png

Config via .env (auto-loaded):
  GITHUB_USER=your-github-username
  GITHUB_PAGES_REPO=science-instagram-bot   # the repo whose Pages hosts cards
"""

import glob
import json
import os
import shutil
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DRAFTS = os.path.join(ROOT, "drafts")
DOCS = os.path.join(ROOT, "docs")


def _load_dotenv():
    """Minimal .env loader (no external deps). Does not override real env vars."""
    path = os.path.join(ROOT, ".env")
    if not os.path.exists(path):
        return
    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, val = line.partition("=")
            key, val = key.strip(), val.strip().strip('"').strip("'")
            os.environ.setdefault(key, val)


def _cfg():
    user = os.environ.get("GITHUB_USER")
    repo = os.environ.get("GITHUB_PAGES_REPO", "science-instagram-bot")
    return user, repo


def public_url(user, repo, account, filename):
    return f"https://{user}.github.io/{repo}/cards/{account}/{filename}"


def _has_gh():
    return shutil.which("gh") is not None


def _run(cmd, cwd=ROOT, check=False):
    print("  $", " ".join(cmd))
    return subprocess.run(cmd, cwd=cwd, check=check, text=True, capture_output=True)


def prepare_docs():
    os.makedirs(DOCS, exist_ok=True)
    open(os.path.join(DOCS, ".nojekyll"), "a").close()
    idx = os.path.join(DOCS, "index.html")
    if not os.path.exists(idx):
        with open(idx, "w") as f:
            f.write("<!doctype html><meta charset=utf-8>"
                    "<title>Science IG cards</title>"
                    "<h1>Science Instagram card host</h1>"
                    "<p>Auto-generated card images live under /cards/.</p>")


def sync(user, repo):
    """Copy cards into docs/, rewrite draft image_urls, return count."""
    n = 0
    for json_path in glob.glob(os.path.join(DRAFTS, "*", "*.json")):
        with open(json_path) as f:
            draft = json.load(f)
        src_png = draft.get("image_path")
        if not src_png or not os.path.exists(src_png):
            continue
        account = draft["account"]
        filename = os.path.basename(src_png)
        dst_dir = os.path.join(DOCS, "cards", account)
        os.makedirs(dst_dir, exist_ok=True)
        shutil.copy2(src_png, os.path.join(dst_dir, filename))
        draft["image_url"] = public_url(user, repo, account, filename)
        with open(json_path, "w") as f:
            json.dump(draft, f, indent=2)
        n += 1
    return n


def push(message="update cards"):
    if not os.path.isdir(os.path.join(ROOT, ".git")):
        print("  ! project is not a git repo; run `git init` + add remote first.")
        return False
    _run(["git", "add", "-A"])
    r = _run(["git", "commit", "-m", message])
    if r.returncode != 0 and "nothing to commit" in (r.stdout + r.stderr):
        print("  (nothing new to commit)")
    p = _run(["git", "push", "-u", "origin", "main"])
    if p.returncode != 0:
        print("  ! push failed:\n" + (p.stderr or p.stdout))
        return False
    print("  pushed to origin/main")
    return True


def enable_pages(user, repo):
    if not _has_gh():
        print("  enable Pages manually: Settings → Pages → Deploy from branch → main / docs")
        return
    p = _run(["gh", "api", "-X", "POST", f"repos/{user}/{repo}/pages",
              "-f", "source[branch]=main", "-f", "source[path]=/docs"])
    if p.returncode == 0:
        print(f"  Pages enabled → https://{user}.github.io/{repo}/")
    elif "409" in (p.stdout + p.stderr):
        print("  Pages already enabled.")
    else:
        print("  (enable Pages manually: Settings → Pages → main / docs)")


def main():
    _load_dotenv()
    user, repo = _cfg()
    if not user:
        print("Set GITHUB_USER in .env first.")
        sys.exit(1)

    print(f"Hosting cards → https://{user}.github.io/{repo}/cards/")
    prepare_docs()
    count = sync(user, repo)
    print(f"  synced {count} card(s), wrote image_url into their drafts")
    if push():
        enable_pages(user, repo)


if __name__ == "__main__":
    main()
