"""Publish due rows from posts.csv to Instagram (Instagram API with Instagram Login).

Env: IG_TOKEN (Instagram user token from the app's "API setup with Instagram login").
     IG_USER_ID optional (looked up from the token). IG_API_HOST optional:
     set to graph.facebook.com to use a Facebook Page token instead (needed for "facebook").
CSV columns: time (ISO 8601 with offset), type (IMAGE|REEL), media_url, caption, platforms, status.
platforms: "instagram", "facebook" or both (empty = instagram).
Due rows get published to each platform not yet in status; status records "platform:id" per success,
or "platform:ERROR <msg>" on failure (cleared and retried on the next run).
"""
import csv
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone

_raw = os.environ.get("IG_TOKEN", "")
# Tolerate stray quotes, spaces, newlines or words pasted around the token.
_m = re.search(r"[A-Za-z0-9_\-]{60,}", _raw)
TOKEN = _m.group(0) if _m else _raw.strip()
# Instagram-login tokens (IGAA...) use graph.instagram.com; Facebook-login tokens (EAA...) use graph.facebook.com.
HOST = os.environ.get("IG_API_HOST") or ("graph.facebook.com" if TOKEN.startswith("EAA") else "graph.instagram.com")
API = f"https://{HOST}/v23.0"
CSV_PATH = "posts.csv"
USER = os.environ.get("IG_USER_ID", "")


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


def publish_facebook(row):
    page = call("GET", "me", fields="id")["id"]
    if row["type"].upper() == "REEL":
        return call("POST", f"{page}/videos", file_url=row["media_url"], description=row["caption"])["id"]
    return call("POST", f"{page}/photos", url=row["media_url"], message=row["caption"])["id"]


def publish_instagram(row):
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


def check():
    """Print which Instagram account the token reaches; publishes nothing."""
    global USER
    if not TOKEN:
        sys.exit("IG_TOKEN secret is missing.")
    USER = USER or call("GET", "me", fields="user_id")["user_id"]
    info = call("GET", USER, fields="username,media_count")
    print(f"OK: token reaches @{info.get('username')} (id {USER}, {info.get('media_count')} posts) via {HOST}")


def main():
    with open(CSV_PATH, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        fields, rows = reader.fieldnames, list(reader)

    if "platforms" not in fields:
        fields.insert(fields.index("status"), "platforms")
    now = datetime.now(timezone.utc)
    publishers = {"instagram": publish_instagram, "facebook": publish_facebook}
    failed = False
    for row in rows:
        if datetime.fromisoformat(row["time"]) > now:
            continue
        wanted = [p.strip() for p in (row.get("platforms") or "instagram").split(",") if p.strip()]
        done = [s for s in (row["status"] or "").split()
                if s.split(":")[0] in publishers and not s.endswith(":ERROR")]
        todo = [p for p in wanted if not any(s.startswith(p + ":") for s in done)]
        if not todo:
            continue
        if not TOKEN:
            sys.exit("IG_TOKEN secret is missing; add it in repo Settings > Secrets.")
        global USER
        if not USER:
            if HOST == "graph.instagram.com":
                USER = call("GET", "me", fields="user_id")["user_id"]
            else:
                pages = call("GET", "me/accounts", fields="instagram_business_account")["data"]
                USER = next((p["instagram_business_account"]["id"] for p in pages if "instagram_business_account" in p), "")
                if not USER:
                    sys.exit("No Instagram account found for this token; set the IG_USER_ID secret.")
        errors = []
        for platform in todo:
            try:
                post_id = publishers[platform](row)
                done.append(f"{platform}:{post_id}")
                print(f"posted {row['time']} {platform} -> {post_id}")
            except Exception as e:
                errors.append(f"{platform}:ERROR {e}")
                print(f"failed {row['time']} {platform}: {e}", file=sys.stderr)
                failed = True
        row["status"] = " ".join(done + errors)

    with open(CSV_PATH, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    check() if os.environ.get("CHECK_ONLY") == "true" else main()
