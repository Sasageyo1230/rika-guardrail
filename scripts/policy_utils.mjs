import fs from "node:fs";
import path from "node:path";
import child_process from "node:child_process";

export function diffStats() {
  // Count any added non-text files as binaries by extension heuristic.
  const changed = child_process.execSync('git diff --name-status origin/main...HEAD', {encoding:'utf8'}).trim().split(/\r?\n/).filter(Boolean);
  const binExt = new Set([".exe",".dll",".so",".dylib",".bin",".o",".a",".pdf",".zip",".7z",".jar",".png",".jpg",".jpeg",".gif",".webp"]);
  let addedBinaries = 0;
  for (const line of changed) {
    const [status, file] = line.split(/\s+/, 2);
    if (status?.startsWith("A")) {
      const ext = path.extname(file).toLowerCase();
      if (binExt.has(ext)) addedBinaries++;
    }
  }
  return { added_binaries: addedBinaries };
}

export function depList() {
  // Very simple: read package.json in root if present
  try {
    const pkg = JSON.parse(fs.readFileSync("package.json","utf8"));
    const deps = Object.entries({...pkg.dependencies, ...pkg.devDependencies}).map(([name,_]) => ({name, registry:"npm"}));
    return deps;
  } catch { return []; }
}

export function secretScan() {
  // Basic regexes; real scanner runs separately (trufflehog). This is belt-and-suspenders.
  const diff = child_process.execSync("git diff -U0 origin/main...HEAD", {encoding:"utf8"});
  const patterns = [
    /sk-[a-zA-Z0-9]{20,}/g,               // API-like tokens
    /AKIA[0-9A-Z]{16}/g,                  // AWS Access Key
    /AIza[0-9A-Za-z-_]{35}/g,             // Google API keys, generic format
    /-----BEGIN (?:RSA|EC) PRIVATE KEY-----/g
  ];
  return patterns.some(rx => rx.test(diff));
}
