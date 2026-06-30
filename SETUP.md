# Christian Bot — Setup Guide

End-to-end deployment of the three-service Docker stack
(daemon + dashboard + bot). Follow sections 1–6 in order, then section 7
to start the stack.

---

## 1. Substack session (storage-state.json)

The daemon polls Substack via the `mcp-substack` Node.js MCP server, which
authenticates with a Playwright-saved browser session.

1. On a workstation with Node.js 20+ and Chromium installed:
   ```bash
   npx playwright install chromium
   node -e "
     const { chromium } = require('playwright');
     (async () => {
       const browser = await chromium.launch({ headless: false });
       const ctx = await browser.newContext();
       const page = await ctx.newPage();
       await page.goto('https://substack.com/sign-in');
       console.log('Log in, then press Enter here to save session.');
       process.stdin.once('data', async () => {
         await ctx.storageState({ path: 'storage-state.json' });
         await browser.close();
       });
     })();
   "
   ```
2. Copy the resulting `storage-state.json` to the host running Docker:
   ```bash
   scp storage-state.json operator@host:/path/to/christian-bot/
   ```
3. The file is bind-mounted **read-only** into the daemon container at
   `/app/storage-state.json`. To refresh cookies later, overwrite the host
   file — the daemon picks up the new session on the next poll without a
   restart. See **Substack session expiry** below for detection.

---

## 2. Webull auth (paper account)

The daemon trades against the **paper-trading** account only in MVP.

1. Open Webull → paper-trading account.
2. Copy the paper account id (an `ACC...` string) into
   `WEBULL_UAT_ACCOUNT_ID` in `.env`.
3. Webull credentials are read from the Webull CLI's own config inside the
   container. On first run:
   ```bash
   docker compose exec daemon webull login --paper
   ```
   The CLI persists the token to `~/.webull/` inside the container; for
   persistence across restarts, mount a host directory at
   `/root/.webull/` (left to operator preference).

---

## 3. Claude CLI auth (InstructionParser fallback)

Claude CLI is installed globally inside the image via npm. Authenticate
once per container:

```bash
docker compose exec daemon claude /login
```

This stores credentials in the container's home dir. The CLI is used by
`InstructionParser` for manual `python -m src.pipeline run` parses and as
a fallback for the cross-check parser. The automatic poll path uses the
DeepSeek-based `CrossCheckParser` (3 × V4 Flash) and does **not** need
Claude CLI at runtime.

---

## 4. DeepSeek API key

`CrossCheckParser` makes 3 parallel DeepSeek V4 Flash calls per post and
takes the 2/3 majority.

1. Sign up at https://platform.deepseek.com.
2. Create an API key.
3. Put it in `DEEPSEEK_API_KEY` in `.env`.
4. (Optional) Override the base URL with `DEEPSEEK_BASE_URL` if using a
   proxy.

---

## 5. Telegram bot token + chat id

The bot pushes pipeline/circuit-breaker/cross-check-disagreement alerts,
accepts `/stop`, and handles drill confirmations.

1. Talk to **@BotFather** → `/newbot` → copy the token into
   `TELEGRAM_BOT_TOKEN`.
2. Send any message to your new bot.
3. Visit `https://api.telegram.org/bot<TOKEN>/getUpdates` → copy the
   `chat.id` of your operator chat into `TELEGRAM_CHAT_ID`.
4. Generate the kill-switch secret:
   ```bash
   openssl rand -hex 32
   ```
   Put the hex string in `DASHBOARD_KILL_SWITCH_SECRET`.

---

## 6. Copy `.env.example` to `.env`

```bash
cp .env.example .env
$EDITOR .env        # fill in every [required] value
```

Also review `config.yaml` — set `runtime.mode` (`offline_replay`,
`shadow`, or `uat_confirm` for MVP) and `risk.symbol_whitelist`.

---

## 7. Start the stack

```bash
docker compose build
docker compose up -d
docker compose ps          # all three services should show (healthy) within 30s
```

Dashboard is bound to `127.0.0.1:8000` inside the Docker network only
(design decision #11 — never exposed publicly). To view it:

```bash
ssh -L 8000:127.0.0.1:8000 operator@host    # then open http://localhost:8000
```

---

## Substack session expiry detection (Task 5.9)

The daemon already has a **consecutive-failures circuit breaker** (Task 2.5,
N=5 → kill switch + alert). Task 5.9 adds a second trigger:

- **6 consecutive zero-post polls** (default `SUBSTACK_ZERO_POST_ALERT_THRESHOLD=6`)
  → silently-expired Substack cookie is the most likely cause.
- The daemon pushes a Telegram alert naming the zero-post streak and the
  suggested fix (re-run section 1 above to refresh `storage-state.json`).

Unlike the failure circuit breaker, the zero-post trigger does **not**
engage the kill switch — Christian may simply have not posted. The alert
lets the operator decide.

---

## Acceptance criteria (Task 5.11)

All four must hold for the change to ship:

| # | Criterion | How to verify |
|---|-----------|---------------|
| 1 | **3 services healthy ≤ 30s** after `docker compose up -d` | `time docker compose up -d`; then `docker compose ps` — daemon, dashboard, and bot all `(healthy)` within 30s. |
| 2 | **Kill switch engages ≤ 2 ticks** | `curl -X POST -H "X-Kill-Switch-Secret: $DASHBOARD_KILL_SWITCH_SECRET" http://localhost:8000/api/kill-switch`; verify `runtime/kill_switch.flag` exists before the daemon's next tick (next tick ≤ tick interval, so ≤ 2 ticks). |
| 3 | **Daemon crash auto-restart ≤ 10s** | `docker compose kill -s SIGKILL daemon`; `docker compose ps` — daemon restarts and reports `Up` within 10s, then `(healthy)` within 30s. |
| 4 | **Volume persistence across down+up** | `docker compose down && docker compose up -d`; verify `runtime/runs.jsonl` still contains prior history via `curl http://localhost:8000/api/runs`. |

### CI smoke check

```bash
docker compose -f docker-compose.yml -f docker-compose.test.yml build
docker compose -f docker-compose.yml -f docker-compose.test.yml up --abort-on-container-exit
```

All three services must reach `(healthy)` and the run must exit 0.

---

## Operations quick reference

| Action | Command |
|--------|---------|
| View logs | `docker compose logs -f daemon` |
| Stop stack (graceful) | `docker compose down` (waits up to 120s for daemon tick-abort) |
| Force stop | `docker compose kill` |
| Manual parse | `docker compose exec daemon python -m src.pipeline run` |
| Read latest run | `docker compose exec daemon jq '. | select(.run_id)' /app/runtime/runs.jsonl \| tail -50` |
| Refresh Substack cookies | Overwrite host `storage-state.json` — no restart needed |
