# Science Instagram Bot

Pulls recent research (Nature per-subject feeds for topic accounts; university
newsrooms for institution accounts), writes an original Instagram caption +
hashtags for each, saves review-ready drafts, and — once real accounts and API
tokens exist — publishes them via the Instagram Graph API behind a per-post
approval gate.

Runs on the Python standard library alone. `anthropic` is optional (better
captions). No `pip install` needed to generate drafts today.

## What works right now

```bash
# Generate drafts for one topic account
python3 -m src.pipeline draft --account neuronews --limit 3

# Generate drafts for ALL 11 topic accounts
python3 -m src.pipeline draft --all --limit 2

# Institution accounts (Caltech, Stanford, MIT, Harvard, Berkeley)
python3 -m src.pipeline --config institutions draft --all --limit 2

# List what you've drafted
python3 -m src.pipeline list
```

Each draft is written to `drafts/<account>/<date>_<n>.json` (machine-readable)
and `.md` (human preview: caption + hashtags, ready to copy-paste into
Instagram or a scheduler).

### The 11 topic accounts
`chemistrynews · biologynews · physicsnews · quantumnews · environmentalnews ·
spacenews · neuronews · medicinenews · ainews · psychnews · mathnews`

Each is mapped to a verified Nature subject RSS feed in
[`config/accounts.py`](config/accounts.py), with its own curated hashtag pool.
Add, remove, or retune feeds and hashtags there.

## Caption quality: two modes

- **Template (default, no setup):** builds a clean caption from the article
  title + abstract. Good enough to review and post manually.
- **LLM (recommended):** set `ANTHROPIC_API_KEY` and `pip install anthropic`.
  Claude then writes an original, paraphrased caption (model `claude-sonnet-5`).
  Never copies source text (copyright). The prompt enforces house writing rules
  (no em dashes, no marketing vocabulary, no manufactured hooks), and a
  deterministic guard strips any em/en dash that slips through.

Abstracts come from **Crossref** (open API, by DOI) for Nature articles, and
from the feed's own summary for institutional feeds. Nature article pages sit
behind a bot challenge, so we never scrape them directly.

## Publishing to Instagram — what you must set up

Instagram has **no simple "post this" API**. Auto-publishing requires, per
account:

1. Convert the account to an **Instagram Business or Creator** account.
2. Link it to a **Facebook Page** inside a Meta Business Suite portfolio.
3. Create a **Meta developer app** (developers.facebook.com) and add the
   *Instagram Graph API* product.
4. Get a **long-lived access token** with `instagram_content_publish`
   permission, and your account's **IG User ID**.
5. Complete Meta **App Review** for content publishing (required to post to
   accounts beyond your own test users).

Then provide credentials via environment variables (see `.env.example`):

```
IG_USER_ID__NEURONEWS=17841400000000000
IG_TOKEN__NEURONEWS=EAAG...long-lived-token...
```

Publish a drafted post (Instagram feed posts **require an image**, so you must
supply a publicly hosted `image_url`):

```bash
python3 -m src.pipeline publish \
  --account neuronews \
  --draft 2026-07-29_01_ultraslow-oscillations \
  --image-url https://your-cdn.example.com/cards/neuro-01.png \
  --confirm
```

**Safety gate:** [`src/publish.py`](src/publish.py) refuses to post unless
credentials exist **and** you pass `--confirm`. Without both it prints a dry
run of exactly what would be sent. This is deliberate — automated public
posting stays behind an explicit per-post approval.

> Because the 11 accounts don't exist yet, the publish step can't fire until
> you create them and add tokens. Everything else — fetch, summarize, caption,
> hashtags, drafts — works today, and the publish code is written and waiting.

## Institution accounts

[`config/institutions.py`](config/institutions.py) defines `researchatcaltech`,
`researchatstanford`, `researchatmit`, `researchatharvard`, `researchatberkeley`.
MIT/Harvard/Berkeley/Stanford use native newsroom RSS; Caltech (no public feed)
uses a Google News query. Add more schools by copying an entry. Google News
titles carry a " - Source" suffix that the LLM caption mode cleans up.

## Image cards

Every draft gets a post-ready 1080×1080 PNG (`drafts/<account>/<id>.png`) with a
per-account gradient, the account handle, the auto-sized title, and a source
footer — rendered by [`src/cards.py`](src/cards.py) (Pillow). Skip with
`--no-cards`.

## Image hosting (GitHub Pages)

The Graph API needs a *public* image URL, so cards are hosted on this repo's own
GitHub Pages by [`src/host.py`](src/host.py): it copies each card into
`docs/cards/<account>/`, writes the public `image_url` back into the draft JSON,
commits, pushes, and enables Pages.

**Config** (`.env`, auto-loaded):
```
GITHUB_USER=saanviiyer
GITHUB_PAGES_REPO=science-instagram-bot
```

**Run:** `python3 -m src.host` — needs `gh auth login` (or a git credential
helper) done once. Pages is served from `main` branch `/docs`.

URLs look like
`https://saanviiyer.github.io/science-instagram-bot/cards/<account>/<id>.png`.
The daily job runs this automatically. Note: this pushes the project to a
**public** repo (secrets in `.env` stay local — it's gitignored).

## Scheduling (installed)

A macOS LaunchAgent runs the drafts every day at **07:00**:

- Agent: `~/Library/LaunchAgents/com.saanvi.science-instagram.plist`
- Runner: [`run_daily.sh`](run_daily.sh) → `draft --all --limit 2`, logs to `drafts/_logs/`

```bash
# change the time: edit Hour/Minute in the plist, then reload
launchctl unload ~/Library/LaunchAgents/com.saanvi.science-instagram.plist
launchctl load  ~/Library/LaunchAgents/com.saanvi.science-instagram.plist

# run it right now to test
bash run_daily.sh

# stop it permanently
launchctl unload ~/Library/LaunchAgents/com.saanvi.science-instagram.plist
```

The Mac must be awake at 07:00; if asleep, launchd runs the job at next wake.
Uncomment the institutions line in `run_daily.sh` to draft those too.

## Copyright & safety notes

- Captions paraphrase; source text is never reproduced. Abstracts are used only
  as input to summarization, with attribution + link back to the source.
- Posting is gated per-post; nothing publishes without your explicit `--confirm`.
- Credentials live only in env vars, never in code or drafts.

## Files

| File | Purpose |
|------|---------|
| `config/accounts.py` | 11 topic accounts → Nature feeds + hashtags |
| `config/institutions.py` | University accounts → newsroom feeds |
| `src/feeds.py` | RSS fetch + Crossref abstracts (bot-challenge resilient) |
| `src/caption.py` | Caption + hashtag generation (template / LLM) |
| `src/publish.py` | Instagram Graph API publish (gated) |
| `src/pipeline.py` | CLI orchestrator |
| `drafts/` | Generated output |
# science-instagram-bot
