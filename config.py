import os
from dotenv import load_dotenv

load_dotenv()

COMPANY_NAME = "ThoughtMinds"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
POLICY_FILE = os.path.join(BASE_DIR, "company_policy.txt")

# PostgreSQL + pgvector Connection URL (used for Employee tables and Policy vectors)
RAW_DB_URL = os.getenv("DATABASE_URL", "")
if RAW_DB_URL.startswith("postgres://"):
    DATABASE_URL = RAW_DB_URL.replace("postgres://", "postgresql+psycopg://", 1)
elif RAW_DB_URL.startswith("postgresql://"):
    DATABASE_URL = RAW_DB_URL.replace("postgresql://", "postgresql+psycopg://", 1)
else:
    DATABASE_URL = RAW_DB_URL

# Cloud LLM (Groq) — used automatically when GROQ_API_KEY is set
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-20b")

# Local Fallback (Ollama)
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
EMBEDDING_MODEL = "BAAI/bge-small-en-v1.5"
CHAT_MODEL = "llama3.1"

CHUNK_SIZE = 500
CHUNK_OVERLAP = 50
TOP_K_RESULTS = 6
