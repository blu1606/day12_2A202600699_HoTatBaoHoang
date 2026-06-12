# Plan: Deploy Backend FastAPI to Vercel

## Overview
- **Priority:** High
- **Status:** In Progress
- **Description:** Deploy the FastAPI backend from `06-lab-complete` to Vercel as a standalone service, resolve Vercel serverless read-only filesystem issues, and set up a deployment workflow.

## Proposed Changes

### 1. Backend Code
- **Modify** [transcripts_handler.py](file:///d:/CODE/AITHUCCHIEN/LABS/day12_2A202600699_HoTatBaoHoang/06-lab-complete/app/transcripts_handler.py): Use `/tmp/transcripts` for transcript storage on Vercel.

### 2. CI/CD Pipeline
- **New** [deploy-backend-vercel.yml](file:///d:/CODE/AITHUCCHIEN/LABS/day12_2A202600699_HoTatBaoHoang/.github/workflows/deploy-backend-vercel.yml): Setup dedicated backend deployment flow using Vercel CLI.

## Success Criteria
- Standalone backend successfully deployed to Vercel.
- API endpoints (`/health`, `/ready`, `/api/v1/transcripts`) respond correctly on Vercel deployment.
- No local file-writing crash on Vercel environment.
- CI/CD workflow passes.
