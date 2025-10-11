import fs from 'fs';
import fsp from 'fs/promises';
import path from 'path';
import process from 'process';
import { chromium, request as pwRequest } from 'playwright';
import YAML from 'yaml';

type Target = {
  id: string;
  name: string;
  jurisdiction: string;
  use_cases?: string[];
  url: string;
};

type ManifestEntry = {
  id: string;
  name: string;
  jurisdiction: string;
  use_cases: string[];
  source_url: string;
  local_path: string;
  access: 'public';
  fetched_at: number;
};

const ROOT = '/Users/localuser/msa';
const TARGETS_PATH = path.join(ROOT, 'scripts/scrape/targets.yaml');
const MANIFEST_PATH = path.join(ROOT, 'templates/manifest.json');
const RAW_DIR = path.join(ROOT, 'templates/raw');

function slugify(value: string): string {
  return value
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/-+/g, '-')
    .replace(/^-|-$/g, '');
}

async function readTargets(targetsPath: string): Promise<Target[]> {
  const content = await fsp.readFile(targetsPath, 'utf-8');
  const data = YAML.parse(content);
  return Array.isArray(data) ? data : [];
}

async function readManifest(): Promise<ManifestEntry[]> {
  if (!fs.existsSync(MANIFEST_PATH)) return [];
  const text = await fsp.readFile(MANIFEST_PATH, 'utf-8');
  try { return JSON.parse(text); } catch { return []; }
}

async function writeManifest(entries: ManifestEntry[]): Promise<void> {
  await fsp.mkdir(path.dirname(MANIFEST_PATH), { recursive: true });
  await fsp.writeFile(MANIFEST_PATH, JSON.stringify(entries, null, 2));
}

function hasEntry(entries: ManifestEntry[], id: string): boolean {
  return entries.some(e => e.id === id);
}

function guessKind(url: string): 'pdf' | 'html' | 'bin' {
  const lower = url.toLowerCase();
  if (lower.endsWith('.pdf')) return 'pdf';
  if (lower.endsWith('.doc') || lower.endsWith('.docx') || lower.endsWith('.html') || lower.endsWith('.htm')) return 'html';
  return 'html';
}

async function fetchBinary(url: string): Promise<Buffer> {
  const context = await pwRequest.newContext();
  const resp = await context.get(url, { timeout: 120000 });
  if (!resp.ok()) throw new Error(`HTTP ${resp.status()} for ${url}`);
  const buf = Buffer.from(await resp.body());
  await context.dispose();
  return buf;
}

async function fetchHtmlWithBrowser(url: string): Promise<string> {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage();
  await page.goto(url, { waitUntil: 'networkidle', timeout: 120000 });
  await page.waitForTimeout(2500);
  const html = await page.content();
  await browser.close();
  return html;
}

async function saveFile(filePath: string, data: Buffer | string): Promise<void> {
  await fsp.mkdir(path.dirname(filePath), { recursive: true });
  if (typeof data === 'string') {
    await fsp.writeFile(filePath, data, 'utf-8');
  } else {
    await fsp.writeFile(filePath, data);
  }
}

function extractFormNumberFromId(targetId: string): string | null {
  const m = targetId.match(/fl-(\d{3})/i);
  return m ? `FL-${m[1]}` : null;
}

async function findCaliforniaPdfViaSearch(formNumber: string): Promise<string | null> {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage();
  const searchUrl = `https://www.courts.ca.gov/site-search.htm?keywords=${encodeURIComponent(formNumber)}`;
  await page.goto(searchUrl, { waitUntil: 'networkidle', timeout: 120000 });
  try {
    await page.waitForSelector('a[href$=".pdf"]', { timeout: 8000 });
  } catch {}
  const links = await page.$$eval('a[href$=".pdf"]', as => as.map(a => (a as HTMLAnchorElement).href));
  await browser.close();
  if (!links || links.length === 0) return null;
  const exact = links.find(u => new RegExp(formNumber, 'i').test(u));
  return exact || links[0];
}

function yyyymmRange(monthsBack: number): string[] {
  const out: string[] = [];
  const now = new Date();
  for (let i = 0; i < monthsBack; i++) {
    const d = new Date(now.getFullYear(), now.getMonth() - i, 1);
    const y = d.getFullYear();
    const m = String(d.getMonth() + 1).padStart(2, '0');
    out.push(`${y}-${m}`);
  }
  return out;
}

async function findCaliforniaPdfViaSitesDefault(formNumber: string): Promise<string | null> {
  const numMatch = formNumber.match(/FL-(\d{3})/i);
  if (!numMatch) return null;
  const num = numMatch[1];
  const candidates: string[] = [];
  for (const ym of yyyymmRange(36)) {
    candidates.push(`https://courts.ca.gov/sites/default/files/courts/default/${ym}/fl${num}.pdf`);
    candidates.push(`https://courts.ca.gov/sites/default/files/courts/default/${ym}/FL${num}.pdf`);
  }
  for (const url of candidates) {
    try {
      // Probe existence
      await fetchBinary(url);
      return url;
    } catch {}
  }
  return null;
}

async function harvestCaliforniaPdfsFromIndex(pages: string[], desired: string[], manifest: ManifestEntry[]): Promise<ManifestEntry[]> {
  const desiredSet = new Set(desired.map(d => d.toUpperCase()));
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage();
  const harvested: ManifestEntry[] = [];
  for (const url of pages) {
    try {
      await page.goto(url, { waitUntil: 'networkidle', timeout: 120000 });
      // Collect candidate links to detail pages that mention FL-xxx
      const detailLinks = await page.$$eval('a', as => as
        .filter(a => /FL-\d{3}/i.test(a.textContent || '') || /FL-\d{3}/i.test((a as HTMLAnchorElement).href))
        .map(a => (a as HTMLAnchorElement).href));
      const uniqueDetail = Array.from(new Set(detailLinks));
      for (const durl of uniqueDetail) {
        try {
          await page.goto(durl, { waitUntil: 'networkidle', timeout: 120000 });
          try { await page.waitForSelector('a[href$=".pdf"]', { timeout: 5000 }); } catch {}
          const pdfs = await page.$$eval('a[href$=".pdf"]', as => as.map(a => (a as HTMLAnchorElement).href));
          for (const href of pdfs) {
            const m = href.match(/fl-(\d{3})\.pdf/i);
            if (!m) continue;
            const formNum = `FL-${m[1]}`.toUpperCase();
            if (!desiredSet.has(formNum)) continue;
            if (manifest.some(e => e.jurisdiction === 'CA' && /fl-\d{3}\.pdf/i.test(e.source_url) && e.source_url.toLowerCase().includes(m[1]))) continue;
            try {
              const buf = await fetchBinary(href);
              const id = `ca-${formNum.toLowerCase()}`;
              const name = `California ${formNum}`;
              const baseName = `${id}-${slugify(name)}`;
              const outPath = path.join(RAW_DIR, `${baseName}.pdf`);
              await saveFile(outPath, buf);
              const entry: ManifestEntry = {
                id,
                name,
                jurisdiction: 'CA',
                use_cases: [],
                source_url: href,
                local_path: path.relative(ROOT, outPath),
                access: 'public',
                fetched_at: Math.floor(Date.now() / 1000)
              };
              harvested.push(entry);
              console.log(`Harvested CA form via detail: ${formNum}`);
            } catch (e) {
              console.log(`Harvest skip ${href}: ${String(e)}`);
            }
          }
        } catch (e) {
          // skip detail page errors
        }
      }
    } catch (e) {
      console.log(`Index page skip ${url}: ${String(e)}`);
    }
  }
  await browser.close();
  return harvested;
}

async function harvestTexasFormsFromGuides(guides: string[], manifest: ManifestEntry[]): Promise<ManifestEntry[]> {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage();
  const harvested: ManifestEntry[] = [];
  for (const url of guides) {
    try {
      await page.goto(url, { waitUntil: 'networkidle', timeout: 120000 });
      // Look for links to common downloadable formats
      const anchors = await page.$$eval('a', as => as.map(a => ({ href: (a as HTMLAnchorElement).href, text: (a.textContent||'').trim() })));
      const hrefs = anchors.map(a => a.href);
      const fileLinks = hrefs.filter(href => /\.(pdf|docx?|rtf)$/i.test(href));
      // Also follow internal resource/form pages to find files
      const internalPages = hrefs.filter(href => href.startsWith('https://texaslawhelp.org/') && (/resource\//i.test(href) || /form/i.test(href)));
      const unique = Array.from(new Set(fileLinks));
      for (const href of unique) {
        try {
          const buf = await fetchBinary(href);
          const id = `tx-${slugify(href.split('/').slice(-1)[0].replace(/\.[^.]+$/, ''))}`;
          const name = `TexasLawHelp Form ${href.split('/').slice(-1)[0]}`;
          const ext = href.toLowerCase().match(/\.(pdf|docx?|rtf)$/)?.[0] || '.bin';
          const outPath = path.join(RAW_DIR, `${id}-${slugify(name)}${ext}`);
          await saveFile(outPath, buf);
          const entry: ManifestEntry = {
            id,
            name,
            jurisdiction: 'TX',
            use_cases: [],
            source_url: href,
            local_path: path.relative(ROOT, outPath),
            access: 'public',
            fetched_at: Math.floor(Date.now() / 1000),
          };
          harvested.push(entry);
          console.log(`Harvested TX form: ${href}`);
        } catch (e) {
          console.log(`TX form skip ${href}: ${String(e)}`);
        }
      }
      // Crawl internal resource/form pages to find actual downloads
      const uniqPages = Array.from(new Set(internalPages));
      for (const purl of uniqPages) {
        try {
          await page.goto(purl, { waitUntil: 'networkidle', timeout: 120000 });
          const pageLinks = await page.$$eval('a', as => as.map(a => (a as HTMLAnchorElement).href));
          const downloads = Array.from(new Set(pageLinks.filter(h => /\.(pdf|docx?|rtf)$/i.test(h))));
          for (const dl of downloads) {
            try {
              const buf = await fetchBinary(dl);
              const id = `tx-${slugify(dl.split('/').slice(-1)[0].replace(/\.[^.]+$/, ''))}`;
              if (harvested.some(h => h.id === id)) continue;
              const name = `TexasLawHelp Form ${dl.split('/').slice(-1)[0]}`;
              const ext = dl.toLowerCase().match(/\.(pdf|docx?|rtf)$/)?.[0] || '.bin';
              const outPath = path.join(RAW_DIR, `${id}-${slugify(name)}${ext}`);
              await saveFile(outPath, buf);
              const entry: ManifestEntry = {
                id,
                name,
                jurisdiction: 'TX',
                use_cases: [],
                source_url: dl,
                local_path: path.relative(ROOT, outPath),
                access: 'public',
                fetched_at: Math.floor(Date.now() / 1000),
              };
              harvested.push(entry);
              console.log(`Harvested TX form via resource page: ${dl}`);
            } catch (e) {
              console.log(`TX resource file skip ${dl}: ${String(e)}`);
            }
          }
        } catch (e) {
          console.log(`TX resource page skip ${purl}: ${String(e)}`);
        }
      }
    } catch (e) {
      console.log(`TX guide skip ${url}: ${String(e)}`);
    }
  }
  await browser.close();
  return harvested;
}

async function crawlTexasLawHelp(startUrls: string[], manifest: ManifestEntry[], maxPages = 60, maxDepth = 3): Promise<ManifestEntry[]> {
  const seen = new Set<string>();
  type Q = { url: string; depth: number };
  const queue: Q[] = startUrls.map(u => ({ url: u, depth: 0 }));
  const harvested: ManifestEntry[] = [];
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage();

  const fileRegex = /\.(pdf|docx?|rtf)([#?].*)?$/i;
  const internalOk = (u: string) => u.startsWith('https://texaslawhelp.org/');
  const allowPath = (u: string) => /texaslawhelp\.org\/(guide|resource|form|topics)\//i.test(u) || u === 'https://texaslawhelp.org/' || /topics\/family-divorce-children/i.test(u);

  while (queue.length && seen.size < maxPages) {
    const { url, depth } = queue.shift() as Q;
    if (seen.has(url)) continue;
    seen.add(url);
    try {
      await page.goto(url, { waitUntil: 'networkidle', timeout: 120000 });
      const links: string[] = await page.$$eval('a', as => as.map(a => (a as HTMLAnchorElement).href));
      // Harvest files on this page
      const files = Array.from(new Set(links.filter(h => fileRegex.test(h))));
      for (const href of files) {
        try {
          const buf = await fetchBinary(href);
          const base = href.split('/').slice(-1)[0];
          const id = `tx-${slugify(base.replace(/\.[^.]+$/, ''))}`;
          if (harvested.some(h => h.id === id)) continue;
          const name = `TexasLawHelp Form ${base}`;
          const ext = (base.match(/\.[^.]+$/)?.[0] || '.bin').toLowerCase();
          const outPath = path.join(RAW_DIR, `${id}-${slugify(name)}${ext}`);
          await saveFile(outPath, buf);
          harvested.push({
            id,
            name,
            jurisdiction: 'TX',
            use_cases: [],
            source_url: href,
            local_path: path.relative(ROOT, outPath),
            access: 'public',
            fetched_at: Math.floor(Date.now() / 1000),
          });
          console.log(`Crawled TX form: ${href}`);
        } catch (e) {
          console.log(`Crawl file skip ${href}: ${String(e)}`);
        }
      }
      // Enqueue internal pages
      if (depth < maxDepth) {
        const nexts = Array.from(new Set(links.filter(h => internalOk(h) && allowPath(h))));
        for (const n of nexts) {
          if (!seen.has(n)) queue.push({ url: n, depth: depth + 1 });
        }
      }
    } catch (e) {
      console.log(`Crawl page skip ${url}: ${String(e)}`);
    }
  }
  await browser.close();
  return harvested;
}

async function main() {
  const args = process.argv.slice(2);
  let targetsPath = TARGETS_PATH;
  let statesFilter: Set<string> | null = new Set(['CA', 'FL', 'TX']);
  for (let i = 0; i < args.length; i++) {
    if (args[i] === '--targets' && args[i+1]) {
      targetsPath = path.resolve(args[i+1]);
      i++;
    } else if (args[i] === '--states' && args[i+1]) {
      statesFilter = new Set(args[i+1].split(',').map(s => s.trim().toUpperCase()));
      i++;
    } else if (args[i] === '--all') {
      statesFilter = null;
    }
  }

  const targets = await readTargets(targetsPath);
  let manifest = await readManifest();

  for (const t of targets) {
    if (statesFilter && !statesFilter.has((t.jurisdiction || '').toUpperCase())) continue;
    if (hasEntry(manifest, t.id)) continue;
    const kind = guessKind(t.url);
    const baseName = `${t.id}-${slugify(t.name)}`;
    let fileName = kind === 'pdf' ? `${baseName}.pdf` : `${baseName}.html`;
    let outPath = path.join(RAW_DIR, fileName);
    let finalSourceUrl = t.url;
    try {
      if (kind === 'pdf') {
        try {
          const buf = await fetchBinary(t.url);
          await saveFile(outPath, buf);
        } catch (err: any) {
          if ((t.jurisdiction || '').toUpperCase() === 'CA' && /HTTP 404/.test(String(err?.message))) {
            const formNumber = extractFormNumberFromId(t.id);
            if (formNumber) {
              const foundUrl = await findCaliforniaPdfViaSearch(formNumber);
              if (foundUrl) {
                const buf2 = await fetchBinary(foundUrl);
                fileName = `${baseName}.pdf`;
                outPath = path.join(RAW_DIR, fileName);
                await saveFile(outPath, buf2);
                finalSourceUrl = foundUrl;
              } else {
                const fallbackUrl = await findCaliforniaPdfViaSitesDefault(formNumber);
                if (fallbackUrl) {
                  const buf3 = await fetchBinary(fallbackUrl);
                  fileName = `${baseName}.pdf`;
                  outPath = path.join(RAW_DIR, fileName);
                  await saveFile(outPath, buf3);
                  finalSourceUrl = fallbackUrl;
                } else {
                  // will rely on index harvesting below
                  throw err;
                }
              }
            } else {
              throw err;
            }
          } else {
            throw err;
          }
        }
      } else {
        const html = await fetchHtmlWithBrowser(t.url);
        await saveFile(outPath, html);
      }
      const entry: ManifestEntry = {
        id: t.id,
        name: t.name,
        jurisdiction: t.jurisdiction,
        use_cases: t.use_cases || [],
        source_url: finalSourceUrl,
        local_path: path.relative(ROOT, outPath),
        access: 'public',
        fetched_at: Math.floor(Date.now() / 1000)
      };
      manifest.push(entry);
      console.log(`Fetched via Playwright: ${t.name}`);
    } catch (e: any) {
      console.log(`Playwright skip ${t.id}: ${e?.message || e}`);
    }
  }

  if (!statesFilter || statesFilter.has('CA')) {
    const indexPages = [
      'https://selfhelp.courts.ca.gov/find-forms/all',
      'https://selfhelp.courts.ca.gov/divorce-forms'
    ];
    const desired = ['FL-180','FL-342','FL-343','FL-345','FL-142','FL-160','FL-311','FL-341','FL-344','FL-355'];
    const harvested = await harvestCaliforniaPdfsFromIndex(indexPages, desired, manifest);
    if (harvested.length) {
      manifest = manifest.concat(harvested);
    }
  }

  if (!statesFilter || statesFilter.has('TX')) {
    const guides = [
      'https://texaslawhelp.org/guide/divorce-with-children-agreed',
      'https://texaslawhelp.org/guide/divorce-without-children-agreed'
    ];
    const txHarvested = await harvestTexasFormsFromGuides(guides, manifest);
    if (txHarvested.length) {
      manifest = manifest.concat(txHarvested);
    }
    // Broad crawl across TexasLawHelp to capture decree/packet files
    const seeds = [
      'https://texaslawhelp.org/',
      'https://texaslawhelp.org/topics/family-divorce-children',
      ...guides,
    ];
    const txCrawled = await crawlTexasLawHelp(seeds, manifest, 120, 4);
    if (txCrawled.length) {
      manifest = manifest.concat(txCrawled);
    }
  }

  await writeManifest(manifest);
  console.log(`Manifest updated: ${MANIFEST_PATH}`);
}

main().catch(err => {
  console.error(err);
  process.exit(1);
});


