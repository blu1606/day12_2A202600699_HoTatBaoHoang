import { NextResponse } from "next/server";
import { FASTAPI_BASE_URL, getHeaders } from "@/lib/api-config";

export async function POST(request: Request) {
  const payload = await request.json();
  const query = payload.query || "";

  try {
    const response = await fetch(`${FASTAPI_BASE_URL}/api/v1/diagnose`, {
      method: "POST",
      headers: getHeaders({ "Content-Type": "application/json" }),
      body: JSON.stringify(payload),
    });
    const contentType = response.headers.get("content-type") ?? "";
    const data = contentType.includes("application/json")
      ? await response.json()
      : {
          error_code: "DIAGNOSE_BACKEND_NON_JSON_RESPONSE",
          message: await response.text(),
        };

    return NextResponse.json(data, { status: response.status });
  } catch {
    // Sandbox Mock Mode fallback: return mock state in 502 payload.
    // The client UI handles saving messages in localStorage, so no local file write is needed.
    return NextResponse.json(
      {
        error_code: "DIAGNOSE_BACKEND_UNAVAILABLE",
        message: "Backend diagnose service is unavailable (Simulating).",
      },
      { status: 502 }
    );
  }
}

