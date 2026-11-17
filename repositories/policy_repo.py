import os
import tempfile
from langchain_community.document_loaders import TextLoader, PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from config import CHUNK_SIZE, CHUNK_OVERLAP


class PolicyRepository:
    def __init__(self, persist_dir: str, embedding_function, initial_policy_file: str):
        self.persist_dir = persist_dir
        self.embedding_function = embedding_function
        self.initial_policy_file = initial_policy_file
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=CHUNK_SIZE,
            chunk_overlap=CHUNK_OVERLAP
        )
        self.db = self._load_or_initialize_db()

    def _load_or_initialize_db(self) -> Chroma:
        if os.path.exists(self.persist_dir) and os.listdir(self.persist_dir):
            return Chroma(
                persist_directory=self.persist_dir,
                embedding_function=self.embedding_function
            )

        loader = TextLoader(self.initial_policy_file)
        documents = loader.load()
        chunks = self.splitter.split_documents(documents)

        return Chroma.from_documents(
            documents=chunks,
            embedding=self.embedding_function,
            persist_directory=self.persist_dir
        )

    def search_relevant_policies(self, query: str, k: int = 3) -> str:
        retriever = self.db.as_retriever(search_kwargs={"k": k})
        matching_docs = retriever.invoke(query)
        return "\n\n".join(doc.page_content for doc in matching_docs)

    def index_uploaded_file(self, file_name: str, file_bytes: bytes) -> int:
        suffix = os.path.splitext(file_name)[1].lower()
        
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp_file:
            tmp_file.write(file_bytes)
            tmp_path = tmp_file.name

        try:
            loader = PyPDFLoader(tmp_path) if suffix == ".pdf" else TextLoader(tmp_path)
            documents = loader.load()
            chunks = self.splitter.split_documents(documents)

            for chunk in chunks:
                chunk.metadata["source"] = file_name

            self.db.add_documents(chunks)
            return len(chunks)
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
