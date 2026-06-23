// Extract a Substack session from the user's REAL Chrome profile by copying it
// to a temp dir and driving the copy.
//
// Why copy: Chrome REFUSES remote debugging on the default user-data-dir
// ("DevTools remote debugging requires a non-default data directory"), so
// Playwright cannot attach to the user's real profile directly. Copying the
// profile elsewhere makes it "non-default" → remote debugging allowed.
//
// Why ignoreDefaultArgs: Chrome v148 encrypts cookies with the macOS Keychain
// ("Chrome Safe Storage"). Playwright forces `--use-mock-keychain` (a fake
// keychain) which CANNOT decrypt the real-encrypted cookies → they'd be
// unreadable. We strip that flag so the copied Chrome uses the real Keychain
// (one authorization prompt → "Always Allow"). Decryption then happens inside
// Chrome; context.storageState() returns plaintext cookie values via CDP.
//
// PRECONDITION: user has logged into Substack in their normal Chrome AND fully
// quit Chrome (Cmd+Q) before running this.

import { chromium } from "/Users/chunsingyu/softwares/mcp-substack/node_modules/playwright/index.mjs";
import { cpSync, rmSync, existsSync, writeFileSync, readdirSync, statSync } from "node:fs";
import { homedir } from "node:os";

const REAL = `${homedir()}/Library/Application Support/Google/Chrome`;
const COPY = "/tmp/chrome-substack-extract";
const STATE_DIR = "/Users/chunsingyu/.config/mcp-substack";
const STORAGE_PATH = `${STATE_DIR}/storage-state.json`;
const META_PATH = `${STATE_DIR}/session-meta.json`;
const PROBE_URL = "https://substack.com/api/v1/subscriptions/page";
const POLL_INTERVAL_MS = 3000;
const DEFAULT_TIMEOUT_S = 120;

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

function dirSizeMb(dir) {
  let total = 0;
  const walk = (d) => {
    let entries;
    try { entries = readdirSync(d); } catch { return; }
    for (const e of entries) {
      const fp = `${d}/${e}`;
      let s;
      try { s = statSync(fp); } catch { continue; }
      if (s.isDirectory()) walk(fp);
      else total += s.size;
    }
  };
  walk(dir);
  return Math.round((total / (1024 * 1024)) * 10) / 10;
}

async function probe(context) {
  const page = await context.newPage();
  try {
    await page.goto("https://substack.com/", { waitUntil: "domcontentloaded" });
    const result = await page.evaluate(async (url) => {
      const r = await fetch(url, { credentials: "include", redirect: "follow" });
      return { status: r.status, url: r.url };
    }, PROBE_URL);
    return {
      authenticated: !isSignInUrl(result.url) && result.status < 400,
      status: result.status,
      url: result.url,
    };
  } finally {
    await page.close();
  }
}

async function main() {
  if (!existsSync(`${REAL}/Default`)) {
    log(`FATAL: real profile not found at ${REAL}/Default`);
    process.exit(1);
  }
  const timeoutS = Number(process.argv[2]) > 0 ? Number(process.argv[2]) : DEFAULT_TIMEOUT_S;

  log(`Copying ${REAL}/Default (+ Local State) → ${COPY} (skipping caches)…`);
  rmSync(COPY, { recursive: true, force: true });
  cpSync(`${REAL}/Local State`, `${COPY}/Local State`);
  // Copy Default but skip large cache/session dirs we don't need for cookies.
  const skip = /(^|\/)(Cache|Code Cache|GPUCache|GrShaderCache|GraphiteDawnCache|Service Worker|Sessions|Media Cache)(\/|$)/i;
  cpSync(`${REAL}/Default`, `${COPY}/Default`, { recursive: true, filter: (src) => !skip.test(src) });
  log(`Copy done (~${dirSizeMb(`${COPY}/Default`)} MB). Launching Chrome on the copy (real Keychain)…`);
  log(`>>> If a macOS Keychain prompt appears, click "Always Allow". <<<`);

  const context = await chromium.launchPersistentContext(COPY, {
    headless: false,
    channel: "chrome",
    ignoreDefaultArgs: ["--use-mock-keychain", "--password-store=basic"],
  });

  try {
    const deadline = Date.now() + timeoutS * 1000;
    let attempt = 0;
    let last = null;
    while (Date.now() <= deadline) {
      attempt += 1;
      try {
        last = await probe(context);
      } catch (err) {
        log(`probe #${attempt} error: ${err.message}`);
        await new Promise((r) => setTimeout(r, POLL_INTERVAL_MS));
        continue;
      }
      log(`probe #${attempt}: status ${last.status}, url ${last.url}, authenticated=${last.authenticated}`);
      if (last.authenticated) {
        const storageState = await context.storageState();
        const cookies = storageState.cookies.filter((c) => c.domain.includes("substack.com"));
        const origins = (storageState.origins || []).filter((o) => String(o.origin || "").includes("substack.com"));
        const empty = cookies.filter((c) => !c.value).length;
        writeFileSync(STORAGE_PATH, JSON.stringify({ cookies, origins }, null, 2));
        const now = new Date().toISOString();
        writeFileSync(META_PATH, JSON.stringify({
          savedAt: now,
          accountHint: null,
          statePath: STORAGE_PATH,
          lastValidatedAt: now,
          lastProbeAuthenticated: true,
          lastProbeReason: `status-${last.status}`,
        }, null, 2));
        log(`Wrote ${STORAGE_PATH} (${cookies.length} substack cookies; ${empty} empty-valued).`);
        log(`Wrote ${META_PATH}`);
        log(`DONE — authenticated session persisted.`);
        return;
      }
      await new Promise((r) => setTimeout(r, POLL_INTERVAL_MS));
    }
    log(`TIMEOUT after ${timeoutS}s — not authenticated (last status ${last?.status}, ${last?.url}).`);
    log(`Likely: (a) no Substack login in Default profile, or (b) Keychain decrypt failed.`);
    process.exitCode = 2;
  } finally {
    try { await context.close(); } catch {}
    log(`Cleaning up ${COPY}…`);
    rmSync(COPY, { recursive: true, force: true });
  }
}

main().catch((err) => {
  log(`FATAL: ${err.message}`);
  process.exit(1);
});
