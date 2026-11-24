import os
import tempfile
from langchain_postgres import PGVector
from langchain_text_splitters import RecursiveCharacterTextSplitter
from config import CHUNK_SIZE, CHUNK_OVERLAP
from services.ocr_service import extract_text_from_file


class PolicyRepository:
    def __init__(self, db_url: str, embedding_function, initial_policy_file: str):
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=CHUNK_SIZE,
            chunk_overlap=CHUNK_OVERLAP,
        )
        self.vectorstore = PGVector(
            embeddings=embedding_function,
            collection_name="thoughtminds_policies",
            connection=db_url,
            use_jsonb=True,
        )
        self._seed_initial_policies(initial_policy_file)

    def _seed_initial_policies(self, policy_file: str):
        existing = self.vectorstore.similarity_search("leave policy", k=1)
        if not existing and os.path.exists(policy_file):
            with open(policy_file, "r", encoding="utf-8") as f:
                text = f.read()
            docs = self.splitter.create_documents([text], metadatas=[{"source": policy_file}])
            self.vectorstore.add_documents(docs)

    def index_uploaded_file(self, filename: str, file_bytes: bytes) -> int:
        suffix = os.path.splitext(filename)[1]
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp.write(file_bytes)
            tmp_path = tmp.name

        try:
            extracted_text = extract_text_from_file(tmp_path)
            if not extracted_text.strip():
                return 0
            docs = self.splitter.create_documents([extracted_text], metadatas=[{"source": filename}])
            self.vectorstore.add_documents(docs)
            return len(docs)
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

    def search_relevant_policies(self, query: str, k: int = 4) -> str:
        results = self.vectorstore.similarity_search(query, k=k)
        if not results:
            return "No relevant policy sections found."
        return "\n\n".join(doc.page_content for doc in results)
