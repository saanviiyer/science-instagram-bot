# science-instagram-bot

This bot turns recent research into Instagram post drafts. It pulls new papers from Nature subject feeds (for topic accounts) and university newsrooms (for institution accounts). For each item it writes an original caption with hashtags and renders a carousel of image cards. It can publish through the Instagram Graph API, but only behind a per-post approval gate.

Drafting runs on the Python standard library. The `anthropic` package (better captions) and Pillow (image cards) are optional.

## How it works

1. `src/feeds.py` reads the RSS feeds. For Nature articles, it gets abstracts from Crossref (open API, by DOI). For institution feeds, it uses the feed's own summary. Nature article pages sit behind a bot challenge, so the bot never scrapes them.
2. `src/caption.py` writes the caption and picks hashtags.
   - Template mode (default) builds a caption from the title and abstract.
   - LLM mode (recommended) needs `ANTHROPIC_API_KEY` and `pip install anthropic`. Claude (`claude-sonnet-5`) writes an original, paraphrased caption. The prompt enforces house writing rules (no em dashes, no marketing words, no manufactured hooks). A deterministic guard also removes any em or en dash in the output. LLM mode also removes the " - Source" suffix from Google News titles.
3. `src/cards.py` renders 1080x1080 PNG carousel slides with Pillow: a title slide, a "What they found" slide, and a follow and source slide. Use `--no-cards` to skip them. Without Pillow, the bot skips cards.
4. Hashtags come in niche, mid, and broad tiers and rotate per post, so a new account can rank on smaller tags.
5. Drafts go to `drafts/<account>/<date>_<n>.json` (for the code) and `.md` (a preview of the caption and hashtags to copy into Instagram or a scheduler). Card images go next to them.

### Accounts

There are 11 topic accounts in `config/accounts.py`: chemistrynews, biologynews, physicsnews, quantumnews, environmentalnews, spacenews, neuronews, medicinenews, ainews, psychnews, and mathnews. Each maps to a verified Nature subject RSS feed and has its own hashtag pool. Edit that file to change feeds or hashtags.

`config/institutions.py` defines researchatcaltech, researchatstanford, researchatmit, researchatharvard, and researchatberkeley. MIT, Harvard, Berkeley, and Stanford use their newsroom RSS feeds. Caltech has no public feed, so it uses a Google News query. To add a school, copy an entry.

## Run it

```bash
git clone https://github.com/saanviiyer/science-instagram-bot
cd science-instagram-bot
pip install -r requirements.txt   # optional, for LLM captions
pip install pillow                # optional, for image cards

python3 -m src.pipeline draft --account neuronews --limit 3
python3 -m src.pipeline draft --all --limit 2
python3 -m src.pipeline --config institutions draft --all --limit 2
python3 -m src.pipeline list
```

`draft` also takes `--within-days` (default 21).

### Publishing

Instagram has no simple "post this" API. Each account needs this setup:

1. Convert it to an Instagram Business or Creator account.
2. Link it to a Facebook Page in a Meta Business Suite portfolio.
3. Create a Meta developer app and add the Instagram Graph API product.
4. Get a long-lived access token with the `instagram_content_publish` permission, and the account's IG User ID.
5. Complete Meta App Review for content publishing. You need it to post to accounts other than your own test users.

Instagram feed posts need a public image URL. `python3 -m src.host` copies each card into `docs/cards/<account>/`, writes the public `image_url` into the draft JSON, then commits, pushes, and turns on GitHub Pages (served from `main`, folder `/docs`). It needs `gh auth login` or a git credential helper. URLs look like `https://<GITHUB_USER>.github.io/<GITHUB_PAGES_REPO>/cards/<account>/<file>.png`. This step pushes the project to a public repo. Secrets in `.env` stay local because git ignores `.env`.

```bash
python3 -m src.pipeline publish --account neuronews --draft <draft-id> \
  --image-url https://<GITHUB_USER>.github.io/<GITHUB_PAGES_REPO>/cards/neuronews/<file>.png \
  --confirm

python3 -m src.pipeline post-due            # dry run
python3 -m src.pipeline post-due --confirm  # post
```

`post-due` checks each account's daily slot in `config/schedule.py`. After the slot passes, it posts the newest unposted draft for that account, once per day. It marks a draft as posted only after a real success, so nothing posts twice. A draft with two or more images posts as a carousel. A draft with one image posts as a single image.

### Approval gate

`src/publish.py` refuses to post unless the account has credentials and you pass `--confirm`. Without both, it prints a dry run of what it would send. `post-due` also accepts `AUTO_PUBLISH=1` in place of `--confirm`. This is a deliberate opt-in. Automated public posting stays behind explicit approval. The accounts do not exist yet, so nothing publishes until you create them and add tokens.

### Scheduling on macOS

The author runs two LaunchAgents. One drafts every day at 07:00 (`draft --all --limit 2`, then `src.host`). The other runs `post-due` every 30 minutes. The runner scripts and plists are local and not in this repo. macOS blocks launchd jobs from reading files in `~/Downloads`, `~/Documents`, and `~/Desktop`, and the job then fails with no message. Keep the project and the runner scripts outside those folders. The Mac must be awake at the scheduled time. If it is asleep, launchd runs the job at the next wake.

## Copyright and safety

- Captions paraphrase. The bot never reproduces source text. It uses abstracts only as input to the summary, and each post links back to the source with attribution.
- Every post needs approval. Nothing publishes without `--confirm` (or `AUTO_PUBLISH=1` for `post-due`).
- Credentials live only in environment variables, never in code or drafts.

## Environment variables

All are optional for drafting. The code loads `.env` on its own. See `.env.example`.

| Name | Purpose |
| ---- | ------- |
| `ANTHROPIC_API_KEY` | Turns on LLM captions. Template mode if unset. |
| `GITHUB_USER` | GitHub user that hosts the card images. Required for `src.host`. |
| `GITHUB_PAGES_REPO` | Repo for GitHub Pages (default `science-instagram-bot`) |
| `AUTO_PUBLISH` | Set to `1` to let `post-due` post without `--confirm` |
| `IG_USER_ID__<ACCOUNT>` | Instagram user ID for one account. Required to publish to it. |
| `IG_TOKEN__<ACCOUNT>` | Long-lived Graph API token for one account. Required to publish to it. |

`<ACCOUNT>` is the account key in upper case, with `-` changed to `_`. For example, `neuronews` uses `IG_USER_ID__NEURONEWS` and `IG_TOKEN__NEURONEWS`. Add one pair per account.

## Layout

| Path | Purpose |
| ---- | ------- |
| `config/accounts.py` | 11 topic accounts, their Nature feeds, and hashtag tiers |
| `config/institutions.py` | University accounts and newsroom feeds |
| `config/schedule.py` | Daily posting slot per account |
| `src/feeds.py` | RSS fetch and Crossref abstracts |
| `src/caption.py` | Caption and hashtag generation (template or LLM) |
| `src/cards.py` | Carousel image cards (Pillow) |
| `src/host.py` | Copies cards to GitHub Pages |
| `src/publish.py` | Instagram Graph API publish (gated) |
| `src/pipeline.py` | Command-line entry point |
| `docs/cards/` | Rendered card images that GitHub Pages serves |
| `drafts/` | Generated drafts. Not committed. |
