# ThoughtMinds HR Assistant

A Streamlit employee portal with an AI assistant for HR policy questions and leave workflows. Employees can view their leave balances, ask questions about the company handbook, request PTO or sick leave, and upload policy documents for indexing.

## Features

- Employee login and registration backed by SQLite.
- HR policy search using Chroma vector storage and FastEmbed embeddings.
- Leave-balance lookup and leave requests through MCP tools.
- PDF, text, and image policy uploads. Scanned PDFs and images are read with Tesseract OCR.
- An MCP server exposing policy search, leave tools, a handbook resource, and a reusable leave-workflow prompt.

## Requirements

- Python 3.12
- A Groq API key
- Tesseract OCR and Poppler for image OCR and scanned PDFs

Install the OCR dependencies:

```bash
# macOS
brew install tesseract poppler

# Debian/Ubuntu
sudo apt-get update
sudo apt-get install -y tesseract-ocr poppler-utils
```

## Run locally

From this directory, create and activate a virtual environment and install the Python dependencies:

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Set the Groq API key in the environment or in a `.env` file in this directory:

```dotenv
GROQ_API_KEY=your-groq-api-key
# Optional; defaults to llama-3.3-70b-versatile
GROQ_MODEL=llama-3.3-70b-versatile
```

Start the portal:

```bash
streamlit run app.py
```

Open [http://localhost:8501](http://localhost:8501). The embedding model is downloaded the first time it is needed.

When the employee database is empty, the app seeds two demo accounts:

| Employee ID | Password |
| --- | --- |
| `EMP101` | `pass123` |
| `EMP102` | `secure456` |

These are demo credentials only; do not use them in a production deployment.

## MCP server

The chat agent starts `hr_mcp_server.py` as a stdio MCP server when it needs HR tools. MCP clients can also launch it directly with the Python environment where the project dependencies are installed:

```bash
python hr_mcp_server.py
```

The server provides policy search, leave-balance lookup, leave submission, the `policy://handbook` resource, and the `apply_leave_workflow` prompt.

## Run with Docker

Build and run the Streamlit app from this directory. Provide a `.env` file containing `GROQ_API_KEY` as described above:

```bash
docker build -t thoughtminds-hr .
docker run --rm -p 8501:8501 --env-file .env thoughtminds-hr
```

## Tests

Run the integration use cases from this directory:

```bash
python test_use_cases.py
```

The tests exercise authentication, OCR, policy retrieval, and leave deduction. They require the configured Groq API key and the OCR system dependencies.

## Project layout

```text
app.py                    Streamlit employee portal
hr_mcp_server.py          MCP tools, resource, and prompt
config.py                 Application configuration and local data paths
company_policy.txt        Initial HR handbook indexed by the app
models.py                 Employee data model
repositories/              SQLite employee and Chroma policy repositories
services/                  Authentication, OCR, and chat-agent services
test_use_cases.py          Integration use cases
```

The employee database (`company_hr.db`) and vector index (`chroma_db/`) are local runtime data and are excluded from Git.
