# Plan: Deploy Frontend and Backend to a Single Vercel Project

## Overview
- **Priority:** High
- **Status:** In Progress
- **Description:** Deploy both Next.js Frontend and FastAPI Backend under one single Vercel project by using a unified `vercel.json` and a single deployment workflow.

## Proposed Changes

### 1. Configuration
- **Modify** [vercel.json](file:///d:/CODE/AITHUCCHIEN/LABS/day12_2A202600699_HoTatBaoHoang/06-lab-complete/vercel.json): Define builds for `@vercel/python` (backend) and `@vercel/next` (frontend) with routing rules.

### 2. Workflow
- **Modify** [deploy-vercel.yml](file:///d:/CODE/AITHUCCHIEN/LABS/day12_2A202600699_HoTatBaoHoang/.github/workflows/deploy-vercel.yml): Change working directory to `06-lab-complete` and run the deployment to the frontend project ID.
- **Delete** [deploy-backend-vercel.yml](file:///d:/CODE/AITHUCCHIEN/LABS/day12_2A202600699_HoTatBaoHoang/.github/workflows/deploy-backend-vercel.yml): Remove redundant standalone backend workflow.

## Success Criteria
- Frontend and backend deployed on the same Vercel project.
- Relative routing `/api/v1/*` automatically forwarded to Python without CORS.
- Unified workflow runs successfully.
