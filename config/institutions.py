"""Institution accounts (researchatcaltech, researchatstanford, …).

Same pipeline, different source: instead of Nature subject feeds, these pull
from each university's research-news RSS feed. Those feeds carry populated
<description> fields, so abstracts come straight from the feed (no Crossref).

Feed URLs below are best-known public endpoints — verify each once and adjust
if an institution changes its CMS. Use exactly like the topic accounts:

    from config.institutions import ACCOUNTS as INST_ACCOUNTS
    (or run the pipeline with --config institutions)
"""

COMMON_TAGS = ["#research", "#science", "#university", "#discovery", "#stem"]

# Institutional posts link to the university newsroom rather than one journal.
SOURCE_NAME = None

ACCOUNTS = {
    "researchatcaltech": {
        "display_name": "Caltech Research",
        # Caltech has no reliable public RSS, so use a Google News query scoped
        # to Caltech research (the universal fallback for any such institution).
        "feed_urls": [
            "https://news.google.com/rss/search?q=Caltech%20research%20when:30d&hl=en-US&gl=US&ceid=US:en"
        ],
        "topic_line": "the latest research from Caltech",
        "hashtags": [
            "#caltech", "#research", "#science", "#engineering",
            "#innovation", "#technology", "#discovery", "#academia",
        ],
    },
    "researchatstanford": {
        "display_name": "Stanford Research",
        "feed_urls": ["https://news.stanford.edu/feed/"],
        "topic_line": "the latest research from Stanford",
        "hashtags": [
            "#stanford", "#research", "#science", "#innovation",
            "#technology", "#discovery", "#academia", "#stanforduniversity",
        ],
    },
    "researchatmit": {
        "display_name": "MIT Research",
        "feed_urls": ["https://news.mit.edu/rss/research"],
        "topic_line": "the latest research from MIT",
        "hashtags": [
            "#mit", "#research", "#science", "#engineering",
            "#innovation", "#technology", "#discovery", "#academia",
        ],
    },
    "researchatharvard": {
        "display_name": "Harvard Research",
        "feed_urls": ["https://news.harvard.edu/gazette/feed/"],
        "topic_line": "the latest research from Harvard",
        "hashtags": [
            "#harvard", "#research", "#science", "#innovation",
            "#discovery", "#academia", "#harvarduniversity", "#highered",
        ],
    },
    "researchatberkeley": {
        "display_name": "Berkeley Research",
        "feed_urls": ["https://news.berkeley.edu/feed/"],
        "topic_line": "the latest research from UC Berkeley",
        "hashtags": [
            "#berkeley", "#ucberkeley", "#research", "#science",
            "#innovation", "#discovery", "#academia", "#calbears",
        ],
    },
}


def feed_urls(account_key):
    return list(ACCOUNTS[account_key]["feed_urls"])
