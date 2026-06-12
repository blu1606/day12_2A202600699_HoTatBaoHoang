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
      { error: "ARTIFACTS_DIR_NOT_FOUND", details: "Failed to locate artifacts directory" },
      { status: 500 }
    );
  }

  let systemPrompt = "";
  try {
    const sysPromptPath = path.join(artifactsDir, "system_prompt.md");
    if (fs.existsSync(sysPromptPath)) {
      systemPrompt = fs.readFileSync(sysPromptPath, "utf-8");
    }
  } catch {}

  let toolsYaml = "";
  try {
    const toolsPath = path.join(artifactsDir, "tools.yaml");
    if (fs.existsSync(toolsPath)) {
      toolsYaml = fs.readFileSync(toolsPath, "utf-8");
    }
  } catch {}

  let reportMd = "";
  try {
    const reportPath = path.join(artifactsDir, "REPORT.md");
    if (fs.existsSync(reportPath)) {
      reportMd = fs.readFileSync(reportPath, "utf-8");
    }
  } catch {}

  let runbookMd = "";
  try {
    const runbookPath = path.join(artifactsDir, "PERSON1_RUNBOOK.md");
    if (fs.existsSync(runbookPath)) {
      runbookMd = fs.readFileSync(runbookPath, "utf-8");
    }
  } catch {}

  return NextResponse.json({
    systemPrompt,
    toolsYaml,
    reportMd,
    runbookMd,
  });
}
