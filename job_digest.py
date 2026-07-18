import requests
import sqlite3
from datetime import datetime

import os
SLACK_WEBHOOK_URL = os.environ.get("SLACK_WEBHOOK_URL")

def send_slack_message(text):
    try:
        requests.post(SLACK_WEBHOOK_URL, json={"text": text}, timeout=10)
    except requests.RequestException as e:
        print(f"Failed to send Slack message: {e}")

def main():
    # --- Fetch ---
    try:
        response = requests.get("https://remoteok.com/api", timeout=10)
        response.raise_for_status()  # raises an error for 4xx/5xx responses
        jobs = response.json()[1:]
    except requests.RequestException as e:
        print(f"Failed to fetch jobs: {e}")
        send_slack_message(f"⚠️ Job digest failed to fetch data: {e}")
        return
    except ValueError as e:
        print(f"Failed to parse response as JSON: {e}")
        send_slack_message(f"⚠️ Job digest got a bad response (not JSON): {e}")
        return

    # --- Filter ---
    keywords = ["automation", "ai training", "data annotation", "qa", "rpa"]
    matches = []
    for job in jobs:
        text = (job.get("position", "") + " " + job.get("description", "")).lower()
        if any(k in text for k in keywords):
            matches.append(job)

    # --- Deduplicate ---
    try:
        conn = sqlite3.connect("seen_jobs.db")
        conn.execute("CREATE TABLE IF NOT EXISTS seen (id TEXT PRIMARY KEY)")

        new_jobs = []
        for job in matches:
            job_id = str(job.get("id"))
            exists = conn.execute("SELECT 1 FROM seen WHERE id=?", (job_id,)).fetchone()
            if not exists:
                new_jobs.append(job)
                conn.execute("INSERT INTO seen (id) VALUES (?)", (job_id,))

        conn.commit()
        conn.close()
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        send_slack_message(f"⚠️ Job digest database error: {e}")
        return

    # --- Report ---
    print(f"Found {len(new_jobs)} NEW matching jobs")

    if new_jobs:
        text = "*New job matches — " + datetime.now().strftime("%Y-%m-%d") + "*\n" + "\n".join(
            f"• {j.get('position')} at {j.get('company')} — {j.get('url')}" for j in new_jobs
        )
        send_slack_message(text)
        print("Sent to Slack.")
    else:
        print("No new jobs — nothing sent.")

if __name__ == "__main__":
    main()