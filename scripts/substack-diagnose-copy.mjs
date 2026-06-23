// Diagnostic: open a fresh copy of the real Chrome profile, dump whether the
// Substack cookies actually DECRYPTED (non-empty values), and probe auth via
// /api/v1/subscriptions (401 vs 200). Writes storage-state if a non-empty
// session cookie is found. One-shot; cleaned up on exit.

import { chromium } from "/Users/chunsingyu/softwares/mcp-substack/node_modules/playwright/index.mjs";
import { cpSync, rmSync, writeFileSync } from "node:fs";
import { homedir } from "node:os";

const REAL = `${homedir()}/Library/Application Support/Google/Chrome`;
const COPY = "/tmp/chrome-substack-diag";
const STATE_DIR = "/Users/chunsingyu/.config/mcp-substack";
const STORAGE_PATH = `${STATE_DIR}/storage-state.json`;
const META_PATH = `${STATE_DIR}/session-meta.json`;
const SUBS_API = "https://substack.com/api/v1/subscriptions";

const log = (m) => process.stdout.write(`[${new Date().toISOString()}] ${m}\n`);

async function main() {
  log("Copying profile → /tmp/chrome-substack-diag …");
  rmSync(COPY, { recursive: true, force: true });
  cpSync(`${REAL}/Local State`, `${COPY}/Local State`);
  const skip = /(^|\/)(Cache|Code Cache|GPUCache|GrShaderCache|GraphiteDawnCache|Service Worker|Sessions|Media Cache)(\/|$)/i;
  cpSync(`${REAL}/Default`, `${COPY}/Default`, { recursive: true, filter: (s) => !skip.test(s) });
  log("Launch copy (real Keychain) — grant Keychain prompt if asked.");

  const context = await chromium.launchPersistentContext(COPY, {
    headless: false,
    channel: "chrome",
    ignoreDefaultArgs: ["--use-mock-keychain", "--password-store=basic"],
  });

  try {
    const page = await context.newPage();
    await page.goto("https://substack.com/", { waitUntil: "domcontentloaded" }).catch((e) => log("goto err: " + e.message));

    // 1) Dump cookie values (masked) to see if decryption worked.
    const cookies = await context.cookies("https://substack.com");
    log(`substack cookies via context.cookies(): ${cookies.length}`);
    let nonEmpty = 0;
    for (const c of cookies) {
      const valLen = c.value ? c.value.length : 0;
      if (valLen > 0) nonEmpty++;
      const preview = c.value ? c.value.slice(0, 6) + `…(${valLen})` : "<EMPTY>";
      log(`  ${c.name.padEnd(28)} ${c.domain.padEnd(20)} httpOnly=${c.httpOnly} val=${preview}`);
    }
    log(`non-empty cookies: ${nonEmpty}/${cookies.length}`);

    // 2) Probe /api/v1/subscriptions via in-page fetch (uses decrypted cookies).
    const probe = await page.evaluate(async (url) => {
      try {
        const r = await fetch(url, { credentials: "include", redirect: "follow" });
        return { status: r.status, url: r.url, ok: r.ok };
      } catch (e) { return { status: -1, url, error: e.message }; }
    }, SUBS_API);
    log(`/api/v1/subscriptions → status ${probe.status} url ${probe.url}`);

    // 3) If we have a non-empty session-ish cookie, persist regardless of probe
    //    (storage-state holds plaintext; auth_status will re-probe).
    const session = cookies.find((c) => c.value && /sid|session|connect|substack/i.test(c.name));
    if (session || nonEmpty > 0) {
      const allCookies = (await context.storageState()).cookies.filter((c) => c.domain.includes("substack.com"));
      const origins = (await context.storageState()).origins.filter((o) => String(o.origin).includes("substack.com"));
      writeFileSync(STORAGE_PATH, JSON.stringify({ cookies: allCookies, origins }, null, 2));
      const now = new Date().toISOString();
      writeFileSync(META_PATH, JSON.stringify({
        savedAt: now, accountHint: null, statePath: STORAGE_PATH,
        lastValidatedAt: now, lastProbeAuthenticated: probe.status === 200,
        lastProbeReason: `status-${probe.status}`,
      }, null, 2));
      log(`WROTE storage-state (${allCookies.length} cookies). session cookie: ${session ? session.name : "(none by name, but non-empty values exist)"}`);
    } else {
      log("NO non-empty cookies → decryption FAILED (Keychain/app-bound). storage-state NOT written.");
    }
  } finally {
    try { await context.close(); } catch {}
    rmSync(COPY, { recursive: true, force: true });
  }
}

main().catch((e) => { log("FATAL: " + e.message); process.exit(1); });
