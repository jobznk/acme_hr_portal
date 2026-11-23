import os
import tempfile
from langchain_core.documents import Document
from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma

from config import CHUNK_SIZE, CHUNK_OVERLAP
from services.ocr_service import extract_text_from_file


class PolicyRepository:
    def __init__(self, persist_dir: str, embedding_function, initial_policy_file: str):
        self.persist_dir = persist_dir
        self.embedding_function = embedding_function
        self.initial_policy_file = initial_policy_file
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=CHUNK_SIZE,
            chunk_overlap=CHUNK_OVERLAP,
        )
        self.db = self._load_or_initialize_db()

    def _load_or_initialize_db(self) -> Chroma:
        if os.path.exists(self.persist_dir) and os.listdir(self.persist_dir):
            return Chroma(
                persist_directory=self.persist_dir,
                embedding_function=self.embedding_function,
            )

        documents = TextLoader(self.initial_policy_file).load()
        chunks = self.splitter.split_documents(documents)

        return Chroma.from_documents(
            documents=chunks,
            embedding=self.embedding_function,
            persist_directory=self.persist_dir,
        )

    def search_relevant_policies(self, query: str, k: int = 3) -> str:
        matching_docs = self.db.similarity_search(query, k=k)
        if not matching_docs:
            return "No matching policy found."
        return "\n\n".join(doc.page_content for doc in matching_docs)

    def index_uploaded_file(self, file_name: str, file_bytes: bytes) -> int:
        """Save uploaded file temporarily, extract text (with OCR), and save to ChromaDB."""
        extension = os.path.splitext(file_name)[1].lower()

        with tempfile.NamedTemporaryFile(delete=False, suffix=extension) as tmp_file:
            tmp_file.write(file_bytes)
            tmp_path = tmp_file.name

        try:
            # Step 1: Extract text using our OCR helper
            text = extract_text_from_file(tmp_path)
            if not text:
                return 0

            # Step 2: Split text into chunks and save in ChromaDB
            doc = Document(page_content=text, metadata={"source": file_name})
            chunks = self.splitter.split_documents([doc])
            self.db.add_documents(chunks)
            return len(chunks)
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
