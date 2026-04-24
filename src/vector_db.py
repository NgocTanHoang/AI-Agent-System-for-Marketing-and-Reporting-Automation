"""
Knowledge Base Vector DB — Lưu trữ và truy vấn Brand Guidelines bằng ChromaDB.
Separate from ReportHistoryDB (few-shot RAG for reports).

Architecture:
  ┌──────────────────────────────────────────────────┐
  │  ChromaDB (data/chromadb/)                       │
  │  ├── Collection: good_reports  (báo cáo tốt)    │
  │  └── Collection: brand_knowledge (brand guides)  │
  └──────────────────────────────────────────────────┘
"""
import os
import hashlib
import logging
from pathlib import Path
from typing import List, Optional

import chromadb
from chromadb.utils import embedding_functions

logger = logging.getLogger("vector_db")


# ---------------------------------------------------------------------------
# 1. BRAND KNOWLEDGE BASE — Vector DB cho Brand Guidelines
# ---------------------------------------------------------------------------

class BrandKnowledgeDB:
    """
    Lưu trữ và truy vấn nội dung từ các file Brand Guidelines (.txt)
    trong data/raw/marketing_content/ bằng ChromaDB + sentence-transformers.

    Chunking strategy: Split theo đoạn văn (double newline),
    fallback split theo 500 ký tự nếu đoạn quá dài.
    """

    CHUNK_SIZE = 500
    CHUNK_OVERLAP = 50

    def __init__(self, db_path: Optional[str] = None, content_dir: Optional[str] = None):
        from src.config import PROJECT_ROOT, RAW_DATA_DIR

        self._db_path = db_path or str(PROJECT_ROOT / "data" / "chromadb")
        self._content_dir = content_dir or str(RAW_DATA_DIR / "marketing_content")
        os.makedirs(self._db_path, exist_ok=True)

        self._client = chromadb.PersistentClient(path=self._db_path)
        self._embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name="all-MiniLM-L6-v2"
        )
        self._collection = self._client.get_or_create_collection(
            name="brand_knowledge",
            embedding_function=self._embedding_fn,
        )

    # --- Chunking ---

    @staticmethod
    def _chunk_text(text: str, chunk_size: int = 500, overlap: int = 50) -> List[str]:
        """
        Split text thành chunks nhỏ hơn cho embedding.
        Ưu tiên split theo đoạn văn (\\n\\n), fallback sliding window.
        """
        # Thử split theo đoạn văn trước
        paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]

        chunks = []
        for para in paragraphs:
            if len(para) <= chunk_size:
                chunks.append(para)
            else:
                # Sliding window cho đoạn văn quá dài
                start = 0
                while start < len(para):
                    end = min(start + chunk_size, len(para))
                    chunks.append(para[start:end])
                    start += chunk_size - overlap
        return chunks

    # --- Indexing ---

    def index_brand_files(self, force_reindex: bool = False) -> dict:
        """
        Đọc tất cả file .txt trong content_dir, chunk, và index vào ChromaDB.
        Returns dict: {filename: n_chunks_indexed}.
        """
        content_path = Path(self._content_dir)
        if not content_path.exists():
            logger.warning("Không tìm thấy thư mục marketing_content: %s", content_path)
            return {}

        txt_files = sorted(content_path.glob("*.txt"))
        if not txt_files:
            logger.warning("Không có file .txt nào trong %s", content_path)
            return {}

        result = {}
        for fpath in txt_files:
            try:
                content = fpath.read_text(encoding="utf-8")
                if not content.strip():
                    continue

                chunks = self._chunk_text(content, self.CHUNK_SIZE, self.CHUNK_OVERLAP)
                if not chunks:
                    continue

                # Tạo deterministic IDs để tránh duplicate khi re-index
                ids = []
                metadatas = []
                for i, chunk in enumerate(chunks):
                    chunk_hash = hashlib.md5(
                        f"{fpath.name}::{i}::{chunk[:100]}".encode()
                    ).hexdigest()[:12]
                    doc_id = f"{fpath.stem}_{i}_{chunk_hash}"
                    ids.append(doc_id)
                    metadatas.append({
                        "source_file": fpath.name,
                        "chunk_index": i,
                        "total_chunks": len(chunks),
                    })

                # Kiểm tra xem đã index chưa (skip nếu không force)
                if not force_reindex:
                    existing = self._collection.get(ids=ids[:1])
                    if existing and existing["ids"]:
                        logger.info("⏭️  Đã index rồi (skip): %s", fpath.name)
                        result[fpath.name] = 0
                        continue

                # Upsert (idempotent — an toàn khi chạy lại)
                self._collection.upsert(
                    documents=chunks,
                    metadatas=metadatas,
                    ids=ids,
                )
                result[fpath.name] = len(chunks)
                logger.info("✅ Đã index %d chunks từ: %s", len(chunks), fpath.name)

            except Exception as e:
                logger.error("❌ Lỗi index file %s: %s", fpath.name, e)
                result[fpath.name] = -1

        return result

    # --- Querying ---

    def search(self, query: str, n_results: int = 5) -> str:
        """
        Semantic search trong brand knowledge base.
        Trả về formatted string để Agent đọc được.
        """
        if self._collection.count() == 0:
            return "⚠️ Brand Knowledge Base chưa được khởi tạo. Không có dữ liệu để tìm kiếm."

        n = min(n_results, self._collection.count())
        results = self._collection.query(
            query_texts=[query],
            n_results=n,
        )

        if not results or not results["documents"] or not results["documents"][0]:
            return f"Không tìm thấy nội dung liên quan đến: '{query}'"

        formatted_chunks = []
        docs = results["documents"][0]
        metas = results["metadatas"][0] if results.get("metadatas") else [{}] * len(docs)
        distances = results["distances"][0] if results.get("distances") else [0.0] * len(docs)

        for i, (doc, meta, dist) in enumerate(zip(docs, metas, distances)):
            source = meta.get("source_file", "unknown")
            relevance = round(1.0 - dist, 3) if dist < 1 else round(1.0 / (1 + dist), 3)
            formatted_chunks.append(
                f"--- Kết quả #{i+1} (Nguồn: {source}, Relevance: {relevance}) ---\n{doc}"
            )

        return "\n\n".join(formatted_chunks)

    def count(self) -> int:
        return self._collection.count()


# ---------------------------------------------------------------------------
# 2. REPORT HISTORY DB — Vector DB cho few-shot RAG (giữ nguyên logic cũ)
# ---------------------------------------------------------------------------

class ReportHistoryDB:
    """Lưu trữ báo cáo được đánh giá tốt để làm few-shot examples."""

    def __init__(self):
        from src.config import PROJECT_ROOT
        db_path = str(PROJECT_ROOT / "data" / "chromadb")
        os.makedirs(db_path, exist_ok=True)

        self.client = chromadb.PersistentClient(path=db_path)
        self.embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name="all-MiniLM-L6-v2"
        )
        self.collection = self.client.get_or_create_collection(
            name="good_reports",
            embedding_function=self.embedding_fn,
        )

    def add_report(self, report_id: str, content: str, topic: str, metadata: dict = None):
        """Lưu báo cáo được đánh giá tốt vào Vector DB."""
        if metadata is None:
            metadata = {}
        metadata["topic"] = topic
        self.collection.add(
            documents=[content],
            metadatas=[metadata],
            ids=[report_id],
        )

    def get_similar_reports(self, query: str, n_results: int = 3):
        """Query top n_results báo cáo tốt nhất làm few-shot examples."""
        if self.collection.count() == 0:
            return []

        results = self.collection.query(
            query_texts=[query],
            n_results=min(n_results, self.collection.count()),
        )

        if results and results["documents"]:
            return results["documents"][0]
        return []
