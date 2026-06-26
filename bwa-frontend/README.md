# ProcureFlow Frontend

Vite + React frontend for the Procurement & Vendor Onboarding Agent demo.

## Live Backend

```text
https://procureflow-api-114500421858.asia-south1.run.app
```

## Local Setup

```bash
npm install
npm run dev
```

The app reads the backend URL from:

```text
VITE_PROCUREFLOW_API_URL
```

Create `.env.local` if you need to override it:

```bash
VITE_PROCUREFLOW_API_URL=https://procureflow-api-114500421858.asia-south1.run.app
```

## Vercel Deployment

1. Import `bwa-frontend` as the Vercel project root.
2. Framework preset: `Vite`.
3. Build command: `npm run build`.
4. Output directory: `dist`.
5. Add environment variable:

```text
VITE_PROCUREFLOW_API_URL=https://procureflow-api-114500421858.asia-south1.run.app
```

## Demo Flow

1. Upload a vendor proposal PDF.
2. Enter requester, department, and annual amount.
3. Click `Analyze Vendor`.
4. Review agent cards and approval workflow.
