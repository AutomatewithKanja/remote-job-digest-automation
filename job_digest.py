import requests
import sqlite3
import re
import os
from datetime import datetime

SLACK_WEBHOOK_URL = os.environ.get("SLACK_WEBHOOK_URL")

KEYWORDS = [
    "automation", "rpa", "workflow", "qa", "quality assurance",
    "data annotation", "data labeling", "ai training", "ai trainer",
    "prompt engineering", "transcription", "content moderation",
    "generalist", "remote contractor", "freelance"
]
KEYWORD_PATTERN = re.compile(
    r'\b(' + '|'.join(re.escape(k) for k in KEYWORDS) + r')\b',
    re.IGNORECASE
)


def send_slack_message(text):
    try:
        requests.post(SLACK_WEBHOOK_URL, json={"text": text}, timeout=10)
    except requests.RequestException as e:
        print(f"Failed to send Slack message: {e}")


def fetch_remoteok():
    try:
        r = requests.get("https://remoteok.com/api", timeout=10)
        r.raise_for_status()
        jobs = r.json()[1:]
        return [
            {
                "source": "RemoteOK",
                "id": f"remoteok-{j.get('id')}",
                "position": j.get("position", ""),
                "company": j.get("company", ""),
                "description": j.get("description", "") or "",
                "url": j.get("url", ""),
            }
            for j in jobs
        ]
    except (requests.RequestException, ValueError) as e:
        print(f"RemoteOK fetch failed: {e}")
        return []


def fetch_remotive():
    try:
        r = requests.get("https://remotive.com/api/remote-jobs", timeout=10)
        r.raise_for_status()
        jobs = r.json().get("jobs", [])
        return [
            {
                "source": "Remotive",
                "id": f"remotive-{j.get('id')}",
                "position": j.get("title", ""),
                "company": j.get("company_name", ""),
                "description": j.get("description", "") or "",
                "url": j.get("url", ""),
            }
            for j in jobs
        ]
    except (requests.RequestException, ValueError) as e:
        print(f"Remotive fetch failed: {e}")
        return []


def fetch_arbeitnow():
    try:
        r = requests.get("https://arbeitnow.com/api/job-board-api", timeout=10)
        r.raise_for_status()
        jobs = r.json().get("data", [])
        return [
            {
                "source": "Arbeitnow",
                "id": f"arbeitnow-{j.get('slug')}",
                "position": j.get("title", ""),
                "company": j.get("company_name", ""),
                "description": j.get("description", "") or "",
                "url": j.get("url", ""),
            }
            for j in jobs
        ]
    except (requests.RequestException, ValueError) as e:
        print(f"Arbeitnow fetch failed: {e}")
        return []


def main():
    all_jobs = fetch_remoteok() + fetch_remotive() + fetch_arbeitnow()

    if not all_jobs:
        print("All sources failed or returned nothing.")
        send_slack_message("⚠️ Job digest: all sources failed or returned nothing.")
        return

    matches = [
        j for j in all_jobs
        if KEYWORD_PATTERN.search(f"{j['position']} {j['description']}")
    ]

    try:
        conn = sqlite3.connect("seen_jobs.db")
        conn.execute("CREATE TABLE IF NOT EXISTS seen (id TEXT PRIMARY KEY)")

        new_jobs = []
        for job in matches:
            exists = conn.execute(
                "SELECT 1 FROM seen WHERE id=?", (job["id"],)
            ).fetchone()
            if not exists:
                new_jobs.append(job)
                conn.execute("INSERT INTO seen (id) VALUES (?)", (job["id"],))

        conn.commit()
        conn.close()
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        send_slack_message(f"⚠️ Job digest database error: {e}")
        return

    print(f"Fetched {len(all_jobs)} total jobs across all sources")
    print(f"Found {len(new_jobs)} NEW matching jobs")

    if new_jobs:
        lines = [
            f"• [{j['source']}] {j['position']} at {j['company']} — {j['url']}"
            for j in new_jobs
        ]
        text = (
            "*New job matches — " + datetime.now().strftime("%Y-%m-%d") + "*\n"
            + "\n".join(lines)
        )
        send_slack_message(text)
        print("Sent to Slack.")
    else:
        print("No new jobs — nothing sent.")


if __name__ == "__main__":
    main()