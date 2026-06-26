from uuid import uuid4

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from app.models import AnalysisResponse
from app.nasiko_client import AgentClient
from app.pdf import extract_pdf_text
from app.store import AnalysisStore
from app.workflow import ProcurementWorkflow

app = FastAPI(title="ProcureFlow API", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

store = AnalysisStore()
workflow = ProcurementWorkflow(store=store, agent_client=AgentClient())


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "healthy", "service": "procureflow-api"}


@app.post("/analyses", response_model=AnalysisResponse)
async def create_analysis(
    file: UploadFile = File(...),
    requester: str | None = Form(default=None),
    department: str | None = Form(default=None),
    estimated_amount: float | None = Form(default=None),
) -> dict:
    if file.content_type not in {"application/pdf", "application/octet-stream"}:
        raise HTTPException(status_code=400, detail="Upload a PDF proposal.")

    file_bytes = await file.read()
    proposal_text = extract_pdf_text(file_bytes)
    if not proposal_text:
        raise HTTPException(status_code=400, detail="Could not extract text from PDF.")

    analysis_id = str(uuid4())
    metadata = {
        "requester": requester,
        "department": department,
        "estimated_amount": estimated_amount,
        "filename": file.filename,
    }
    store.create(
        analysis_id,
        {
            "analysis_id": analysis_id,
            "status": "created",
            **metadata,
            "extracted_text": proposal_text,
            "agent_results": {},
        },
    )

    return await workflow.run(
        analysis_id=analysis_id,
        proposal_text=proposal_text,
        metadata=metadata,
    )


@app.get("/analyses/{analysis_id}")
async def get_analysis(analysis_id: str) -> dict:
    record = store.get(analysis_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Analysis not found.")
    return record
