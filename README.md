# Remote Job Digest Automation

Automated daily job-scouting pipeline that fetches remote job listings from 
a public API, filters for relevant roles, deduplicates against previously 
seen postings, and delivers new matches to Slack — fully hosted on GitHub 
Actions with no dependency on a local machine.

## Problem

Manually checking job boards every day for relevant remote listings is slow 
and easy to forget. Most job alert tools are either paid, limited in 
filtering, or tied to a specific platform.

## Solution

A self-hosted, zero-cost pipeline that runs daily in the cloud, filters 
listings against custom keywords, tracks what's already been seen so 
nothing repeats, and pushes a clean digest straight to Slack.

## Workflow

1. **Fetch** — pulls live job listings from the RemoteOK public JSON API
2. **Filter** — matches listings against a configurable keyword list 
   (e.g. automation, AI training, data annotation, QA, RPA)
3. **Deduplicate** — checks each listing against a SQLite database of 
   previously seen job IDs; only genuinely new listings are reported
4. **Notify** — sends a formatted digest of new matches to a Slack channel 
   via an Incoming Webhook
5. **Schedule** — runs automatically once a day via a GitHub Actions cron 
   workflow, with a manual trigger also available

## Error handling

- Network/API failures, malformed responses, and database errors are all 
  caught individually
- On failure, a warning message is sent to Slack instead of failing silently, 
  so a broken run is never invisible

## Technical notes

- Chose a public JSON API over HTML scraping for reliability — scraping is 
  fragile against site redesigns, while the API returns stable structured data
- The SQLite "seen jobs" database is committed back to the repo after each 
  run (via the GitHub Actions workflow) so state persists across scheduled 
  runs without needing external storage
- Slack webhook URL is never hardcoded — it's read from an environment 
  variable, sourced from a GitHub Actions repository secret
- Initially set up with local Windows Task Scheduler, then migrated to 
  GitHub Actions so the automation runs independently of any local machine 
  being powered on or connected to the internet

## Tools used

Python, `requests`, SQLite, Slack Incoming Webhooks, GitHub Actions (cron + 
`workflow_dispatch`), Git

## Known limitations

- Keyword matching is substring-based, so it can occasionally produce a 
  false positive (e.g. a role matching on an unrelated use of "qa")
- Currently targets a single job source (RemoteOK); could be extended to 
  aggregate multiple APIs

## Future improvements

- Add stricter keyword matching (whole-word or regex-based) to reduce 
  false positives
- Support multiple job sources
- Add a simple digest archive (e.g. a markdown log) alongside Slack delivery

## Setup

1. Clone the repo
2. `pip install -r requirements.txt`
3. Set the `SLACK_WEBHOOK_URL` environment variable
4. Run `python job_digest.py`

For automated daily runs, fork the repo and add your own `SLACK_WEBHOOK_URL` 
as a GitHub Actions repository secret — the included workflow 
(`.github/workflows/job_digest.yml`) handles the rest.