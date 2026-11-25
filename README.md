# Indigo Cosmetics — Instagram + Facebook autopost

Publishes scheduled posts to @indigo__cosmetics and the Indigo Facebook Page through the official Meta Graph API. Runs hourly on GitHub Actions; no computer needs to stay on.

## One-time setup

1. **Instagram account type.** In the Instagram app: Settings → Account type and tools → switch to **Business** (or Creator). Link it to the Indigo Facebook Page.
2. **Meta app.** Done: app **Indigo Autopost** (Instagram API + Manage everything on your Page, with `pages_manage_posts`).
3. **Token (Page token, does not expire).** In Graph API Explorer (developers.facebook.com/tools/explorer):
   - Meta App: Indigo Autopost. Add permissions `instagram_basic`, `instagram_content_publish`, `pages_show_list`, `pages_read_engagement`, `pages_manage_posts`, `business_management`. Click **Generate Access Token** and approve.
   - Open the token in the Access Token Debugger (the ⓘ icon) → **Extend Access Token** → copy the long-lived token.
   - Back in Explorer, paste it and run `me/accounts?fields=name,access_token,instagram_business_account{id,username}`.
   - The Page `access_token` in that result is `IG_TOKEN` (used for both Instagram and the Facebook Page). A Page token made from a long-lived user token does not expire.
4. **Instagram user id.** From the same result, `instagram_business_account.id` for `indigo__cosmetics` is `IG_USER_ID`.
5. **GitHub.** Repo is ready. Go to Settings → Secrets and variables → Actions → add:
   - `IG_USER_ID` — the id from step 4
   - `IG_TOKEN` — the token from step 3
6. Test: Actions tab → *Indigo autopost* → **Run workflow**.

## Adding posts

Edit `posts.csv`, one row per post:

| column | value |
|---|---|
| `time` | publish time with offset, e.g. `2026-12-01T19:00:00+02:00` (Khartoum) |
| `type` | `IMAGE` or `REEL` |
| `media_url` | **public direct link** to a JPEG (image) or MP4 (reel) |
| `caption` | post text; wrap in quotes if it has commas |
| `platforms` | `instagram`, `facebook`, or `instagram,facebook`; empty = both |
| `status` | leave empty — the bot fills in `instagram:<id> facebook:<id>` or `<platform>:ERROR ...` |

A failed platform is retried on the next run; platforms already posted are skipped. Never post a row twice by clearing a status that already has ids.

## Notes

- Media lives in `media/` and is linked by its raw.githubusercontent.com URL, so this repo must be public (secrets stay private). Instagram and Facebook fetch the file themselves.
- Images: JPEG only. Reels: MP4, 9:16, 3 s – 15 min.
- Posts land up to ~1 hour after `time` (hourly check).
- Instagram caps API publishing per 24 hours; normal brand schedules are far below it.
- On Facebook, `IMAGE` posts as a photo and `REEL` as a Page video.
- Carousels and stories are not supported yet.
