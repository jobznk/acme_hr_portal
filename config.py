import os
from dotenv import load_dotenv

load_dotenv()

COMPANY_NAME = "ThoughtMinds"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

POLICY_FILE = os.path.join(BASE_DIR, "company_policy.txt")
CHROMA_DB_FOLDER = os.path.join(BASE_DIR, "chroma_db")
SQL_DB_FILE = os.path.join(BASE_DIR, "company_hr.db")

# Cloud LLM (Groq) — used automatically when GROQ_API_KEY is set
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")

# Local Fallback (Ollama)
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
CHAT_MODEL = "llama3.1"

CHUNK_SIZE = 500
CHUNK_OVERLAP = 50
TOP_K_RESULTS = 6
