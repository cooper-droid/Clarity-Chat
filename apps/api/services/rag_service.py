"""
RAG (Retrieval-Augmented Generation) service.
Handles semantic search and retrieval from approved documents.
"""
from typing import List, Dict, Optional
from sqlalchemy.orm import Session
from sqlalchemy import text

# Import models (try SQLite first)
try:
    from models_sqlite import Document, Chunk, DocumentStatus
except ImportError:
    from models import Document, Chunk, DocumentStatus

from services.ai_provider import ai_provider


class RAGService:
    def __init__(self, db: Session):
        self.db = db

    def retrieve_relevant_chunks(self, query: str, limit: int = 3) -> List[Dict]:
        """
        Retrieve most relevant chunks for a query.
        Uses vector similarity in production, keyword search in dev mode.
        """
        # Try vector search first
        embedding = ai_provider.generate_embedding(query)

        if embedding:
            return self._vector_search(embedding, limit)
        else:
            # Fallback to keyword search in dev mode
            return self._keyword_search(query, limit)

    def _vector_search(self, embedding: List[float], limit: int) -> List[Dict]:
        """Semantic search using pgvector."""
        try:
            # Convert embedding to pgvector format
            embedding_str = "[" + ",".join(map(str, embedding)) + "]"

            # Query using cosine similarity
            sql = text("""
                SELECT
                    c.id,
                    c.content,
                    c.chunk_index,
                    d.title,
                    d.source_url,
                    d.published_date,
                    1 - (c.embedding <=> :embedding::vector) as similarity
                FROM chunks c
                JOIN documents d ON c.document_id = d.id
                WHERE d.status = :status
                AND c.embedding IS NOT NULL
                ORDER BY c.embedding <=> :embedding::vector
                LIMIT :limit
            """)

            result = self.db.execute(
                sql,
                {
                    "embedding": embedding_str,
                    "status": DocumentStatus.APPROVED.value,
                    "limit": limit
                }
            )

            chunks = []
            for row in result:
                chunks.append({
                    "id": row[0],
                    "content": row[1],
                    "chunk_index": row[2],
                    "title": row[3],
                    "source_url": row[4],
                    "published_date": row[5].strftime("%Y-%m-%d") if row[5] else None,
                    "similarity": float(row[6])
                })

            return chunks

        except Exception as e:
            print(f"Vector search error: {e}")
            # Fallback to keyword search
            return self._keyword_search("", limit)

    def _keyword_search(self, query: str, limit: int) -> List[Dict]:
        """Fallback keyword search when embeddings unavailable."""
        try:
            keywords = query.lower().split()
            if not keywords:
                # Return most recent approved chunks
                results = (
                    self.db.query(Chunk, Document)
                    .join(Document)
                    .filter(Document.status == DocumentStatus.APPROVED)
                    .order_by(Document.created_at.desc())
                    .limit(limit)
                    .all()
                )
            else:
                # Search for chunks containing keywords
                search_pattern = "%{}%".format("%".join(keywords))
                results = (
                    self.db.query(Chunk, Document)
                    .join(Document)
                    .filter(Document.status == DocumentStatus.APPROVED)
                    .filter(Chunk.content.ilike(search_pattern))
                    .order_by(Document.created_at.desc())
                    .limit(limit)
                    .all()
                )

            chunks = []
            for chunk, doc in results:
                chunks.append({
                    "id": chunk.id,
                    "content": chunk.content,
                    "chunk_index": chunk.chunk_index,
                    "title": doc.title,
                    "source_url": doc.source_url,
                    "published_date": doc.published_date.strftime("%Y-%m-%d") if doc.published_date else None,
                    "similarity": 0.5  # Placeholder
                })

            return chunks

        except Exception as e:
            print(f"Keyword search error: {e}")
            return []

    def get_approved_documents(self) -> List[Document]:
        """Get all approved documents."""
        return (
            self.db.query(Document)
            .filter(Document.status == DocumentStatus.APPROVED)
            .order_by(Document.created_at.desc())
            .all()
        )
