from api.utils.vector_store_manager import VectorStoreManager
from api.utils.reranking import CrossEncoderReranker
from typing import List, Dict, Any
import asyncio

class RetrieverAgent:
    """
    Queries the vector store (Weaviate) and fetches relevant documents based on a user’s research query or theme.
    """
    def __init__(self, collection_name: str = "ResearchPaper", research_domain: str = "General"):
        self.collection_name = collection_name
        self.research_domain = research_domain
        self.vstore = VectorStoreManager(collection_name=self.collection_name, research_domain=self.research_domain)

    async def run(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Main entry point for retrieval.
        Args:
            query (str): The research prompt or topic.
            top_k (int): Number of top documents to return.
        Returns:
            List[Dict]: Ranked documents with metadata and provenance.
        """
        # Fetch candidates from Weaviate with domain filter
        candidates = await asyncio.to_thread(self.vstore.similarity_search, query, top_k, self.research_domain)

        # Verify provenance by refetching each UUID from Weaviate and attach provenance fields
        verified: List[Dict[str, Any]] = []
        for doc in candidates:
            uuid = doc.get("uuid")
            if not uuid:
                continue
            try:
                fetched = await asyncio.to_thread(self.vstore.weaviate.get_document_by_id, self.collection_name, uuid, False)
                if not fetched or not fetched.get("properties"):
                    continue
                # Attach provenance
                doc["provenance"] = {
                    "collection_name": self.collection_name,
                    "uuid": uuid,
                    "retrieval_mode": "near_text",
                    "source": "weaviate",
                }
                verified.append(doc)
            except Exception:
                continue

        if not verified:
            return []

        # Apply relevance cutoff based on vector distance (lower is better). Drop weak matches.
        MAX_DISTANCE = 0.35
        filtered = []
        for d in verified:
            md = d.get("metadata") or {}
            dist = md.get("distance")
            if dist is None or dist <= MAX_DISTANCE:
                filtered.append(d)
        if not filtered:
            return []

        # Cross-encoder reranking with scores
        pairs = await asyncio.to_thread(CrossEncoderReranker.rerank_with_scores, query, filtered, top_k)
        ranked_docs: List[Dict[str, Any]] = []
        for doc, score in pairs:
            meta = doc.get("metadata") or {}
            meta["rerank_score"] = float(score)
            doc["metadata"] = meta
            ranked_docs.append(doc)

        return ranked_docs 