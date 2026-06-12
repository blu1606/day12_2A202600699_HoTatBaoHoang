import { NextResponse } from "next/server";

export async function GET(request: Request) {
  const { searchParams } = new URL(request.url);
  const sessionId = searchParams.get("session_id");
  const list = searchParams.get("list");

  if (list === "true" || list === "1") {
    // Return mock transcript list
    return NextResponse.json([
      {
        id: "cohort-rag-session",
        name: "cohort-rag-session.json",
        created_at: new Date().toISOString(),
        size: 1540
      }
    ]);
  }

  // Return mock transcript details for a given session ID
  const targetSessionId = sessionId || "cohort-rag-session";
  return NextResponse.json({
    session_id: targetSessionId,
    turns: [
      {
        turn_index: 1,
        user: "Chẩn đoán cohort RAG và đề xuất hướng hỗ trợ học viên",
        assistant_text: "Cohort có 45 học viên, điểm trung bình 7.2, 5 học viên rủi ro, 2 concept cần theo dõi. Cohort cần ưu tiên Retrieval Augmented Generation (RAG) (45% học viên yếu). Nhóm Needs Foundation có 2 học viên cần củng cố nền tảng; nhóm Needs Practice có 2 học viên cần luyện tập thêm.",
        started_at: new Date(Date.now() - 5000).toISOString(),
        ended_at: new Date().toISOString(),
        rounds: [
          {
            round: 1,
            assistant_text: "Load mentor request",
            tool_calls: [
              {
                name: "get_session_cohort_data",
                args: { session_id: targetSessionId }
              }
            ],
            tool_results: [
              {
                tool: "get_session_cohort_data",
                args: { session_id: targetSessionId },
                result: {
                  cohort_summary: {
                    total_students: 45,
                    average_score: 7.2,
                    at_risk_count: 5
                  },
                  students: [
                    { id: "s1", name: "Nguyen Van A", score: 5.5 },
                    { id: "s2", name: "Tran Thi B", score: 6.0 }
                  ]
                }
              }
            ]
          }
        ]
      }
    ]
  });
}
