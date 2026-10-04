# Karachi Events Radar

A mobile-friendly events dashboard and a daily Python discovery agent for AI/ML, agents, sustainability, emerging technology and student events in Karachi or online.

[Open the dashboard](https://ahyaanlakhani.github.io/karachi-events/) · [Configure API secrets](https://github.com/ahyaanlakhani/karachi-events/settings/secrets/actions) · [Run or inspect the agent](https://github.com/ahyaanlakhani/karachi-events/actions/workflows/radar.yml)

**The included dashboard starts with clearly labelled fictional sample events.** They have no registration links. A successful collection replaces them with live data; failed runs preserve the previous dataset. Live collection needs API keys for useful coverage. No keys belong in browser code or Git.

## Preview locally

Requires Python 3.11 or later. From this project folder:

```sh
python -m http.server 8765 --bind 127.0.0.1 --directory docs
```

Open http://127.0.0.1:8765. The dashboard is static HTML, CSS and JavaScript: no Node build or database is needed. Light/dark preference is saved only on your device. Fonts have a local fallback if Google Fonts is unavailable.

## Set up daily cloud runs

1. Create a free account at [GitHub](https://github.com/signup) if needed. Create a **public** repository named `karachi-events`. Upload these project files, including `.github/workflows/`, with `main` as the default branch. Keep `.venv`, `.env`, caches and test artifacts out of Git.
2. Open [Google AI Studio](https://aistudio.google.com/apikey), sign in and create a Gemini API key for a project eligible for the free tier. Do not enable paid usage for this project if you want a strict free-only setup. Availability and quotas vary by model/account; confirm [Gemini pricing](https://ai.google.dev/gemini-api/docs/pricing). The default is `gemini-2.5-flash`; change `GEMINI_MODEL` under GitHub **Settings → Secrets and variables → Actions → Variables** if your account requires a different supported model.
3. Create a free account at [Tavily](https://app.tavily.com/) and copy your API key from its dashboard. Keep paid overages disabled. Tavily provides monthly **credits**, not an unconditional number of searches; see [pricing](https://www.tavily.com/pricing).
4. In your GitHub repository, open **Settings → Secrets and variables → Actions → New repository secret**. Add `GEMINI_API_KEY` and `TAVILY_API_KEY`. Paste each value only into its secret field. Optionally create a key at [Groq](https://console.groq.com/keys) and add `GROQ_API_KEY` for fallback extraction. Its model can be configured with the `GROQ_MODEL` repository variable.
5. Open **Settings → Pages → Build and deployment → Source** and select **GitHub Actions**. If your account or organization restricts workflow writes, allow the workflow to write repository contents; the agent commits only its data, status and credit count.
6. Open **Actions → Update and publish radar → Run workflow**, select `main`, leave **Collect fresh events** enabled, and run. On success, your dashboard is at `https://YOUR_USERNAME.github.io/karachi-events/`. A run with refresh disabled publishes the existing dataset, including the sample preview.

The schedule is **07:17 PKT daily** (`02:17 UTC`). It runs on GitHub's servers while your PC is off. Scheduled jobs can be delayed, and GitHub can disable public-repository schedules after 60 days without activity. Inspect Actions if updates stop. Successful data/status commits normally keep this repository active. See [scheduled workflows](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows#schedule).

GitHub Pages and standard hosted Actions runners support free use with public repositories, within their limits: [Pages](https://docs.github.com/en/pages/getting-started-with-github-pages/github-pages-limits), [Actions](https://docs.github.com/en/actions/concepts/billing-and-usage). The project is designed to stay within free tiers; it cannot guarantee provider quotas or future pricing. It never enables billing.

## Run the agent on your computer

```sh
python -m venv .venv
# Windows PowerShell:
.\.venv\Scripts\Activate.ps1
# macOS/Linux: source .venv/bin/activate
python -m pip install -r requirements.txt
```

Set `GEMINI_API_KEY` and `TAVILY_API_KEY` in your shell environment (plus optional `GROQ_API_KEY`), then:

```sh
python -m agent.radar
```

`.env.example` lists supported variables; the program intentionally does not automatically load `.env` files. Do not paste secrets into scripts, committed files, chat or screenshots. Without keys, the agent can read accessible JSON-LD event pages but web search and AI extraction are disabled.

For isolated experiments, supply `--output .artifacts/live --state-dir .artifacts/state`. Credit accounting in a separate state directory does not include production usage, so keep one state directory for actual runs using the same key. Use `--config path/to/config.json` to select a different configuration.

## What the agent does

1. Reads configured listing pages for Luma, Eventbrite, Meetup and GDG, discovers event links, and runs bounded Tavily basic searches for those sources, university societies, public LinkedIn/Facebook posts and online events. It respects robots.txt and never attempts a login or bypasses an access block.
2. Reads schema.org `Event` JSON-LD first. Otherwise, Gemini extracts facts with exact date evidence; Groq can act as a fallback. Unchanged extraction results are cached. The LLM has no tools and treats page text as untrusted data.
3. Rejects missing/invalid dates, cancelled/postponed events, past events, unrelated topics, physical events outside Karachi and explicitly restricted online events when identified by AI extraction. Online time-without-timezone records are rejected. A date with no time is displayed as **Time to be confirmed**. Online country eligibility is otherwise unknown; confirm it with the organizer.
4. Fetches the event's own page again. **Verified** means matching title, date and location in structured event data on that page. A reachable URL, LLM confidence or search snippet alone never earns this badge. Verification does not guarantee organizer legitimacy, remaining seats, online country eligibility or future cancellation status.
5. Merges strong same-day/time matches, preserves discovery dates, removes past events and atomically writes `docs/events.json`. Previously seen events not re-confirmed become unverified when retained during a successful partial collection. Failed collections leave the previous event file byte-for-byte unchanged and write a warning to `docs/status.json`; the dashboard hides expired events and shows failed/stale data notices.

Evidence scores are fixed rubric values, **not probabilities**: 90 = matching structured page evidence, 55 = reachable page without enough matching structured evidence, 25 = page unavailable or retained data. Every live record has a source link. Event-page buttons lead to the registration-capable source; no signup or payment is performed.

## Budgets and customization

Edit `agent/config.json`:

- `queries`: searches and the `{month}` placeholder; default eight queries per run.
- `listing_urls`: additional public listing pages. `event_urls`: event pages to check directly, useful for organizer or university pages missed by search.
- `monthly_search_credits`: default **300**, stored in `.state/usage.json` and committed by the workflow. A basic search reserves one credit **before** the request, including failed attempts. This only tracks this project's requests; provider usage elsewhere still counts toward your account limit.
- `max_pages_per_run`: 40 candidate pages; verification re-fetches are additional. `max_llm_calls_per_run`: 20 calls across both providers. Quota failures skip extraction or use the configured fallback.
- `horizon_days`: 120. PKT conversion uses `Asia/Karachi`.

The crawler does not render JavaScript. Some sites block automated access; indexed search snippets may still yield unverified records. Coverage is necessarily incomplete. The current month in a query is a discovery hint, not a guarantee that every future event will be found.

## Tests and demo data

```sh
python -m unittest discover -s tests -v
node --check docs/app.js
# Generate fresh fictional examples in an isolated directory:
python -m agent.demo --output .artifacts/demo
```

Tests cover time conversion, strict date handling, blocked URLs, duplicate merging, conservative verification, provider fallback, extraction caching, search budgets and last-good-data preservation. They use mocked providers and require no paid API calls.

To deliberately reset the dashboard to sample data, use `python -m agent.demo --output docs`. This overwrites the local public event file, so do not use it on a live dataset you want to keep.

## Files

- `agent/radar.py`: collection, extraction, verification, deduplication and publishing.
- `agent/config.json`: sources and budgets.
- `docs/`: public dashboard and public data only.
- `.github/workflows/radar.yml`: daily update, data commit and GitHub Pages deployment.
- `tests/test_radar.py`: offline reliability checks.

If collection fails, inspect `docs/status.json` and the **Collect and verify events** step. Check keys, model availability and quota first. If GitHub refuses the data commit, check branch protection and workflow write permissions. The workflow does not force-push or bypass branch protection. If deployment fails, confirm Pages uses GitHub Actions.
