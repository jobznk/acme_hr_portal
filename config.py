# import os

# BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# POLICY_FILE = os.path.join(BASE_DIR, "company_policy.txt")
# CHROMA_DB_FOLDER = os.path.join(BASE_DIR, "chroma_db")
# SQL_DB_FILE = os.path.join(BASE_DIR, "company_hr.db")

# EMBEDDING_MODEL = "nomic-embed-text"
# CHAT_MODEL = "llama3.1"
# CHUNK_SIZE = 500
# CHUNK_OVERLAP = 50
# TOP_K_RESULTS = 6


import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

POLICY_FILE = os.path.join(BASE_DIR, "company_policy.txt")
CHROMA_DB_FOLDER = os.path.join(BASE_DIR, "chroma_db")
SQL_DB_FILE = os.path.join(BASE_DIR, "company_hr.db")

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
EMBEDDING_MODEL = "nomic-embed-text"
CHAT_MODEL = "llama3.1"
CHUNK_SIZE = 500
CHUNK_OVERLAP = 50
TOP_K_RESULTS = 6

