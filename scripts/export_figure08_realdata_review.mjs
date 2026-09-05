#!/usr/bin/env node
import path from 'node:path';
import fs from 'node:fs';
import { execFileSync } from 'node:child_process';
import { fileURLToPath, pathToFileURL } from 'node:url';

const root = path.dirname(path.dirname(fileURLToPath(import.meta.url)));
const modules = process.env.NODE_MODULES || '/Users/zhangyuxi/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules';
const chrome = process.env.CHROME_PATH || '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome';
const dataRoot = process.env.MONITOR_DATA || '/Volumes/SN750-500GB/monitor_admin/analyzer/data';
const db = path.join(dataRoot, 'analyzer.db');
const photosRoot = path.join(dataRoot, 'photos');
const input = path.join(root, 'src/figures/08-photo-quality-review-realdata-4variants.html');
const outputDir = path.join(root, 'review/figures');
fs.mkdirSync(outputDir, { recursive: true });

const { chromium } = await import(pathToFileURL(path.join(modules, 'playwright/index.mjs')).href);

function sqlJson(sql) {
  const raw = execFileSync('sqlite3', ['-json', db, sql], { encoding: 'utf8' }).trim();
  return raw ? JSON.parse(raw) : [];
}
function one(sql) {
  return sqlJson(sql)[0];
}

const stats = one(`
WITH s AS (
  SELECT COUNT(*) AS candidates,
         SUM(confirm_status='confirmed_duplicate') AS duplicates,
         SUM(confirm_status='confirmed_different') AS different,
         SUM(confirm_status='pending') AS pending
  FROM similar_pair
), w AS (
  SELECT COUNT(*) AS workorders,
         COUNT(DISTINCT city) AS units,
         DATE(MIN(cre_time)) AS min_date,
         DATE(MAX(cre_time)) AS max_date
  FROM workorder
), f AS (
  SELECT COUNT(*) AS feedback FROM feedback_photo
)
SELECT f.feedback, s.candidates, s.duplicates, s.different, s.pending,
       (s.duplicates+s.different) AS reviewed,
       w.workorders, w.units, w.min_date, w.max_date,
       100.0*s.duplicates/(s.duplicates+s.different) AS review_dup_rate
FROM s,w,f;
`);

const buckets = sqlJson(`
SELECT CASE
         WHEN clip_similarity>=0.95 THEN '>=0.95'
         WHEN clip_similarity>=0.90 THEN '0.90-0.95'
         WHEN clip_similarity>=0.85 THEN '0.85-0.90'
         ELSE '0.80-0.85'
       END AS bucket,
       COUNT(*) AS n
FROM similar_pair
GROUP BY bucket;
`);
const bucketOrder = ['>=0.95','0.90-0.95','0.85-0.90','0.80-0.85'];
const bucketData = bucketOrder.map(bucket => ({ bucket, n: Number(buckets.find(x => x.bucket === bucket)?.n || 0) }));

const dup = one(`
SELECT s.clip_similarity*100.0 AS similarity,
       p1.photo_path AS photo1,
       p2.photo_path AS photo2
FROM similar_pair s
JOIN feedback_photo p1 ON p1.id=s.photo1_id
JOIN feedback_photo p2 ON p2.id=s.photo2_id
WHERE s.confirm_status='confirmed_duplicate'
  AND s.clip_similarity<0.999
ORDER BY s.clip_similarity DESC, s.phash_distance ASC
LIMIT 1;
`);
const diff = one(`
SELECT s.clip_similarity*100.0 AS similarity,
       p1.photo_path AS photo1,
       p2.photo_path AS photo2
FROM similar_pair s
JOIN feedback_photo p1 ON p1.id=s.photo1_id
JOIN feedback_photo p2 ON p2.id=s.photo2_id
WHERE s.confirm_status='confirmed_different'
ORDER BY s.clip_similarity DESC, s.phash_distance ASC
LIMIT 1;
`);

for (const rel of [dup.photo1, dup.photo2, diff.photo1, diff.photo2]) {
  const full = path.join(photosRoot, rel);
  if (!fs.existsSync(full)) throw new Error(`真实样本照片缺失: ${full}`);
}

const data = {
  feedback: Number(stats.feedback),
  candidates: Number(stats.candidates),
  reviewed: Number(stats.reviewed),
  duplicates: Number(stats.duplicates),
  different: Number(stats.different),
  pending: Number(stats.pending),
  workorders: Number(stats.workorders),
  units: Number(stats.units),
  dateRange: `${stats.min_date}—${stats.max_date}`,
  reviewDupRate: Number(stats.review_dup_rate),
  dupSimilarity: Number(dup.similarity),
  diffSimilarity: Number(diff.similarity),
  buckets: bucketData,
};
const images = {
  dupA: pathToFileURL(path.join(photosRoot, dup.photo1)).href,
  dupB: pathToFileURL(path.join(photosRoot, dup.photo2)).href,
  diffA: pathToFileURL(path.join(photosRoot, diff.photo1)).href,
  diffB: pathToFileURL(path.join(photosRoot, diff.photo2)).href,
};

const browser = await chromium.launch({
  headless: true,
  executablePath: chrome,
  args: ['--allow-file-access-from-files'],
});
const page = await browser.newPage({ viewport: { width: 1600, height: 720 }, deviceScaleFactor: 2 });
await page.goto(pathToFileURL(input).href, { waitUntil: 'load' });
await page.evaluate(({data, images}) => {
  window.applyRealData(data);
  window.setCaseImages(images);
}, { data, images });
await page.evaluate(async () => {
  await Promise.all([...document.images].map(img => img.complete ? Promise.resolve() : new Promise((resolve, reject) => {
    img.addEventListener('load', resolve, {once:true});
    img.addEventListener('error', reject, {once:true});
  })));
});

const outputs = [
  ['#fig08-a','08-照片质量督查-真实数据-方案A-Nature证据链.png'],
  ['#fig08-b','08-照片质量督查-真实数据-方案B-数据主导.png'],
  ['#fig08-c','08-照片质量督查-真实数据-方案C-人机分工.png'],
  ['#fig08-d','08-照片质量督查-真实数据-方案D-论文图版.png'],
];
for (const [selector, filename] of outputs) {
  const output = path.join(outputDir, filename);
  await page.locator(selector).screenshot({ path: output });
  console.log(`[figure08] exported ${output}`);
}
await browser.close();

console.log('[figure08] real-data summary');
console.log(JSON.stringify(data, null, 2));
