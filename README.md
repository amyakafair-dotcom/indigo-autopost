# Indigo Cosmetics — Instagram autopost

Publishes scheduled posts to @indigo__cosmetics through the official Instagram API (Instagram Login, no Facebook Page needed). Runs hourly on GitHub Actions; no computer needs to stay on.

## One-time setup

1. **Instagram account type.** Done: @indigo__cosmetics is a professional (business) account.
2. **Meta app.** App **Indigo Autopost** → Use cases → *Manage messaging & content on Instagram* → Customize → **API setup with Instagram login**.
   - Under *Generate access tokens*, click **Add account**, log in as @indigo__cosmetics and approve.
   - Click **Generate token** next to the account and copy it (valid 60 days).
3. **GitHub.** Settings → Secrets and variables → Actions → **New repository secret**: name `IG_TOKEN`, value the token from step 2. (`IG_USER_ID` is optional; it is looked up from the token.)
4. Test: Actions tab → *Indigo autopost* → **Run workflow**.
5. **Every ~60 days:** generate a new token (step 2) and update `IG_TOKEN`.

Facebook Page posting is supported too (`platforms` = `facebook`) but needs a Facebook Page token: set secret/env `IG_API_HOST=graph.facebook.com` and use a Page token in `IG_TOKEN`.

## Adding posts

Edit `posts.csv`, one row per post:

| column | value |
|---|---|
| `time` | publish time with offset, e.g. `2026-12-01T19:00:00+02:00` (Khartoum) |
| `type` | `IMAGE` or `REEL` |
| `media_url` | **public direct link** to a JPEG (image) or MP4 (reel) |
| `caption` | post text; wrap in quotes if it has commas |
| `platforms` | `instagram` (default when empty); `facebook` needs a Page token |
| `status` | leave empty — the bot fills in `instagram:<id> facebook:<id>` or `<platform>:ERROR ...` |

A failed platform is retried on the next run; platforms already posted are skipped. Never post a row twice by clearing a status that already has ids.

## Notes

- Media lives in `media/` and is linked by its raw.githubusercontent.com URL, so this repo must be public (secrets stay private). Instagram and Facebook fetch the file themselves.
- Images: JPEG only. Reels: MP4, 9:16, 3 s – 15 min.
- Posts land up to ~1 hour after `time` (hourly check).
- Instagram caps API publishing per 24 hours; normal brand schedules are far below it.
- On Facebook, `IMAGE` posts as a photo and `REEL` as a Page video.
- Carousels and stories are not supported yet.
