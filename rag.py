import os
from pathlib import Path
from typing import List

import certifi
from dotenv import load_dotenv

load_dotenv()

os.environ["SSL_CERT_FILE"] = certifi.where()
os.environ["REQUESTS_CA_BUNDLE"] = certifi.where()

from langchain_chroma import Chroma
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from pypdf import PdfReader
import docx2txt

Path("uploads").mkdir(exist_ok=True)
Path("chroma_db").mkdir(exist_ok=True)

# Khởi tạo mô hình Embedding của Google
embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")

vectorstore = Chroma(
    collection_name="tuonggpt_rag_docs",
    embedding_function=embeddings,
    persist_directory="chroma_db"
)


def read_file_text(file_path: str) -> str:
    path = Path(file_path)
    suffix = path.suffix.lower()

    if suffix == ".pdf":
        reader = PdfReader(file_path)
        text = ""
        for page in reader.pages:
            text += (page.extract_text() or "") + "\n"
        return text

    if suffix == ".docx":
        return docx2txt.process(file_path)

    if suffix in [".txt", ".md", ".py", ".csv"]:
        return path.read_text(encoding="utf-8", errors="ignore")

    raise ValueError("Định dạng file không hỗ trợ. Hỗ trợ: PDF, DOCX, TXT, MD, PY, CSV.")


def add_document_to_rag(file_path: str, user_id: str, thread_id: str):
    """Cắt đoạn và gán metadata user_id + thread_id vào từng chunk."""
    text = read_file_text(file_path)
    if not text.strip():
        raise ValueError("Không thể trích xuất văn bản từ tệp này.")

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=900,
        chunk_overlap=150
    )
    chunks = splitter.split_text(text)

    docs: List[Document] = [
        Document(
            page_content=chunk,
            metadata={
                "user_id": str(user_id),
                "thread_id": str(thread_id),
                "source": Path(file_path).name
            }
        )
        for chunk in chunks
    ]

    vectorstore.add_documents(docs)
    return {
        "filename": Path(file_path).name,
        "chunks": len(docs)
    }


def retrieve_from_rag(query: str, user_id: str, thread_id: str, k: int = 4) -> str:
    """Retrieve RAG follow User and Thread."""
    # Lọc kép: Chỉ tài liệu của đúng user_id VÀ đúng thread_id mới được tìm thấy
    filter_criteria = {
        "$and": [
            {"user_id": str(user_id)},
            {"thread_id": str(thread_id)}
        ]
    }

    try:
        docs = vectorstore.similarity_search(
            query,
            k=k,
            filter=filter_criteria
        )
    except Exception:
        # Dự phòng trường hợp ChromaDB phiên bản cũ không hỗ trợ $and phức tạp
        docs = vectorstore.similarity_search(
            query,
            k=k,
            filter={"thread_id": str(thread_id)}
        )
        docs = [d for d in docs if d.metadata.get("user_id") == str(user_id)]

    if not docs:
        return "No relevant uploaded document content found for this conversation."

    results = []
    for i, doc in enumerate(docs, start=1):
        source = doc.metadata.get("source", "uploaded document")
        results.append(f"[Source {i}: {source}]\n{doc.page_content}")

    return "\n\n".join(results)