export type Risk = {
  type: string;
  severity: "low" | "medium" | "high" | string;
  message: string;
};

export type WorkflowStep = {
  step: string;
  status: string;
  reason: string;
};

export type AgentResults = {
  intake?: Record<string, unknown>;
  contract?: Record<string, unknown>;
  security?: Record<string, unknown>;
  budget?: Record<string, unknown>;
  approval?: Record<string, unknown>;
};

export type AnalysisResponse = {
  analysis_id: string;
  status: string;
  vendor: {
    name: string;
    service: string;
    department: string;
    annual_cost: number | null;
  };
  agent_results: AgentResults;
  risks: Risk[];
  required_approvals: string[];
  workflow: WorkflowStep[];
  summary: string;
};
