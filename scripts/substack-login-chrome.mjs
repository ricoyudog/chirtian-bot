// Real-Google-Chrome Substack login → write mcp-substack storage-state.
//
// Why this exists: the mcp-substack MCP tool `substack_login_begin` launches
// Playwright's bundled Chromium and its `substack_login_save` only persists the
// browser context that *the same MCP server process* opened (pending sessions
// live in an in-memory Map). To log in via the real system Chrome we drive it
// ourselves with `channel: 'chrome'` and write the storage-state to the exact
// path mcp-substack reads (`~/.config/mcp-substack/storage-state.json`), so
// `substack_auth_status {refresh:true}` validates it via its HTTP probe.
//
// Mirrors: mcp-substack/lib/substack/client.mjs probeBrowserContext() + the
// storage-state / session-meta shape written by auth/login-manager.mjs saveLogin.
//
// Usage: node scripts/substack-login-chrome.mjs [timeoutSeconds=480]

import { chromium } from "/Users/chunsingyu/softwares/mcp-substack/node_modules/playwright/index.mjs";
import { writeFileSync } from "node:fs";

const STATE_DIR = "/Users/chunsingyu/.config/mcp-substack";
const STORAGE_PATH = `${STATE_DIR}/storage-state.json`;
const META_PATH = `${STATE_DIR}/session-meta.json`;
const PROBE_URL = "https://substack.com/api/v1/subscriptions/page";
const SIGN_IN_URL = "https://substack.com/sign-in";
const POLL_INTERVAL_MS = 4000;
const DEFAULT_TIMEOUT_S = 480;

function log(msg) {
  process.stdout.write(`[${new Date().toISOString()}] ${msg}\n`);
}

function isSignInUrl(url) {
  if (!url) return false;
  try {
    return new URL(url, "https://substack.com").pathname.includes("sign-in");
  } catch {
    return String(url).includes("sign-in");
  }
}

// In-browser probe — identical to mcp-substack probeBrowserContext (client.mjs).
async function probe(context) {
  const page = await context.newPage();
  try {
    await page.goto("https://substack.com/", { waitUntil: "domcontentloaded" });
    const result = await page.evaluate(async (url) => {
      const r = await fetch(url, { credentials: "include", redirect: "follow" });
      return { status: r.status, url: r.url };
    }, PROBE_URL);
    const redirectedToLogin = isSignInUrl(result.url);
    return {
      authenticated: !redirectedToLogin && result.status < 400,
      status: result.status,
      url: result.url,
    };
  } finally {
    await page.close();
  }
}

async function main() {
  const timeoutS = Number(process.argv[2]) > 0 ? Number(process.argv[2]) : DEFAULT_TIMEOUT_S;
  const deadline = Date.now() + timeoutS * 1000;

  log(`Launching real Google Chrome (channel: 'chrome')…`);
  const browser = await chromium.launch({ headless: false, channel: "chrome" });
  const context = await browser.newContext();
  const page = await context.newPage();
  await page.goto(SIGN_IN_URL, { waitUntil: "domcontentloaded" });
  log(`Opened ${SIGN_IN_URL}`);
  log(`Complete the magic-link login in Chrome (enter email → click the sign-in link in your inbox).`);
  log(`Polling every ${POLL_INTERVAL_MS / 1000}s for an authenticated session (max ${timeoutS}s)…`);

  try {
    let attempt = 0;
    // eslint-disable-next-line no-constant-condition
    while (true) {
      if (Date.now() > deadline) {
        log(`TIMEOUT: ${timeoutS}s reached without authenticated session. Browser left open — re-run if needed.`);
        await browser.close();
        process.exit(2);
      }
      await new Promise((r) => setTimeout(r, POLL_INTERVAL_MS));
      attempt += 1;
      let p;
      try {
        p = await probe(context);
      } catch (err) {
        log(`probe #${attempt} error: ${err.message}`);
        continue;
      }
      if (p.authenticated) {
        log(`probe #${attempt}: AUTHENTICATED (status ${p.status}, ${p.url})`);
        const storageState = await context.storageState();
        writeFileSync(STORAGE_PATH, JSON.stringify(storageState, null, 2));
        const now = new Date().toISOString();
        const meta = {
          savedAt: now,
          accountHint: null,
          statePath: STORAGE_PATH,
          lastValidatedAt: now,
          lastProbeAuthenticated: true,
          lastProbeReason: `status-${p.status}`,
        };
        writeFileSync(META_PATH, JSON.stringify(meta, null, 2));
        log(`Wrote ${STORAGE_PATH}`);
        log(`Wrote ${META_PATH}`);
        log(`DONE — authenticated session persisted.`);
        await browser.close();
        process.exit(0);
      }
      if (attempt % 5 === 1) {
        log(`probe #${attempt}: not yet (status ${p.status}, ${p.url}) — waiting for login…`);
      }
    }
  } catch (err) {
    log(`FATAL: ${err.message}`);
    try { await browser.close(); } catch {}
    process.exit(1);
  }
}

main();
