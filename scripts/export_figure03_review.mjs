#!/usr/bin/env node
import path from 'node:path';
import fs from 'node:fs';
import { fileURLToPath, pathToFileURL } from 'node:url';

const root = path.dirname(path.dirname(fileURLToPath(import.meta.url)));
const modules = process.env.NODE_MODULES || '/Users/zhangyuxi/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules';
const chrome = process.env.CHROME_PATH || '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome';
const { chromium } = await import(pathToFileURL(path.join(modules, 'playwright/index.mjs')).href);

const input = path.join(root, 'src/figures/03-management-efficiency-quality-model.html');
const outputDir = path.join(root, 'review/figures');
const output = path.join(outputDir, '03-增效提质总体模型.png');
const distOutputDir = path.join(root, 'dist/figures');
const distOutput = path.join(distOutputDir, '03-增效提质总体模型.png');
fs.mkdirSync(outputDir, { recursive: true });
fs.mkdirSync(distOutputDir, { recursive: true });

const browser = await chromium.launch({ headless: true, executablePath: chrome });
const page = await browser.newPage({ viewport: { width: 1664, height: 936 }, deviceScaleFactor: 2 });
await page.goto(pathToFileURL(input).href, { waitUntil: 'load' });
await page.locator('#figure03').screenshot({ path: output });
fs.copyFileSync(output, distOutput);
await browser.close();
console.log(`[figure03] exported ${output}`);
console.log(`[figure03] synced ${distOutput}`);
