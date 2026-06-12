import { NextResponse } from "next/server";
import fs from "fs";
import path from "path";

function findArtifactsDirectory(): string | null {
  const pathsToTry = [
    path.join(process.cwd(), /*turbopackIgnore: true*/ "artifacts"),
    path.join(process.cwd(), /*turbopackIgnore: true*/ "../artifacts"),
    path.join(process.cwd(), /*turbopackIgnore: true*/ "06-lab-complete/artifacts"),
    path.join("/var/task", /*turbopackIgnore: true*/ "artifacts"),
    path.join("/var/task", /*turbopackIgnore: true*/ "06-lab-complete/artifacts"),
  ];

  for (const p of pathsToTry) {
    if (fs.existsSync(p) && fs.lstatSync(p).isDirectory()) {
      return p;
    }
  }
  return null;
}

export async function GET() {
  const artifactsDir = findArtifactsDirectory();
  if (!artifactsDir) {
    console.error("Artifacts directory not found in paths.");
    return NextResponse.json(
      { headers: [], rows: [] }
    );
  }

  const csvPath = path.join(artifactsDir, "version_log.csv");
  if (!fs.existsSync(csvPath)) {
    return NextResponse.json(
      { headers: [], rows: [] }
    );
  }

  try {
    const content = fs.readFileSync(csvPath, "utf-8");
    const lines = content.split(/\r?\n/).filter(line => line.trim() !== "");
    if (lines.length === 0) {
      return NextResponse.json({ headers: [], rows: [] });
    }

    // Parse simple CSV (comma-separated, trim values)
    const headers = lines[0].split(",").map(h => h.trim());
    const rows: Record<string, string>[] = [];

    for (let i = 1; i < lines.length; i++) {
      const rowValues = lines[i].split(",").map(v => v.trim());
      const rowDict: Record<string, string> = {};
      headers.forEach((h, idx) => {
        rowDict[h] = rowValues[idx] || "";
      });
      rows.push(rowDict);
    }

    return NextResponse.json({ headers, rows });
  } catch (error: any) {
    console.error("Failed to read/parse version log CSV:", error);
    return NextResponse.json(
      { headers: [], rows: [] }
    );
  }
}
