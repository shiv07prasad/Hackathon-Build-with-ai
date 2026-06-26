import type { AnalysisResponse } from "./types";

const defaultApiUrl = "https://procureflow-api-114500421858.asia-south1.run.app";

export const apiUrl =
  import.meta.env.VITE_PROCUREFLOW_API_URL?.replace(/\/$/, "") || defaultApiUrl;

export async function submitProposal(formData: FormData): Promise<AnalysisResponse> {
  const response = await fetch(`${apiUrl}/analyses`, {
    method: "POST",
    body: formData,
  });

  if (!response.ok) {
    const text = await response.text();
    throw new Error(text || `Request failed with ${response.status}`);
  }

  return response.json();
}
