#!/usr/bin/env node
/**
 * run-evals.mjs — golden before/after cases that exercise validate.mjs.
 *
 * This is the release gate for the CEO To-Do reliability guarantee. It runs the
 * bundled validator against each fixture and asserts the EXPECTED exit code:
 *   - every good fixture must exit 0
 *   - every bad fixture must exit non-zero (the invariant fired)
 *
 * "Now" is pinned to 2026-07-06 via CEO_TODO_TODAY so staleness math is
 * deterministic and does not drift as real time passes.
 *
 * Cases covered (map to the Reliability section):
 *   - no-loss             (dropped OPEN item vs a prior snapshot ⇒ fail)
 *   - stale-boundary      (7-day cutoff: 6d ok, 9d must be STALE)
 *   - user-added-protection (auto-closed [user-added] ⇒ fail)
 *   - dedup / duplicate-id (cross-channel dupe collapsed to one id; a real
 *                           duplicate id ⇒ fail)
 *   - idempotency         (validating the same good doc twice is identical)
 *
 * Usage:  node run-evals.mjs
 * Exit:   0 if every case met its expectation, 1 otherwise.
 */

import { spawnSync } from 'node:child_process';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const here = dirname(fileURLToPath(import.meta.url));
const VALIDATE = join(here, '..', 'validate.mjs');
const PINNED_TODAY = '2026-07-06';

function runValidate(args) {
  const res = spawnSync('node', [VALIDATE, ...args], {
    encoding: 'utf8',
    env: { ...process.env, CEO_TODO_TODAY: PINNED_TODAY },
  });
  return { code: res.status, out: (res.stdout || '') + (res.stderr || '') };
}

// Bad cases carry `match`: a substring the failure output MUST contain, so a
// validator that fails for the WRONG reason does not pass the suite.
const cases = [
  // ----- good fixtures: expect exit 0 -----
  { name: 'good-clean (valid doc)', args: ['good-clean.md'], expect: 0 },
  { name: 'good-dedup (cross-channel dupe kept once)', args: ['good-dedup.md'], expect: 0 },
  { name: 'good-alt-bullet (*, + and 1. markers are valid items, not skipped)', args: ['good-alt-bullet.md'], expect: 0 },
  {
    name: 'good no-loss (clean doc vs prior snapshot, nothing dropped)',
    args: ['good-clean.md', '--prev', 'good-prev-snapshot.md'],
    expect: 0,
  },
  {
    name: 'good park-to-NEEDS-REVIEW (moving a prior item to NEEDS-REVIEW is not a loss)',
    args: ['good-park-to-needs-review.md', '--prev', 'good-prev-snapshot.md'],
    expect: 0,
  },
  // ----- bad fixtures: expect non-zero AND the right violation -----
  { name: 'bad duplicate-id', args: ['bad-duplicate-id.md'], expect: 'nonzero', match: 'duplicate id' },
  {
    name: 'bad no-loss (prior OPEN item dropped)',
    args: ['bad-dropped-open.md', '--prev', 'good-prev-snapshot.md'],
    expect: 'nonzero',
    match: 'no-loss',
  },
  { name: 'bad stale-boundary (9d OPEN not marked STALE)', args: ['bad-stale-boundary.md'], expect: 'nonzero', match: 'STALE' },
  {
    name: 'bad user-added-protection (auto-closed [user-added])',
    args: ['bad-user-added-closed.md'],
    expect: 'nonzero',
    match: 'user-added',
  },
  {
    name: 'bad star-bullet-evasion (a * commitment that violates an invariant must be CAUGHT, not skipped)',
    args: ['bad-star-bullet-evasion.md'],
    expect: 'nonzero',
    match: 'STALE',
  },
  { name: 'bad waiting-no-reply-by', args: ['bad-waiting-no-replyby.md'], expect: 'nonzero', match: 'reply-by' },
  { name: 'bad missing-stamp', args: ['bad-missing-stamp.md'], expect: 'nonzero', match: 'last updated' },
  { name: 'bad malformed-line (commitment-shaped, does not parse)', args: ['bad-malformed-line.md'], expect: 'nonzero', match: 'canonical grammar' },
];

let failures = 0;
console.log(`Running ${cases.length} eval cases (today pinned to ${PINNED_TODAY})\n`);

for (const c of cases) {
  const { code, out } = runValidate(c.args.map((a) => (a.endsWith('.md') ? join(here, a) : a)));
  const codeOk = c.expect === 'nonzero' ? code !== 0 : code === c.expect;
  const matchOk = !c.match || out.includes(c.match);
  const pass = codeOk && matchOk;
  const tag = pass ? 'PASS' : 'FAIL';
  const want = c.expect === 'nonzero' ? 'non-zero' : String(c.expect);
  const wantMatch = c.match ? ` matching "${c.match}"` : '';
  console.log(`  [${tag}] ${c.name} — got exit ${code}, wanted ${want}${wantMatch}`);
  if (!pass) {
    failures++;
    if (!matchOk && codeOk) console.log(`        (exit code ok, but output did not contain "${c.match}")`);
    console.log('        ' + out.trim().split('\n').join('\n        '));
  }
}

// ----- idempotency: validating the same good doc twice is byte-identical -----
const r1 = runValidate([join(here, 'good-clean.md')]);
const r2 = runValidate([join(here, 'good-clean.md')]);
const idempotent = r1.code === 0 && r2.code === 0 && r1.out === r2.out;
console.log(`  [${idempotent ? 'PASS' : 'FAIL'}] idempotency (two runs on the same doc are identical)`);
if (!idempotent) failures++;

console.log('');
if (failures > 0) {
  console.error(`EVALS FAILED: ${failures} case(s) did not meet expectation.`);
  process.exit(1);
}
console.log(`All ${cases.length + 1} eval cases passed.`);
process.exit(0);
