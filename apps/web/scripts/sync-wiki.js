import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// 소스: 프로젝트 루트 docs/wiki
// 대상: apps/web/public/wiki
const sourceDir = path.resolve(__dirname, '../../../docs/wiki');
const targetDir = path.resolve(__dirname, '../public/wiki');

const IGNORE_PATTERNS = ['.obsidian', '.DS_Store'];

function ensureDirectoryExists(dir) {
  if (!fs.existsSync(dir)) {
    fs.mkdirSync(dir, { recursive: true });
  }
}

function cleanDirectory(dir) {
  if (fs.existsSync(dir)) {
    fs.rmSync(dir, { recursive: true, force: true });
  }
}

function buildTreeAndCopy(currentSource, currentTarget, relativePath = '') {
  const entries = fs.readdirSync(currentSource, { withFileTypes: true });
  const items = [];

  for (const entry of entries) {
    if (IGNORE_PATTERNS.includes(entry.name) || entry.name.startsWith('.')) {
      continue;
    }

    const srcPath = path.join(currentSource, entry.name);
    const destPath = path.join(currentTarget, entry.name);
    const relPath = relativePath ? `${relativePath}/${entry.name}` : entry.name;

    if (entry.isDirectory()) {
      ensureDirectoryExists(destPath);
      const children = buildTreeAndCopy(srcPath, destPath, relPath);
      items.push({
        type: 'directory',
        name: entry.name,
        path: relPath,
        children
      });
    } else if (entry.isFile()) {
      fs.copyFileSync(srcPath, destPath);
      items.push({
        type: 'file',
        name: entry.name,
        path: relPath,
        ext: path.extname(entry.name).toLowerCase()
      });
    }
  }

  // 디렉토리가 먼저 오고, 파일은 알파벳순으로 정렬 (대문.md, README.md 등은 상단 처리)
  items.sort((a, b) => {
    if (a.type !== b.type) {
      return a.type === 'directory' ? -1 : 1;
    }
    const topNames = ['대문.md', 'readme.md', 'index.md', '세계관 개요.md', '리그 체계 개요.md', '구단 목록.md', '경기 및 시즌 규정.md'];
    const aTopIndex = topNames.indexOf(a.name.toLowerCase());
    const bTopIndex = topNames.indexOf(b.name.toLowerCase());

    if (aTopIndex !== -1 && bTopIndex !== -1) return aTopIndex - bTopIndex;
    if (aTopIndex !== -1) return -1;
    if (bTopIndex !== -1) return 1;

    return a.name.localeCompare(b.name, undefined, { numeric: true, sensitivity: 'base' });
  });

  return items;
}

function syncWiki() {
  console.log('[sync-wiki] Syncing docs/wiki to apps/web/public/wiki...');
  
  if (!fs.existsSync(sourceDir)) {
    console.error(`[sync-wiki] Error: Source directory does not exist at ${sourceDir}`);
    process.exit(1);
  }

  cleanDirectory(targetDir);
  ensureDirectoryExists(targetDir);

  const tree = buildTreeAndCopy(sourceDir, targetDir);

  const manifestPath = path.join(targetDir, 'manifest.json');
  fs.writeFileSync(manifestPath, JSON.stringify({ tree, syncedAt: new Date().toISOString() }, null, 2));

  console.log('[sync-wiki] Successfully synced docs/wiki and generated manifest.json');
}

syncWiki();
