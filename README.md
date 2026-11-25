# ThoughtMinds HR Assistant

A decoupled AI-powered HR employee portal built with a **Streamlit** frontend, a **FastAPI** backend, **LangGraph + Groq** agent orchestration, **MCP (Model Context Protocol)** tools, and **PostgreSQL + `pgvector`** for relational and vector persistence. Employees can view live leave balances, ask general or company-policy questions, apply for PTO/sick leave, and upload scanned policy documents for OCR indexing.

## Architecture (v3.0)

text
[Browser] ──► [Streamlit Frontend: app.py] (Thin UI + HRBackendClient)
                     │
                     │  REST HTTP (API_BASE_URL)
                     ▼
              [FastAPI Backend: api.py] (Groq + LangGraph + OCR + LangSmith)
                     │
                     ├──► [MCP Server: hr_mcp_server.py] (stdio tools & resources)
                     │
                     ▼
              [PostgreSQL + pgvector] (employees table + langchain_pg_embedding)
```

## Features

- **Decoupled Frontend & Backend:** Thin Streamlit UI (`app.py` + `services/api_client.py`) communicating over REST HTTP with a dedicated FastAPI server (`api.py`) with graceful offline handling.
- **PostgreSQL & `pgvector` Persistence:** Employee accounts, SHA-256 credentials, leave balances, and 384-dimension `FastEmbed` policy vectors stored in PostgreSQL using `psycopg_pool` and `langchain-postgres`.
- **MCP Tool & Resource Server:** `hr_mcp_server.py` exposes `search_hr_policies`, `check_leave_balance`, `submit_leave_request`, the `policy://handbook` resource, and the `apply_leave_workflow` prompt over `stdio`.
- **Multi-Format Document Ingestion & OCR:** Supports `.txt`, `.pdf`, `.png`, `.jpg`, and `.jpeg` policy uploads using `pypdf`, `pdf2image` (Poppler), and `pytesseract` (Tesseract OCR).
- **Live AI Observability:** Integrated with **LangSmith** for visual step-by-step tracing of Groq LLM prompts, MCP tool calls, latency, and token usage.

## Requirements

- Python 3.12
- PostgreSQL 16+ with the `pgvector` extension enabled (`CREATE EXTENSION IF NOT EXISTS vector;`)
- A Groq API key
- Tesseract OCR and Poppler for image OCR and scanned PDFs

Install the OCR system dependencies:

```bash
# macOS
brew install tesseract poppler

# Debian/Ubuntu
sudo apt-get update
sudo apt-get install -y tesseract-ocr poppler-utils
```

## Run Locally

1. **Create and activate a virtual environment, then install Python dependencies:**

```bash
python3.12 -m venv .venv-312
source .venv-312/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

2. **Configure your `.env` file in this directory:**

```dotenv
GROQ_API_KEY=your-groq-api-key
GROQ_MODEL=openai/gpt-oss-20b
DATABASE_URL=postgresql://postgres:password@localhost:5432/thoughtminds_hr
API_BASE_URL=http://localhost:8000

# Optional: LangSmith Observability
LANGSMITH_TRACING=true
LANGSMITH_API_KEY=your-langsmith-api-key
LANGSMITH_PROJECT=thoughtminds-hr-prod
LANGSMITH_ENDPOINT=https://langchain.com
```

3. **Start the FastAPI Backend (Terminal 1):**

```bash
uvicorn api:app --host 0.0.0.0 --port 8000 --reload
```

Interactive Swagger API documentation is available at [http://localhost:8000/docs](http://localhost:8000/docs).

4. **Start the Streamlit Frontend (Terminal 2):**

```bash
streamlit run app.py --server.port 8502
```

Open [http://localhost:8502](http://localhost:8502). On first startup, `FastEmbed` downloads the embedding model and seeds `company_policy.txt` into `pgvector`.

When the `employees` table is empty, the app seeds two demo accounts:

| Employee ID | Password | Role |
| --- | --- | --- |
| `EMP101` | `pass123` | Senior Software Engineer |
| `EMP102` | `secure456` | HR Manager |

These are demo credentials only; do not use them in a production deployment.

## Cloud Deployment (Railway)

This project is structured to deploy as **3 connected services** on Railway from a single repository:

1. **PostgreSQL (`Postgres-bpmt`):** Managed PostgreSQL database with `pgvector` enabled.
2. **FastAPI Backend (`thoughtminds-hr-api`):**
   - Start command: `uvicorn api:app --host 0.0.0.0 --port 8000`
   - Environment variables: `DATABASE_URL`, `GROQ_API_KEY`, `GROQ_MODEL`, `LANGSMITH_TRACING`, `LANGSMITH_API_KEY`, `LANGSMITH_PROJECT`, `LANGSMITH_ENDPOINT`
3. **Streamlit Frontend (`thoughtminds-hr`):**
   - Start command: `streamlit run app.py --server.port 8501 --server.address 0.0.0.0`
   - Environment variable: `API_BASE_URL` pointing to the FastAPI service URL

## MCP Server

The chat agent spawns `hr_mcp_server.py` as a `stdio` MCP server (forwarding `os.environ` so `DATABASE_URL` is inherited). MCP clients can also launch it directly:

```bash
python hr_mcp_server.py
```

## Tests

Run the integration use cases from this directory:

```bash
python test_use_cases.py
```

The tests exercise authentication, OCR, policy retrieval, and leave deduction against your configured PostgreSQL database and Groq API key.

## Project Layout

```text
api.py                     FastAPI REST backend entry point (/auth, /employees, /chat, /docs)
app.py                     Thin Streamlit employee portal UI
hr_mcp_server.py           MCP tools, resource (policy://handbook), and workflow prompt
config.py                  Environment variables and model/database configuration
company_policy.txt         Initial HR handbook seeded into pgvector
models.py                  Employee domain dataclass
repositories/
  employee_repo.py         PostgreSQL connection pool & employee/leave queries
  policy_repo.py           PGVector policy storage & similarity search
services/
  api_client.py            HTTP client wrapper with offline error handling for Streamlit
  auth_service.py          SHA-256 authentication, registration & default user seeding
  ocr_service.py           PDF, TXT, and Tesseract image text extraction
  rag_service.py           LangGraph + Groq + MCP stdio agent orchestration
test_use_cases.py          End-to-end integration tests
```
