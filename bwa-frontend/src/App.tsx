import { FormEvent, useMemo, useState } from "react";
import { apiUrl, submitProposal } from "./api";
import type { AnalysisResponse, AgentResults, Risk } from "./types";

const agentOrder: Array<{
  key: keyof AgentResults;
  title: string;
  description: string;
}> = [
  {
    key: "intake",
    title: "Vendor Intake Agent",
    description: "Extracts vendor, amount, department, service, term, and missing fields.",
  },
  {
    key: "contract",
    title: "Contract Risk Agent",
    description: "Finds auto-renewal, cancellation, liability, SLA, and negotiation risks.",
  },
  {
    key: "security",
    title: "Security Review Agent",
    description: "Checks customer data, SOC2, DPA, GDPR, and security evidence gaps.",
  },
  {
    key: "budget",
    title: "Budget Agent",
    description: "Checks department budget and finance approval thresholds.",
  },
  {
    key: "approval",
    title: "Approval Agent",
    description: "Creates the final approval decision and review workflow.",
  },
];

function App() {
  const [file, setFile] = useState<File | null>(null);
  const [requester, setRequester] = useState("Shiv");
  const [department, setDepartment] = useState("Sales");
  const [amount, setAmount] = useState("48000");
  const [analysis, setAnalysis] = useState<AnalysisResponse | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const completedAgents = useMemo(() => {
    if (!analysis) return 0;
    return agentOrder.filter((agent) => Boolean(analysis.agent_results[agent.key])).length;
  }, [analysis]);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!file) {
      setError("Upload a vendor proposal PDF first.");
      return;
    }

    setIsLoading(true);
    setError(null);
    setAnalysis(null);

    const formData = new FormData();
    formData.append("file", file);
    formData.append("requester", requester);
    formData.append("department", department);
    formData.append("estimated_amount", amount);

    try {
      setAnalysis(await submitProposal(formData));
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Something went wrong.");
    } finally {
      setIsLoading(false);
    }
  }

  return (
    <main className="app-shell">
      <section className="hero">
        <div>
          <p className="eyebrow">Enterprise Agent Engineering</p>
          <h1>ProcureFlow AI</h1>
          <p className="hero-copy">
            Upload a vendor proposal and let ADK-powered procurement agents produce risk checks,
            budget validation, negotiation points, and an approval workflow.
          </p>
        </div>
        <div className="stack-card">
          <span>Google ADK</span>
          <span>Nasiko-ready AgentCards</span>
          <span>Cloud Run Backend</span>
          <span>Firestore Memory</span>
        </div>
      </section>

      <section className="workspace">
        <aside className="panel upload-panel">
          <div className="panel-heading">
            <p className="eyebrow">Step 1</p>
            <h2>Vendor Submission</h2>
          </div>
          <form onSubmit={handleSubmit}>
            <label className="file-drop">
              <input
                accept="application/pdf"
                type="file"
                onChange={(event) => setFile(event.target.files?.[0] ?? null)}
              />
              <span>{file ? file.name : "Choose proposal PDF"}</span>
              <small>PDF proposals, invoices, or SaaS quotes</small>
            </label>

            <label>
              Requester
              <input value={requester} onChange={(event) => setRequester(event.target.value)} />
            </label>

            <label>
              Department
              <select value={department} onChange={(event) => setDepartment(event.target.value)}>
                <option>Sales</option>
                <option>Marketing</option>
                <option>Engineering</option>
                <option>HR</option>
              </select>
            </label>

            <label>
              Estimated annual amount
              <input
                inputMode="numeric"
                value={amount}
                onChange={(event) => setAmount(event.target.value)}
              />
            </label>

            <button disabled={isLoading} type="submit">
              {isLoading ? "Agents analyzing..." : "Analyze Vendor"}
            </button>
          </form>
          <p className="api-note">API: {apiUrl}</p>
          {error && <div className="error-box">{error}</div>}
        </aside>

        <section className="panel analysis-panel">
          <div className="panel-heading split">
            <div>
              <p className="eyebrow">Step 2</p>
              <h2>Agent Analysis</h2>
            </div>
            <div className="progress-pill">
              {analysis ? `${completedAgents}/5 complete` : isLoading ? "Running" : "Waiting"}
            </div>
          </div>

          <div className="agent-grid">
            {agentOrder.map((agent) => (
              <AgentCard
                key={agent.key}
                title={agent.title}
                description={agent.description}
                result={analysis?.agent_results[agent.key]}
                isLoading={isLoading}
              />
            ))}
          </div>
        </section>

        <aside className="panel decision-panel">
          <div className="panel-heading">
            <p className="eyebrow">Step 3</p>
            <h2>Approval Workflow</h2>
          </div>
          {analysis ? <DecisionSummary analysis={analysis} /> : <EmptyDecision isLoading={isLoading} />}
        </aside>
      </section>
    </main>
  );
}

function AgentCard({
  title,
  description,
  result,
  isLoading,
}: {
  title: string;
  description: string;
  result?: Record<string, unknown>;
  isLoading: boolean;
}) {
  const status = result ? "Complete" : isLoading ? "Running" : "Waiting";

  return (
    <article className={`agent-card ${status.toLowerCase()}`}>
      <div className="agent-card-header">
        <h3>{title}</h3>
        <span>{status}</span>
      </div>
      <p>{description}</p>
      {result && <pre>{JSON.stringify(result, null, 2)}</pre>}
    </article>
  );
}

function DecisionSummary({ analysis }: { analysis: AnalysisResponse }) {
  return (
    <div className="decision-content">
      <div className={`status-card ${analysis.status}`}>
        <span>Approval Status</span>
        <strong>{formatLabel(analysis.status)}</strong>
        <p>{analysis.summary}</p>
      </div>

      <div className="vendor-card">
        <h3>{analysis.vendor.name}</h3>
        <p>{analysis.vendor.service}</p>
        <div className="metric-row">
          <span>{analysis.vendor.department}</span>
          <span>{formatCurrency(analysis.vendor.annual_cost)}</span>
        </div>
      </div>

      <div>
        <h3>Required Approvals</h3>
        <div className="chip-row">
          {analysis.required_approvals.map((approval) => (
            <span className="chip" key={approval}>
              {approval}
            </span>
          ))}
        </div>
      </div>

      <div>
        <h3>Top Risks</h3>
        <div className="risk-list">
          {analysis.risks.map((risk, index) => (
            <RiskItem key={`${risk.type}-${risk.message}-${index}`} risk={risk} />
          ))}
        </div>
      </div>

      <div>
        <h3>Workflow</h3>
        <div className="timeline">
          {analysis.workflow.map((step) => (
            <div className="timeline-step" key={step.step}>
              <span />
              <div>
                <strong>{step.step}</strong>
                <p>{step.reason}</p>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

function RiskItem({ risk }: { risk: Risk }) {
  return (
    <div className="risk-item">
      <span className={`severity ${risk.severity}`}>{risk.severity}</span>
      <p>{risk.message}</p>
    </div>
  );
}

function EmptyDecision({ isLoading }: { isLoading: boolean }) {
  return (
    <div className="empty-state">
      <div className="orb" />
      <h3>{isLoading ? "Routing to agents..." : "No decision yet"}</h3>
      <p>
        {isLoading
          ? "The procurement agents are extracting terms, checking budget, and building the workflow."
          : "Upload a PDF to generate approval routing, risks, and next steps."}
      </p>
    </div>
  );
}

function formatLabel(value: string) {
  return value
    .split("_")
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(" ");
}

function formatCurrency(value: number | null) {
  if (value === null) return "Unknown amount";
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    maximumFractionDigits: 0,
  }).format(value);
}

export default App;
