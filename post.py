"""Publish due rows from posts.csv to Instagram via the Graph API.

Env: IG_USER_ID, IG_TOKEN.
CSV columns: time (ISO 8601 with offset), type (IMAGE|REEL), media_url, caption, status.
Rows with empty status and time <= now get published; status becomes the post id or ERROR:<msg>.
"""
import csv
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone

API = "https://graph.facebook.com/v27.0"
CSV_PATH = "posts.csv"
USER = os.environ["IG_USER_ID"]
TOKEN = os.environ["IG_TOKEN"]


def call(method, path, **params):
    params["access_token"] = TOKEN
    data = urllib.parse.urlencode(params).encode()
    url = f"{API}/{path}"
    if method == "GET":
        url, data = f"{url}?{data.decode()}", None
    try:
        with urllib.request.urlopen(urllib.request.Request(url, data=data, method=method)) as r:
            return json.load(r)
    except urllib.error.HTTPError as e:
        raise RuntimeError(json.load(e).get("error", {}).get("message", str(e)))


def publish(row):
    if row["type"].upper() == "REEL":
        c = call("POST", f"{USER}/media", media_type="REELS", video_url=row["media_url"], caption=row["caption"])
        # Video needs processing before publish.
        for _ in range(60):
            status = call("GET", c["id"], fields="status_code")["status_code"]
            if status == "FINISHED":
                break
            if status == "ERROR":
                raise RuntimeError("video processing failed")
            time.sleep(10)
        else:
            raise RuntimeError("video processing timed out")
    else:
        c = call("POST", f"{USER}/media", image_url=row["media_url"], caption=row["caption"])
    return call("POST", f"{USER}/media_publish", creation_id=c["id"])["id"]


def main():
    with open(CSV_PATH, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        fields, rows = reader.fieldnames, list(reader)

    now = datetime.now(timezone.utc)
    failed = False
    for row in rows:
        if row["status"].strip() or datetime.fromisoformat(row["time"]) > now:
            continue
        try:
            row["status"] = publish(row)
            print(f"posted {row['time']} -> {row['status']}")
        except Exception as e:
            row["status"] = f"ERROR: {e}"
            print(f"failed {row['time']}: {e}", file=sys.stderr)
            failed = True

    with open(CSV_PATH, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
