import { NextResponse } from "next/server";
import { traces } from "@/lib/mock-traces";

export async function POST(request: Request) {
  try {
    const payload = await request.json();
    const query = (payload.query || "").toLowerCase();

    // 1. Simulate Security Blocked
    if (query.includes("ignore") || query.includes("reveal system prompt") || query.includes("system prompt")) {
      const trace = traces.find(t => t.id === "security-blocked");
      return NextResponse.json(
        {
          error_code: "PROMPT_INJECTION_DETECTED",
          message: trace?.summary || "Yêu cầu bị từ chối: Phát hiện dấu hiệu chèn câu lệnh không an toàn.",
          steps: trace?.steps || [],
        },
        { status: 400 }
      );
    }

    // 2. Simulate Timeout Fallback
    if (query.includes("slow") || query.includes("timeout") || query.includes("delay")) {
      const trace = traces.find(t => t.id === "timeout-fallback");
      return NextResponse.json(
        {
          summary: trace?.summary || "",
          steps: trace?.steps || [],
          task_id: "task-fb-mock-123456",
          telemetry: {
            total_execution_time_ms: 5240,
            prompt_tokens: 0,
            completion_tokens: 0,
            estimated_cost_usd: 0.0,
            is_fallback_triggered: true,
          }
        },
        { status: 200 }
      );
    }

    // 3. Simulate Success Cohort Diagnostics (Default)
    const successTrace = traces.find(t => t.id === "success-cohort-diagnostic");
    return NextResponse.json(
      {
        summary: successTrace?.summary || "",
        steps: successTrace?.steps || [],
        task_id: "task-success-mock-123456",
        telemetry: {
          total_execution_time_ms: 3200,
          prompt_tokens: 1500,
          completion_tokens: 850,
          estimated_cost_usd: 0.045,
          is_fallback_triggered: false,
        }
      },
      { status: 200 }
    );
  } catch (error) {
    return NextResponse.json(
      {
        error_code: "MOCK_DIAGNOSE_ERROR",
        message: "Failed to process mock diagnose request.",
      },
      { status: 500 }
    );
  }
}
