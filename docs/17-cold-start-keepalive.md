# Streamlit Cloud Cold Start — Plan & Mitigations

> Date: 2026-05-02. Written during the ANU AI Buildathon while the demo was live at <https://litbridge.streamlit.app/>.

## The problem

Streamlit Community Cloud free tier puts idle apps to sleep. When a judge / reviewer visits the URL after a quiet period, they hit a **30–60 s cold start**:

1. Container spin-up (~10–15 s)
2. `pip install` from cache (~5–10 s)
3. `sentence-transformers/all-MiniLM-L6-v2` load (~80 MB, ~5–10 s if not cached locally)
4. First-request `@st.cache_resource` warm-up (~1–2 s)

If we don't know when judges will look, we can't manually pre-warm.

---

## Options ranked (cheap → expensive)

### A. GitHub Actions cron pinger (chosen)
- **Cost**: $0 (public repo = unlimited Actions minutes)
- **Effort**: ~10 min one-time
- **Reliability**: 60–80% — Streamlit Cloud may fingerprint synthetic HTTP traffic, but in practice the sleep timer does reset on most pings
- **What we did**: see [Implementation](#what-we-actually-did) below

### B. Playwright cron (more reliable)
- **Cost**: $0
- **Effort**: 30–60 min (more YAML + npm install in CI)
- **Reliability**: ≥95% — opens a real headless Chromium session, Streamlit sees a websocket handshake
- **When to use**: when curl-based pings stop working / Streamlit tightens detection

### C. Third-party uptime monitors (UptimeRobot / cron-job.org / Pingdom)
- **Cost**: $0 free tier
- **Effort**: 5 min sign-up
- **Reliability**: same as A (HTTP-only)
- **Pro**: no repo changes
- **Con**: yet another account / dashboard

### D. Move to a non-sleeping host
| Platform | Price | Sleeps? | Notes |
|---|---|---|---|
| Hetzner CX22 VPS | €4.51 / mo (~$5) | No (you control) | Best $/value, but needs Linux ops |
| Railway Hobby | $5 / mo + usage | No | Easy deploy, decent free credits |
| Render Starter | $7 / mo | No | 512 MB RAM may be tight for sentence-transformers |
| Fly.io | $5–10 / mo (auto-stop off) | No | Needs Dockerfile |
| HuggingFace Spaces (free) | $0 | After 48 h | More forgiving than Streamlit Cloud |
| HF Spaces Pro CPU upgrade | ~$36 / mo | No | Overpriced |
| Streamlit in Snowflake | Snowflake credits, hourly | No | Enterprise pricing — bad fit for personal demos |

### E. Streamlit Community Cloud paid tier
- As of 2026-01: **no self-serve always-on personal tier** that I'm aware of. Streamlit pushes "always-on" use cases to Snowflake. Verify on <https://streamlit.io/cloud> before assuming this exists.

### F. Reduce cold start time itself
- Bundle the embedder model in the repo (~80 MB) — eliminates one phase but adds Git LFS / size pain
- Container boot itself can't be skipped on free tier
- Even after this, expect ~15 s wake time

---

## What we actually did

### File: `.github/workflows/keepalive.yml`

```yaml
name: Keep Alive

on:
  schedule:
    - cron: '*/5 * * * *'   # GitHub may delay scheduled runs 5–15 min
  workflow_dispatch: {}

jobs:
  ping:
    runs-on: ubuntu-latest
    timeout-minutes: 2
    steps:
      - name: Ping LitBridge root (no redirect follow — Streamlit auth loops on -L)
        run: |
          curl -sS -o /dev/null \
            -w "ROOT  HTTP %{http_code} · %{time_total}s · %{url_effective}\n" \
            -A "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36" \
            -H "Accept: text/html,application/xhtml+xml" \
            --max-time 30 \
            https://litbridge.streamlit.app/ || true

      - name: Ping health endpoint (belt-and-suspenders)
        run: |
          curl -sS -o /dev/null \
            -w "HEALTH HTTP %{http_code} · %{time_total}s\n" \
            --max-time 10 \
            https://litbridge.streamlit.app/_stcore/health || true
```

### Verify / monitor / disable

- Live workflow: <https://github.com/xingkongliang/litbridge/actions/workflows/keepalive.yml>
- Manual trigger: `gh workflow run "Keep Alive" --repo xingkongliang/litbridge`
- Recent runs: `gh run list --repo xingkongliang/litbridge --workflow=keepalive.yml --limit 5`
- **Disable after the demo**: Actions tab → Keep Alive workflow → ⋯ menu → Disable workflow

A successful ping looks like:
```
ROOT  HTTP 303 · 0.43s · https://litbridge.streamlit.app/
HEALTH HTTP 303 · 0.34s
```

The 303 is Streamlit Cloud's auth gate — it means the app is alive and responding. Don't be alarmed by the non-200.

---

## Lessons learned

1. **`curl -L` against Streamlit Cloud loops forever** — Streamlit auth redirect chain doesn't terminate without browser-side cookies. Drop `-L`, accept the 303 as success.
2. **`/_stcore/health` is uncached and cheap** but hitting only this endpoint may not count as "user traffic" — Streamlit's sleep detector watches for actual page hits. Belt-and-suspenders: ping both root and health.
3. **GitHub Actions cron lag**: scheduled jobs are best-effort and can be delayed 5–15 min during peak load. A 5-min cron in practice fires every 7–12 min.
4. **The minimum cron interval is `*/5`** — GitHub rejects sub-5-min schedules.
5. **Public repos = unlimited Actions minutes.** Private repos get 2,000 min/mo on free tier — at 5-min intervals that's ~7 days of continuous pinging before you blow the quota.

---

## Belt-and-suspenders for the demo day

For a **specific judging window** when timing matters:

1. **Cron pinger** running (this doc)
2. **Keep a browser tab open** on the deployed app — your active websocket is the strongest signal that the app is live; Streamlit treats any active session as "in use"
3. **Local backup**: have `streamlit run app.py` ready on your laptop with `ngrok http 8501` in a second terminal. If Cloud genuinely fails, switch the demo URL to the ngrok one in 30 s.

---

## Related

- The deployed app: <https://litbridge.streamlit.app/>
- Repo: <https://github.com/xingkongliang/litbridge>
- Streamlit Cloud sleep policy is undocumented; community discussion: search "Streamlit Community Cloud sleep" on the Streamlit forum for current behavior.
