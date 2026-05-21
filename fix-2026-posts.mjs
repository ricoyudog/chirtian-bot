#!/usr/bin/env node
/**
 * Batch repair script for broken 2026 Christian Substack posts.
 * Uses authenticated Playwright to re-fetch paid content and overwrite broken files.
 *
 * Usage:
 *   node fix-2026-posts.mjs [--month 2026-01] [--dry-run] [--force]
 *
 * Options:
 *   --month YYYY-MM   Only process a specific month (e.g. 2026-03)
 *   --dry-run         Show what would be fixed without writing
 *   --force           Re-fetch even posts that look OK (>20 lines)
 */

import { chromium } from 'playwright';
import { readFileSync, writeFileSync, readdirSync, statSync, mkdirSync, existsSync } from 'fs';
import { join, dirname } from 'path';

const VAULT_ROOT = '/Users/chunsingyu/softwares/christian-bot';
const CHRISTIAN_DIR = join(VAULT_ROOT, 'christian log');
const STATE_FILE = '/Users/chunsingyu/.config/mcp-substack/storage-state.json';
const SUBSTACK_URL = 'https://christian1hedge.substack.com';

// Parse CLI args
const args = process.argv.slice(2);
const monthFilter = args.includes('--month') ? args[args.indexOf('--month') + 1] : null;
const dryRun = args.includes('--dry-run');
const force = args.includes('--force');

const BROKEN_THRESHOLD = 20; // Files with <= this many lines are considered broken

function htmlToMarkdown(html) {
  if (!html) return '';
  let md = html;
  md = md.replace(/<h([1-6])[^>]*>([\s\S]*?)<\/h\1>/gi, (_, level, content) =>
    '\n' + '#'.repeat(parseInt(level)) + ' ' + content.trim() + '\n');
  md = md.replace(/<(strong|b)[^>]*>([\s\S]*?)<\/\1>/gi, '**$2**');
  md = md.replace(/<(em|i)[^>]*>([\s\S]*?)<\/\1>/gi, '*$2*');
  md = md.replace(/<a[^>]*href="([^"]*)"[^>]*>([\s\S]*?)<\/a>/gi, '[$2]($1)');
  md = md.replace(/<img[^>]*src="([^"]*)"[^>]*alt="([^"]*)"[^>]*\/?>/gi, '![$2]($1)');
  md = md.replace(/<img[^>]*src="([^"]*)"[^>]*\/?>/gi, '![]($1)');
  md = md.replace(/<blockquote[^>]*>([\s\S]*?)<\/blockquote>/gi, (_, c) =>
    '\n' + c.trim().split('\n').map(l => '> ' + l).join('\n') + '\n');
  md = md.replace(/<li[^>]*>([\s\S]*?)<\/li>/gi, '\n- $1');
  md = md.replace(/<hr\s*\/?>/gi, '\n---\n');
  md = md.replace(/<br\s*\/?>/gi, '\n');
  md = md.replace(/<\/p>/gi, '\n\n');
  md = md.replace(/<p[^>]*>/gi, '');
  md = md.replace(/<[^>]+>/g, '');
  md = md.replace(/&amp;/g, '&').replace(/&lt;/g, '<').replace(/&gt;/g, '>')
    .replace(/&quot;/g, '"').replace(/&#39;/g, "'").replace(/&nbsp;/g, ' ');
  md = md.replace(/\n{3,}/g, '\n\n');
  return md.trim();
}

function parseFrontmatter(content) {
  const match = content.match(/^---\n([\s\S]*?)\n---/);
  if (!match) return {};
  const fm = {};
  for (const line of match[1].split('\n')) {
    const m = line.match(/^(\w+):\s*(.*)$/);
    if (m) {
      let val = m[2].trim();
      if (val.startsWith('"') && val.endsWith('"')) val = val.slice(1, -1);
      if (val.startsWith('[') && val.endsWith(']')) {
        val = val.slice(1, -1).split(',').map(s => s.trim());
      }
      fm[m[1]] = val;
    }
  }
  return fm;
}

function collectFiles() {
  const files = [];
  function walk(dir) {
    for (const entry of readdirSync(dir, { withFileTypes: true })) {
      const full = join(dir, entry.name);
      if (entry.isDirectory()) {
        if (!monthFilter || full.includes(monthFilter)) walk(full);
      } else if (entry.name.endsWith('.md')) {
        files.push(full);
      }
    }
  }
  walk(CHRISTIAN_DIR);
  return files.filter(f => {
    // Only 2026 files
    const rel = f.replace(CHRISTIAN_DIR + '/', '');
    return rel.startsWith('2026-');
  });
}

function isBroken(filepath) {
  if (force) return true;
  const content = readFileSync(filepath, 'utf-8');
  const lines = content.split('\n').length;
  if (lines <= BROKEN_THRESHOLD) return true;

  // Also check for garbled content patterns
  const garbledPatterns = [
    /ChristianMay.*Paid/i,
    /∙ Paid/,
    /^\d+$/m,  // lines that are just numbers (like "2", "2")
  ];

  // Check if the body (after frontmatter) is mostly garbled
  const bodyMatch = content.match(/^---\n[\s\S]*?\n---\n([\s\S]*)$/);
  if (bodyMatch) {
    const body = bodyMatch[1].trim();
    // If body is very short and contains garbled patterns
    if (body.length < 100 && /Christian|Paid|Share/i.test(body)) return true;
    // If body only has image links with corrupted URLs
    if (/\$s_!/.test(body)) return true;
  }
  return false;
}

async function main() {
  console.log('=== Christian Substack 2026 Post Repair ===\n');
  if (monthFilter) console.log(`Filter: month = ${monthFilter}`);
  if (dryRun) console.log('DRY RUN - no files will be written');
  if (force) console.log('FORCE - re-fetching all posts');

  const allFiles = collectFiles();
  const brokenFiles = allFiles.filter(isBroken);
  console.log(`\nTotal 2026 files: ${allFiles.length}`);
  console.log(`Broken (≤${BROKEN_THRESHOLD} lines or garbled): ${brokenFiles.length}`);
  console.log(`OK (skipping): ${allFiles.length - brokenFiles.length}\n`);

  if (brokenFiles.length === 0) {
    console.log('Nothing to fix!');
    return;
  }

  // Extract source URLs
  const toFix = brokenFiles.map(f => {
    const content = readFileSync(f, 'utf-8');
    const fm = parseFrontmatter(content);
    const sourceUrl = fm.source;
    if (!sourceUrl) {
      console.warn(`  SKIP (no source URL): ${f}`);
      return null;
    }
    return { filepath: f, sourceUrl, title: fm.title, fm };
  }).filter(Boolean);

  console.log(`Posts to fix: ${toFix.length}\n`);

  // Launch browser
  console.log('Launching authenticated browser...');
  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext({
    storageState: STATE_FILE,
    userAgent: 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36'
  });
  const page = await context.newPage();

  // Establish session
  console.log('Establishing session...');
  await page.goto(SUBSTACK_URL, { waitUntil: 'networkidle', timeout: 30000 });
  await page.waitForTimeout(3000);
  console.log('Session established.\n');

  let fixed = 0, failed = 0, skipped = 0;

  for (let i = 0; i < toFix.length; i++) {
    const { filepath, sourceUrl, title, fm } = toFix[i];
    const relPath = filepath.replace(VAULT_ROOT + '/', '');
    process.stdout.write(`[${i + 1}/${toFix.length}] ${relPath}`);

    try {
      // Navigate to post page
      await page.goto(sourceUrl, { waitUntil: 'networkidle', timeout: 30000 });
      await page.waitForTimeout(1500);

      // Scrape body from DOM
      const bodyHtml = await page.evaluate(() => {
        const selectors = [
          'div.body.markup',
          'div.available-content',
          '.body.markup',
          '.available-content',
          'article .body',
          'div[class*="body"]'
        ];
        for (const sel of selectors) {
          const el = document.querySelector(sel);
          if (el && el.innerHTML.trim().length > 10) {
            return el.innerHTML;
          }
        }
        return null;
      });

      const bodyMd = htmlToMarkdown(bodyHtml || '');

      // Preserve original frontmatter, just update the body
      const frontmatter = readFileSync(filepath, 'utf-8').match(/^---\n[\s\S]*?\n---/)?.[0];
      if (!frontmatter) {
        console.log(' [SKIP: no frontmatter]');
        skipped++;
        continue;
      }

      const newContent = `${frontmatter}\n\n${bodyMd}\n\n---\n> Source: [${fm.title || title}](${sourceUrl})\n`;

      if (dryRun) {
        console.log(` [DRY-RUN: would write ${bodyMd.length} chars]`);
      } else {
        writeFileSync(filepath, newContent, 'utf-8');
        console.log(` [FIXED: ${bodyMd.length} chars]`);
      }
      fixed++;
    } catch (e) {
      console.log(` [ERROR: ${e.message}]`);
      failed++;
    }

    // Rate limit
    await page.waitForTimeout(1500);
  }

  console.log(`\n${'='.repeat(50)}`);
  console.log(`Done! Fixed: ${fixed}, Failed: ${failed}, Skipped: ${skipped}`);

  await browser.close();
}

main().catch(e => { console.error(e); process.exit(1); });
