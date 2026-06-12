import { NextResponse } from "next/server";
import fs from "fs";
import path from "path";

function findDataDirectory(): string | null {
  const pathsToTry = [
    path.join(process.cwd(), "data"),
    path.join(process.cwd(), "..", "data"),
    path.join(process.cwd(), "06-lab-complete", "data"),
    path.join("/var/task", "data"),
    path.join("/var/task", "06-lab-complete", "data"),
  ];

  for (const p of pathsToTry) {
    if (fs.existsSync(p) && fs.lstatSync(p).isDirectory()) {
      return p;
    }
  }
  return null;
}

export async function GET() {
  const dataDir = findDataDirectory();
  if (!dataDir) {
    console.error("Data directory not found in paths.");
    return NextResponse.json(
      { error: "DATA_DIR_NOT_FOUND", details: "Failed to locate data directory" },
      { status: 500 }
    );
  }

  try {
    const result: Record<string, any> = {};
    const files = fs.readdirSync(dataDir);
    
    for (const filename of files) {
      if (!filename.endswith(".json")) {
        continue;
      }
      
      const filePath = path.join(dataDir, filename);
      try {
        const content = fs.readFileSync(filePath, "utf-8");
        result[filename] = JSON.parse(content);
      } catch (err: any) {
        result[filename] = { error: `Failed to read/parse: ${err.message}` };
      }
    }

    return NextResponse.json(result);
  } catch (error: any) {
    console.error("Failed to read eval cases:", error);
    return NextResponse.json(
      { error: "EVAL_CASES_READ_FAILED", details: error.message },
      { status: 500 }
    );
  }
}
