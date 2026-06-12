import { NextResponse } from "next/server";
import { FASTAPI_BASE_URL, getHeaders } from "@/lib/api-config";

export async function GET(request: Request) {
  const fastapiBaseUrl = FASTAPI_BASE_URL;
  const { searchParams } = new URL(request.url);
  const sessionId = searchParams.get("session_id");
  const list = searchParams.get("list");

  let url = `${fastapiBaseUrl}/api/v1/transcripts`;
  const params = new URLSearchParams();
  if (list) params.append("list", list);
  if (sessionId) params.append("session_id", sessionId);
  
  if (params.toString()) {
    url += `?${params.toString()}`;
  }

  try {
    const res = await fetch(url, {
      cache: "no-store",
      headers: getHeaders(),
    });
    if (!res.ok) {
      return NextResponse.json(
        { error: "BACKEND_ERROR", details: `Backend returned status ${res.status}` },
        { status: 502 }
      );
    }
    const data = await res.json();
    return NextResponse.json(data);
  } catch (error: any) {
    console.error("Failed to fetch transcripts from backend:", error);
    return NextResponse.json(
      { error: "BACKEND_UNAVAILABLE" },
      { status: 502 }
    );
  }
}


