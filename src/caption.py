"""Turn an article into an Instagram caption + hashtags.

Two modes:
  * LLM mode  - if ANTHROPIC_API_KEY is set, Claude writes an original,
                engaging summary from the abstract (never copying source text).
  * template  - a deterministic fallback that needs no API key, so drafts can
                be generated immediately.

Hashtags are assembled from the account's curated pool + shared science tags,
capped for Instagram readability.
"""

import collections
import os
import textwrap

MODEL = "claude-sonnet-5"
MAX_HASHTAGS = 14
CAPTION_CHAR_TARGET = 550  # comfortably under IG's 2,200 limit


def _rotate(items, seed):
    if not items:
        return []
    d = collections.deque(items)
    d.rotate(-(seed % len(items)))
    return list(d)


def _select_hashtags(account_cfg, common_tags, seed=0):
    """Mix niche/mid/broad tags, rotating within each tier so posts vary.

    Accepts either a tiered dict {niche,mid,broad} or a flat list (institutions).
    """
    tags = account_cfg["hashtags"]
    if isinstance(tags, dict):
        picked = (
            _rotate(tags.get("niche", []), seed)[:6]
            + _rotate(tags.get("mid", []), seed)[:4]
            + _rotate(tags.get("broad", []) + list(common_tags), seed)[:4]
        )
    else:
        picked = _rotate(tags, seed)[:9] + list(common_tags)[:4]
    return list(dict.fromkeys(picked))[:MAX_HASHTAGS]


def summarize(abstract, max_len=320):
    """Trim an abstract to a short factual summary (first sentences)."""
    if not abstract or not abstract.strip():
        return ""
    text = " ".join(abstract.replace("\n", " ").split())
    if len(text) > max_len:
        cut = text[:max_len].rsplit(". ", 1)[0]
        text = (cut + ".") if cut else (text[:max_len] + "…")
    return _enforce_style(text)


def _subject(account_cfg):
    return (account_cfg["display_name"]
            .replace(" News", "").replace(" Research", " research"))


# Closing prompts to the audience. Genuine questions/invites (not the banned
# "open with a question you answer yourself"). {subject} is filled per account.
_QUESTIONS = [
    "What would you want researchers to look at next in {subject}?",
    "Does this change how you think about {subject}?",
    "Surprising, or did you see this coming?",
    "Worth a save if you follow {subject}. What stands out to you?",
    "How do you think this plays out over the next few years?",
    "Curious what you make of this. Tell us below.",
]


def _source_line(source_name):
    if source_name:
        return f"📄 Source: {source_name} (link in bio 👆)"
    return "📄 Full story in bio 👆"


def _template_caption(article, account_cfg, source_name, seed=0):
    """No-API caption: lead with the finding, then a question to the audience."""
    subject = _subject(account_cfg)
    summary = summarize(article.get("abstract", ""))
    lead = summary if summary else f"A new study on {article['title'].rstrip('.').lower()}."
    question = _rotate(_QUESTIONS, seed)[0].format(subject=subject)

    parts = [
        lead,
        f"“{article['title']}”",
        question,
        f"{_source_line(source_name)}\n"
        f"Follow @{{account_handle}} for {account_cfg['topic_line']}.",
    ]
    return "\n\n".join(parts)


_LLM_PROMPT = """You write Instagram captions for a science-news account called \
"{display_name}" that covers {topic_line}.

Write an original caption for the research article below.

Content rules:
- 2 to 4 sentences, about 60 to 90 words. Plain, clear language for a curious \
general reader.
- Paraphrase the abstract in your own words. Never copy its phrasing and never \
quote more than a few words.
- Say what the finding is and why it matters. No hype, no invented results.
- End with a short line inviting people to read the study.
- At most one emoji. Do not add hashtags (they are added separately).

Writing style (follow strictly):
- No em dashes anywhere. Use a period, comma, or parentheses instead.
- No semicolons joining two clauses that could be sentences. No colon used for a \
dramatic reveal.
- Do not use a list of three parallel items in a sentence.
- Do not use the "not just X, it's Y" construction in any form.
- Do not open with a manufactured hook or a rhetorical question you then answer.
- Do not end with a summary line that restates what you just said.
- Avoid these words: framework, leverage, unlock, elevate, delve, dive into, \
navigate, landscape, robust, holistic, seamless, streamline, empower, foster, \
harness, unpack, game-changer, cutting-edge, myriad, plethora, boasts, \
showcases, paves the way, plays a crucial/pivotal role, in today's world, when \
it comes to, it's worth noting, it's important to note, ultimately.
- Say things plainly. Let sentence length vary with the content rather than a beat.

Article title: {title}
Abstract (source material, paraphrase and do not quote at length): {abstract}

Return only the caption text."""


def _enforce_style(text):
    """Deterministic backstop for the writing rules the prompt asks for:
    no em/en dashes reach a published caption even if the model slips."""
    text = text.replace(" — ", ", ").replace("—", ", ")
    text = text.replace(" – ", ", ").replace("–", "-")
    return text.strip()


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
        raw = "".join(b.text for b in msg.content if b.type == "text").strip()
        return _enforce_style(raw)
    except Exception as exc:
        print(f"  ! LLM caption failed, using template: {exc}")
        return None


def build_caption(article, account_key, account_cfg, common_tags, source_name="Nature", seed=0):
    """Return a dict: {caption, hashtags, full_text} for one article."""
    llm = _llm_caption(article, account_cfg)
    if llm:
        src = f"📄 Source ({source_name}): " if source_name else "📄 Read more: "
        caption = f"{llm}\n\n{src}{article['link']}"
    else:
        caption = _enforce_style(
            _template_caption(article, account_cfg, source_name, seed).replace(
                "{account_handle}", account_key
            )
        )

    hashtags = _select_hashtags(account_cfg, common_tags, seed)
    full_text = f"{caption}\n\n" + " ".join(hashtags)
    return {
        "caption": caption,
        "hashtags": hashtags,
        "full_text": full_text,
    }
