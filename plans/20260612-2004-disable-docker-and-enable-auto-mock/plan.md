# Plan: Disable Docker Build and Enable Full Auto-Mock Mode

Kế hoạch tạm thời disable các job build Docker trong GitHub Actions và chuyển ứng dụng sang chế độ Auto-Mock hoàn toàn từ Frontend cho tới các Next.js API Routes.

## Progress
- [x] Phase 1: Vô hiệu hóa Docker build trong GitHub Actions Workflows
- [x] Phase 2: Ép chế độ Mock mặc định và ẩn button toggle trên UI chat
- [x] Phase 3: Mock toàn bộ các API Next.js routes
- [x] Phase 4: Kiểm tra và kiểm thử chất lượng

## Key Dependencies
- Không có dependency ngoài.

## Phase 1: Disable Docker Build in CI/CD
- File đã sửa:
  - [ci.yml](file:///d:/CODE/AITHUCCHIEN/LABS/day12_2A202600699_HoTatBaoHoang/.github/workflows/ci.yml): comment out job `verify-docker-build`.
  - [deploy-docker.yml](file:///d:/CODE/AITHUCCHIEN/LABS/day12_2A202600699_HoTatBaoHoang/.github/workflows/deploy-docker.yml): đổi trigger `on` thành `workflow_dispatch`.

## Phase 2: Force Frontend Chat Mock Mode
- File đã sửa:
  - [chat-panel-interactive.tsx](file:///d:/CODE/AITHUCCHIEN/LABS/day12_2A202600699_HoTatBaoHoang/06-lab-complete/frontend/components/chat-panel-interactive.tsx):
    - Đặt mặc định `useState(true)` cho `isMockMode`.
    - Xóa nút toggler của Mock Mode / Live API và thay bằng một badge "Sandbox Mock Mode" tĩnh.

## Phase 3: Mock Next.js API Routes
- File đã sửa:
  - `/api/diagnose/route.ts`: Luôn trả về mock response chẩn đoán tĩnh tương tự cấu trúc thành công của FastAPI (đáp ứng thông minh theo query đầu vào).
  - `/api/transcripts/route.ts`: Trả về danh sách transcript tĩnh hoặc transcript cụ thể.
  - `/api/runs/route.ts`: Trả về danh sách rỗng hoặc dữ liệu chạy kiểm thử mock.
  - `/api/eval-cases/route.ts`: Đọc file `.json` trực tiếp từ thư mục `data/` của project ở local và trả về.
  - `/api/prompt-tools/route.ts`: Đọc file `system_prompt.md`, `tools.yaml`, `REPORT.md`, `PERSON1_RUNBOOK.md` cục bộ qua `fs` và trả về.
  - `/api/version-log/route.ts`: Đọc file `version_log.csv` cục bộ qua `fs` và trả về.
