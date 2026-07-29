"""Turn an article into an Instagram caption + hashtags.

Two modes:
  * LLM mode  - if ANTHROPIC_API_KEY is set, Claude writes an original,
                engaging summary from the abstract (never copying source text).
  * template  - a deterministic fallback that needs no API key, so drafts can
                be generated immediately.

Hashtags are assembled from the account's curated pool + shared science tags,
capped for Instagram readability.
"""

import os
import textwrap

MODEL = "claude-sonnet-5"
MAX_HASHTAGS = 12
CAPTION_CHAR_TARGET = 550  # comfortably under IG's 2,200 limit


def _select_hashtags(account_cfg, common_tags):
    tags = list(dict.fromkeys(account_cfg["hashtags"] + common_tags))
    return tags[:MAX_HASHTAGS]


def _hook_prefix(account_cfg):
    return f"🔬 New in {account_cfg['display_name'].replace(' News', '')}"


def _source_line(source_name):
    if source_name:
        return f"📄 Source: {source_name} (link in bio 👆 / below)."
    return "📄 Read the full story (link in bio 👆 / below)."


def _template_caption(article, account_cfg, source_name):
    """No-API fallback: build a clean caption from title + abstract."""
    abstract = article.get("abstract", "").strip()
    if abstract:
        # first ~2 sentences, trimmed — an original framing, not a copy
        summary = " ".join(abstract.replace("\n", " ").split())
        if len(summary) > 320:
            cut = summary[:320].rsplit(". ", 1)[0]
            summary = cut + "." if cut else summary[:320] + "…"
    else:
        summary = "Read the full study for the details."

    body = (
        f"{_hook_prefix(account_cfg)}\n\n"
        f"“{article['title']}”\n\n"
        f"{summary}\n\n"
        f"{_source_line(source_name)}\n"
        f"Follow @{{account_handle}} for {account_cfg['topic_line']}."
    )
    return body


_LLM_PROMPT = """You write Instagram captions for a science-news account called \
"{display_name}" that covers {topic_line}.

Write an original, engaging caption for the research article below. Requirements:
- 2-4 short sentences (~60-90 words). Plain, exciting, accurate language for a \
general-but-curious audience.
- Open with a strong hook. Do NOT copy phrasing from the abstract — paraphrase \
in your own words.
- Explain why it matters. No hype, no fabricated results.
- End with a call to read the study. Do NOT include hashtags (added separately).
- Include 1-2 tasteful emoji max.

Article title: {title}
Abstract (source material — paraphrase, never quote at length): {abstract}

Return only the caption text."""


def _llm_caption(article, account_cfg):
    try:
        import anthropic
    except ImportError:
        return None
    if not os.environ.get("ANTHROPIC_API_KEY"):
        return None
    try:
        client = anthropic.Anthropic()
        msg = client.messages.create(
            model=MODEL,
            max_tokens=400,
            messages=[{
                "role": "user",
                "content": _LLM_PROMPT.format(
                    display_name=account_cfg["display_name"],
                    topic_line=account_cfg["topic_line"],
                    title=article["title"],
                    abstract=(article.get("abstract") or "(no abstract available)")[:2500],
                ),
            }],
        )
        return "".join(b.text for b in msg.content if b.type == "text").strip()
    except Exception as exc:
        print(f"  ! LLM caption failed, using template: {exc}")
        return None


def build_caption(article, account_key, account_cfg, common_tags, source_name="Nature"):
    """Return a dict: {caption, hashtags, full_text} for one article."""
    llm = _llm_caption(article, account_cfg)
    if llm:
        src = f"📄 Source: {source_name} — " if source_name else "📄 Read more: "
        caption = f"{llm}\n\n{src}{article['link']}"
    else:
        caption = _template_caption(article, account_cfg, source_name).replace(
            "{account_handle}", account_key
        )

    hashtags = _select_hashtags(account_cfg, common_tags)
    full_text = f"{caption}\n\n" + " ".join(hashtags)
    return {
        "caption": caption,
        "hashtags": hashtags,
        "full_text": full_text,
    }
