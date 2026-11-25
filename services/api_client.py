import os
import requests


class HRBackendClient:
    """HTTP client wrapper for communicating safely with the FastAPI backend."""

    def __init__(self, base_url: str | None = None):
        self.base_url = (base_url or os.getenv("API_BASE_URL", "http://localhost:8000")).rstrip("/")

    def is_online(self) -> bool:
        try:
            res = requests.get(f"{self.base_url}/health", timeout=3)
            return res.status_code == 200
        except requests.exceptions.RequestException:
            return False

    def login(self, emp_id: str, password: str) -> tuple[dict | None, str]:
        try:
            res = requests.post(
                f"{self.base_url}/auth/login",
                json={"emp_id": emp_id, "password": password},
                timeout=10,
            )
            if res.status_code == 200:
                return res.json()["employee"], ""
            return None, res.json().get("detail", "Invalid Employee ID or Password.")
        except requests.exceptions.RequestException:
            return None, "⚠️ HR Backend Service is temporarily unavailable. Please try again in a moment."

    def register(
        self, emp_id: str, name: str, role: str, location: str, password: str
    ) -> tuple[bool, str]:
        try:
            res = requests.post(
                f"{self.base_url}/auth/register",
                json={
                    "emp_id": emp_id,
                    "name": name,
                    "role": role,
                    "location": location,
                    "password": password,
                },
                timeout=10,
            )
            if res.status_code == 200:
                return True, res.json()["message"]
            return False, res.json().get("detail", "Registration failed.")
        except requests.exceptions.RequestException:
            return False, "⚠️ HR Backend Service is temporarily unavailable. Please try again later."

    def get_employee(self, emp_id: str) -> dict | None:
        try:
            res = requests.get(f"{self.base_url}/employees/{emp_id}", timeout=5)
            return res.json()["employee"] if res.status_code == 200 else None
        except requests.exceptions.RequestException:
            return None

    def ask_agent(self, emp_id: str, prompt_text: str) -> str:
        try:
            res = requests.post(
                f"{self.base_url}/chat/ask",
                json={"emp_id": emp_id, "prompt_text": prompt_text},
                timeout=60,
            )
            if res.status_code == 200:
                return res.json()["reply"]
            return f"⚠️ Backend error: {res.json().get('detail', 'Something went wrong.')}"
        except requests.exceptions.RequestException:
            return "⚠️ **HR Backend Service is currently offline.** Please start the FastAPI server and try again."

    def upload_document(self, filename: str, file_bytes: bytes) -> tuple[int, str]:
        try:
            files = {"file": (filename, file_bytes)}
            res = requests.post(f"{self.base_url}/docs/upload", files=files, timeout=60)
            if res.status_code == 200:
                chunks = res.json()["chunks_indexed"]
                return chunks, "" if chunks > 0 else "Could not read any text from that file."
            return 0, res.json().get("detail", "Document upload failed.")
        except requests.exceptions.RequestException:
            return 0, "⚠️ Upload failed — HR Backend Service is currently offline."
