"""LanceDB repository implementation for vector storage and hybrid search."""

import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

import lancedb
from lancedb.pydantic import LanceModel, Vector
from sentence_transformers import SentenceTransformer


class ResearchDocument(LanceModel):  # type: ignore[misc]
    """Document stored in LanceDB with vector embedding."""

    id: str
    content: str
    vector: Vector(384)  # type: ignore[valid-type]  # bge-small-en-v1.5 dimension
    session_id: str
    source_url: str | None = None
    source_name: str | None = None
    domain: str | None = None
    created_at: str  # ISO format datetime
    metadata: str  # JSON-encoded metadata


class LanceDBRepository:
    """LanceDB implementation for vector storage and hybrid search."""

    TABLE_NAME = "research_documents"
    MODEL_NAME = "BAAI/bge-small-en-v1.5"
    CHUNK_SIZE = 400  # Approximate words for 512 tokens
    CHUNK_OVERLAP = 50  # Approximate words for 64 tokens

    def __init__(self, db_path: str = "./data/lance_db") -> None:
        """Initialize LanceDB repository.

        Args:
            db_path: Path to LanceDB database directory
        """
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.embedder = SentenceTransformer(self.MODEL_NAME)
        self.db = lancedb.connect(str(self.db_path))
        self._table: Any = None

    def _get_table(self) -> Any:
        """Get or create the documents table."""
        if self._table is None:
            try:
                self._table = self.db.open_table(self.TABLE_NAME)
            except Exception:
                # Table doesn't exist, create it
                self._table = self.db.create_table(
                    self.TABLE_NAME,
                    schema=ResearchDocument
                )
        return self._table

    def chunk_document(self, text: str) -> list[str]:
        """Chunk document for embedding.

        Uses sliding window approach with overlap:
        - Target: 512 tokens (~400 words)
        - Overlap: 64 tokens (~50 words)

        Args:
            text: The text to chunk

        Returns:
            list[str]: List of text chunks
        """
        words = text.split()
        chunks = []

        for i in range(0, len(words), self.CHUNK_SIZE - self.CHUNK_OVERLAP):
            chunk = ' '.join(words[i:i + self.CHUNK_SIZE])
            if chunk:
                chunks.append(chunk)

        return chunks if chunks else [text]  # Return original if no chunks

    async def store_document(
        self,
        content: str,
        metadata: dict[str, Any],
        session_id: str
    ) -> str:
        """Store document with embedding.

        Chunks the document and stores each chunk separately.

        Args:
            content: The document content to store
            metadata: Additional metadata about the document
            session_id: The research session ID

        Returns:
            str: The primary document ID (first chunk)
        """
        table = self._get_table()
        chunks = self.chunk_document(content)
        embeddings = self.embedder.encode(chunks)

        primary_id: str | None = None
        documents = []

        for i, (chunk, embedding) in enumerate(zip(chunks, embeddings, strict=True)):
            doc_id = str(uuid.uuid4())
            if i == 0:
                primary_id = doc_id

            chunk_metadata = {**metadata, "chunk_index": i, "total_chunks": len(chunks)}

            doc = ResearchDocument(
                id=doc_id,
                content=chunk,
                vector=embedding.tolist(),
                session_id=session_id,
                source_url=metadata.get("source_url"),
                source_name=metadata.get("source_name"),
                domain=metadata.get("domain"),
                created_at=datetime.now().isoformat(),
                metadata=json.dumps(chunk_metadata)
            )
            documents.append(doc.model_dump())

        table.add(documents)
        if primary_id is None:
            raise ValueError("No documents were created")
        return primary_id

    def _merge_results(
        self,
        semantic_results: list[dict[str, Any]],
        keyword_results: list[dict[str, Any]],
        semantic_weight: float = 0.6,
        keyword_weight: float = 0.4
    ) -> list[dict[str, Any]]:
        """Merge semantic and keyword search results with weighted scoring.

        Args:
            semantic_results: Results from vector search
            keyword_results: Results from full-text search
            semantic_weight: Weight for semantic scores
            keyword_weight: Weight for keyword scores

        Returns:
            list[dict]: Merged and sorted results
        """
        # Create score maps
        semantic_scores: dict[str, float] = {
            r["id"]: r.get("_distance", 1.0) for r in semantic_results
        }
        keyword_scores: dict[str, float] = {
            r["id"]: r.get("score", 0.0) for r in keyword_results
        }

        # Normalize scores (semantic uses distance, lower is better)
        if semantic_scores:
            max_distance = max(semantic_scores.values())
            semantic_scores = {
                k: 1.0 - (v / max_distance) if max_distance > 0 else 1.0
                for k, v in semantic_scores.items()
            }

        if keyword_scores:
            max_keyword = max(keyword_scores.values())
            keyword_scores = {
                k: v / max_keyword if max_keyword > 0 else 0.0
                for k, v in keyword_scores.items()
            }

        # Combine scores
        all_ids = set(semantic_scores.keys()) | set(keyword_scores.keys())
        combined_scores: dict[str, float] = {}
        for doc_id in all_ids:
            sem_score = semantic_scores.get(doc_id, 0.0)
            key_score = keyword_scores.get(doc_id, 0.0)
            combined_scores[doc_id] = (
                semantic_weight * sem_score + keyword_weight * key_score
            )

        # Get documents and add combined scores
        doc_map: dict[str, dict[str, Any]] = {
            r["id"]: r for r in semantic_results + keyword_results
        }
        results: list[dict[str, Any]] = []
        for doc_id, score in combined_scores.items():
            doc = doc_map.get(doc_id)
            if doc:
                doc["combined_score"] = score
                results.append(doc)

        # Sort by combined score (descending)
        results.sort(key=lambda x: x["combined_score"], reverse=True)
        return results

    async def search_similar(
        self,
        query: str,
        limit: int = 10,
        filters: dict[str, Any] | None = None
    ) -> list[dict[str, Any]]:
        """Search for similar documents using hybrid search.

        Combines semantic (vector) search and keyword (FTS) search:
        - 60% semantic similarity
        - 40% keyword matching

        Args:
            query: The search query
            limit: Maximum number of results to return
            filters: Optional filters to apply (not implemented yet)

        Returns:
            list[dict]: List of matching documents with metadata
        """
        _ = filters  # Not implemented yet
        table = self._get_table()

        # Get query embedding
        query_vector = self.embedder.encode(query)

        # Semantic search
        semantic_results: list[dict[str, Any]] = (
            table.search(query_vector.tolist())
            .limit(limit * 2)
            .to_list()
        )

        # Keyword search (FTS)
        keyword_results: list[dict[str, Any]]
        try:
            keyword_results = (
                table.search(query, query_type="fts")
                .limit(limit * 2)
                .to_list()
            )
        except Exception:
            # FTS might not be enabled, fall back to semantic only
            keyword_results = []

        # Merge results with weighted scoring
        combined = self._merge_results(
            semantic_results,
            keyword_results,
            semantic_weight=0.6,
            keyword_weight=0.4
        )

        return combined[:limit]
