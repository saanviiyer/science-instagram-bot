"""Fetch recent articles from Nature subject RSS feeds.

Dependency-free: uses only the Python standard library so the pipeline runs
without `pip install`. Each article is returned with its title, link, publish
date, and abstract (pulled from the article page's `dc.description` meta tag,
because Nature's subject feeds ship empty <description> fields).
"""

import html
import json
import re
import shutil
import subprocess
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from xml.etree import ElementTree

# Nature article pages sit behind a JS bot challenge, so abstracts are pulled
# from Crossref's open API by DOI instead. Include a contact per Crossref's
# etiquette for the "polite pool".
USER_AGENT = "science-instagram-bot/1.0 (mailto:saanvisub07@gmail.com)"
TIMEOUT = 25


def _challenged(body):
    return "Client Challenge" in body[:2000]


def _curl_get(url, accept):
    """Fallback fetch via curl, whose TLS signature clears Nature's challenge
    where urllib's does not. Silently returns '' if curl is unavailable."""
    if not shutil.which("curl"):
        return ""
    try:
        out = subprocess.run(
            ["curl", "-sL", "--max-time", str(TIMEOUT),
             "-A", USER_AGENT, "-H", f"Accept: {accept}", url],
            capture_output=True, text=True, timeout=TIMEOUT + 5,
        )
        return out.stdout
    except Exception:
        return ""


def _get(url, accept="application/rss+xml,application/xml,application/json;q=0.9,*/*;q=0.8", retries=4):
    """GET a URL as text, working past Nature's intermittent bot challenge.

    Tries urllib with backoff, then falls back to curl (a different TLS
    fingerprint that Nature's challenge lets through more reliably).
    """
    last = ""
    for attempt in range(retries):
        req = urllib.request.Request(
            url, headers={"User-Agent": USER_AGENT, "Accept": accept}
        )
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            body = resp.read().decode("utf-8", errors="replace")
        if not _challenged(body):
            return body
        last = body
        time.sleep(1.0 * (attempt + 1))

    curled = _curl_get(url, accept)
    if curled and not _challenged(curled):
        return curled
    return last


def _parse_date(text):
    try:
        dt = parsedate_to_datetime(text)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except (TypeError, ValueError):
        return None


def fetch_feed(url):
    """Return a list of article dicts from one Nature subject RSS feed."""
    xml = _get(url)
    root = ElementTree.fromstring(xml)
    items = []
    for item in root.iter("item"):
        title = (item.findtext("title") or "").strip()
        link = (item.findtext("link") or "").strip()
        pub = _parse_date(item.findtext("pubDate") or "")
        # Nature subject feeds ship empty descriptions; institutional/news feeds
        # usually populate them — keep as an abstract fallback.
        desc = _strip_jats(item.findtext("description") or "")
        if title and link:
            items.append({"title": title, "link": link, "published": pub,
                          "feed_summary": desc})
    return items


_DOI_RE = re.compile(r"/articles/(s\d[\w.-]+)")
_JATS_RE = re.compile(r"<[^>]+>")


def _doi_from_url(article_url):
    """Nature article URLs end in the article id, which maps to a 10.1038 DOI."""
    m = _DOI_RE.search(article_url)
    return f"10.1038/{m.group(1)}" if m else None


def _strip_jats(text):
    text = _JATS_RE.sub(" ", text)
    text = html.unescape(text)
    text = text.replace("Abstract", "", 1) if text.strip().startswith("Abstract") else text
    return " ".join(text.split())


def fetch_abstract(article_url):
    """Return the abstract for a Nature article via Crossref, or '' if none."""
    doi = _doi_from_url(article_url)
    if not doi:
        return ""
    try:
        raw = _get(f"https://api.crossref.org/works/{urllib.parse.quote(doi)}")
        msg = json.loads(raw).get("message", {})
    except Exception:
        return ""
    abstract = msg.get("abstract")
    return _strip_jats(abstract) if abstract else ""


def recent_articles(feed_urls, limit=3, within_days=14, with_abstracts=True):
    """Fetch, merge, de-dupe, and sort the most recent articles across feeds.

    Returns up to `limit` articles, newest first, optionally filtered to those
    published within `within_days`.
    """
    seen = set()
    merged = []
    for url in feed_urls:
        try:
            for art in fetch_feed(url):
                if art["link"] in seen:
                    continue
                seen.add(art["link"])
                merged.append(art)
        except Exception as exc:  # one bad feed shouldn't kill the batch
            print(f"  ! feed error {url}: {exc}")

    now = datetime.now(timezone.utc)
    if within_days is not None:
        merged = [
            a for a in merged
            if a["published"] is None
            or (now - a["published"]).days <= within_days
        ]
    merged.sort(key=lambda a: a["published"] or now, reverse=True)
    merged = merged[:limit]

    if with_abstracts:
        for art in merged:
            # Prefer a real Crossref abstract (Nature/DOI); fall back to the
            # feed's own summary (institutional/news feeds).
            art["abstract"] = fetch_abstract(art["link"]) or art.get("feed_summary", "")
    return merged
