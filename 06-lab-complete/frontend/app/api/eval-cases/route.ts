import { NextResponse } from "next/server";
import { FASTAPI_BASE_URL } from "@/lib/api-config";

export async function GET() {
  const fastapiBaseUrl = FASTAPI_BASE_URL;
  try {
    const res = await fetch(`${fastapiBaseUrl}/api/v1/eval-cases`, {
      cache: "no-store",
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
    console.error("Failed to fetch eval-cases from backend:", error);
    return NextResponse.json(
      { error: "BACKEND_UNAVAILABLE" },
      { status: 502 }
    );
  }
}
