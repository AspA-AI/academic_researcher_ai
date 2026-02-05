"""
Smart Retrieval Service - Intelligent document retrieval with quality evaluation and fallback.
"""

import asyncio
import uuid
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
import sys
import os

# Add the parent directory to the path to import utils

from api.utils.vector_store_manager import VectorStoreManager
from api.services.data_extraction_service import DataExtractionService
from api.services.retrieval_quality import (
    RetrievalQualityConfig,
    attach_rerank_scores,
    adaptive_rerank_threshold,
    rerank_score_stats,
    filter_by_rerank_threshold,
    diversify_by_paper,
    assess_evidence_sufficiency,
)
from api.utils.reranking import CrossEncoderReranker

class SmartRetrievalService:
    """
    Service for intelligent document retrieval with quality evaluation and CORE API fallback.
    
    This service provides:
    1. Vector store similarity search
    2. Quality evaluation of results
    3. Smart fallback to CORE API extraction
    4. Result merging and optimization
    """
    
    def __init__(self):
        """Initialize smart retrieval service."""
        self.vector_store_manager = None
        self.extraction_service = DataExtractionService()
        self.collection_name = "ResearchPaper"
        self.research_domain = "General"
        
        # Quality thresholds
        self.quality_thresholds = {
            "min_quantity_ratio": 0.3,      # Minimum 30% of requested results
            "min_certainty_score": 0.7,     # Minimum certainty from Weaviate
            "min_relevance_score": 0.6,     # Minimum reranking score
            "min_recent_ratio": 0.2,        # Minimum 20% recent docs (last 2 years)
            "max_years_old": 2               # Define "recent" as last 2 years
        }
        
        # Retrieval history
        self.retrieval_history = []

        # Retrieval policy (rerank thresholds, evidence sufficiency, loop budgets)
        self.qcfg = RetrievalQualityConfig()
    
    def _initialize_vector_store(self, collection_name: str = "ResearchPaper", research_domain: str = "General"):
        """Initialize vector store manager."""
        if not self.vector_store_manager or self.collection_name != collection_name or self.research_domain != research_domain:
            self.vector_store_manager = VectorStoreManager(collection_name=collection_name, research_domain=research_domain)
            self.collection_name = collection_name
            self.research_domain = research_domain
    
    def _calculate_quality_metrics(
        self,
        results: List[Dict[str, Any]],
        query: str,
        requested_max_results: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Calculate quality metrics for retrieved results.
        
        Args:
            results: List of retrieved documents
            query: Original search query
            
        Returns:
            Dict containing quality metrics
        """
        if not results:
            return {
                "quantity_score": 0.0,
                "certainty_score": 0.0,
                "recency_score": 0.0,
                "overall_score": 0.0
            }
        
        # 1. Quantity Score (relative to requested size, if provided)
        if requested_max_results:
            quantity_score = min(1.0, len(results) / max(1, requested_max_results))
        else:
            quantity_score = 1.0
        
        # 2. Certainty Score (from Weaviate metadata)
        certainty_scores = []
        for result in results:
            metadata = result.get("metadata", {})
            certainty = metadata.get("certainty", 0.5)  # Default to 0.5 if not available
            certainty_scores.append(certainty)
        
        avg_certainty = sum(certainty_scores) / len(certainty_scores) if certainty_scores else 0.0
        
        # 3. Recency Score
        current_year = datetime.now().year
        recent_docs = 0
        for result in results:
            year = result.get("year", 0)
            if isinstance(year, str):
                try:
                    year = int(year)
                except ValueError:
                    year = 0
            
            if year >= current_year - self.quality_thresholds["max_years_old"]:
                recent_docs += 1
        
        recency_score = recent_docs / len(results) if results else 0.0
        
        # 4. Overall Score (weighted average)
        overall_score = (
            quantity_score * 0.2 +
            avg_certainty * 0.5 +
            recency_score * 0.3
        )
        
        return {
            "quantity_score": quantity_score,
            "certainty_score": avg_certainty,
            "recency_score": recency_score,
            "overall_score": overall_score,
            "total_results": len(results),
            "recent_results": recent_docs
        }
    
    def _should_fallback_to_core_api(
        self, 
        results: List[Dict[str, Any]], 
        quality_metrics: Dict[str, Any],
        query: str, 
        max_results: int
    ) -> Dict[str, Any]:
        """
        Decide if we need to fallback to CORE API.
        
        Args:
            results: Current vector store results
            quality_metrics: Quality metrics for current results
            query: Search query
            max_results: Requested number of results
            
        Returns:
            Dict containing fallback decision and reasoning
        """
        fallback_reasons = []
        should_fallback = False
        
        # 1. Quantity Check
        if len(results) < max_results * self.quality_thresholds["min_quantity_ratio"]:
            fallback_reasons.append(f"Insufficient quantity: {len(results)} < {max_results * self.quality_thresholds['min_quantity_ratio']:.1f}")
            should_fallback = True
        
        # 2. Certainty Check
        if quality_metrics["certainty_score"] < self.quality_thresholds["min_certainty_score"]:
            fallback_reasons.append(f"Low certainty: {quality_metrics['certainty_score']:.2f} < {self.quality_thresholds['min_certainty_score']}")
            should_fallback = True
        
        # 3. Recency Check
        if quality_metrics["recency_score"] < self.quality_thresholds["min_recent_ratio"]:
            fallback_reasons.append(f"Few recent docs: {quality_metrics['recency_score']:.2f} < {self.quality_thresholds['min_recent_ratio']}")
            should_fallback = True
        
        # 4. Overall Quality Check
        if quality_metrics["overall_score"] < 0.6:  # Overall quality threshold
            fallback_reasons.append(f"Low overall quality: {quality_metrics['overall_score']:.2f} < 0.6")
            should_fallback = True

        # 5. Evidence sufficiency check (rerank + unique papers)
        if quality_metrics.get("evidence_ok") is False:
            fallback_reasons.append("Insufficient relevant evidence after reranking/filters")
            should_fallback = True
        
        return {
            "should_fallback": should_fallback,
            "reasons": fallback_reasons,
            "quality_metrics": quality_metrics
        }
    
    def _merge_and_deduplicate_results(
        self, 
        original_results: List[Dict[str, Any]], 
        new_results: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Merge and deduplicate results from vector store and CORE API.
        
        Args:
            original_results: Results from initial vector search
            new_results: Results from post-extraction vector search
            
        Returns:
            Merged and deduplicated results
        """
        # Create a dict to track unique documents by DOI or title
        seen_docs = {}
        merged_results = []
        
        # Add new results first (they're fresher)
        for result in new_results:
            doi = result.get("doi", "")
            title = result.get("title", "").lower().strip()
            
            # Create unique key based on DOI or title
            key = doi if doi else title
            
            if key and key not in seen_docs:
                seen_docs[key] = True
                result["source_priority"] = "new"
                merged_results.append(result)
        
        # Add original results if not already present
        for result in original_results:
            doi = result.get("doi", "")
            title = result.get("title", "").lower().strip()
            
            key = doi if doi else title
            
            if key and key not in seen_docs:
                seen_docs[key] = True
                result["source_priority"] = "existing"
                merged_results.append(result)
        
        print(f"[DEBUG] Merged results: {len(new_results)} new + {len(original_results)} original = {len(merged_results)} unique")
        
        return merged_results
    
    async def smart_retrieve_documents(
        self, 
        query: str, 
        research_domain: str = "General", 
        max_results: int = 20,
        enable_fallback: bool = True
    ) -> Dict[str, Any]:
        """
        Smart document retrieval with quality evaluation and fallback.
        
        Args:
            query: Search query
            research_domain: Research domain/field
            max_results: Maximum number of results to return
            enable_fallback: Whether to enable CORE API fallback
            
        Returns:
            Dict containing:
                - success: bool
                - documents: List[Dict] - Retrieved documents
                - quality_metrics: Dict - Quality evaluation
                - fallback_used: bool - Whether fallback was triggered
                - fallback_info: Dict - Fallback details (if used)
                - retrieval_id: str - For tracking
                - timestamp: str
        """
        retrieval_id = str(uuid.uuid4())
        start_time = datetime.now(timezone.utc)
        
        print(f"[DEBUG] ===== SMART RETRIEVAL SERVICE =====")
        print(f"[DEBUG] Retrieval ID: {retrieval_id}")
        print(f"[DEBUG] Query: '{query}'")
        print(f"[DEBUG] Research Domain: {research_domain}")
        print(f"[DEBUG] Max Results: {max_results}")
        print(f"[DEBUG] Fallback Enabled: {enable_fallback}")
        
        try:
            # Initialize vector store
            self._initialize_vector_store(self.collection_name, research_domain)
            
            # Step 1: Initial vector store search
            print(f"[DEBUG] Step 1: Initial vector store search...")
            candidate_k = max(max_results, max_results * max(1, self.qcfg.candidate_multiplier))
            initial_candidates = self.vector_store_manager.similarity_search(query, candidate_k, research_domain)
            print(f"[DEBUG] Initial search returned {len(initial_candidates)} candidates (requested={max_results})")

            # Step 1.5: Rerank + filter by minimum relevance score
            reranker_available = CrossEncoderReranker.is_available()
            reranker_info = CrossEncoderReranker.availability_info()
            ranked = attach_rerank_scores(query, initial_candidates, top_k=len(initial_candidates))
            threshold = adaptive_rerank_threshold(ranked, self.qcfg) if reranker_available else 0.0
            filtered_candidates = filter_by_rerank_threshold(
                ranked,
                min_score=threshold,
                reranker_available=reranker_available,
                min_keep=min(self.qcfg.min_results_after_filter, max_results),
            )
            # Paper-level diversification: prioritize unique papers over many chunks from one paper
            diversified = diversify_by_paper(
                filtered_candidates,
                max_papers=max_results,
                max_chunks_per_paper=self.qcfg.max_chunks_per_paper,
            )
            initial_results = diversified[:max_results]
            print(f"[DEBUG] After rerank+filter: kept {len(initial_results)} results (min_score={threshold})")
            
            # Step 2: Evaluate quality
            print(f"[DEBUG] Step 2: Evaluating result quality...")
            quality_metrics = self._calculate_quality_metrics(initial_results, query, requested_max_results=max_results)
            print(f"[DEBUG] Quality metrics: {quality_metrics}")

            evidence_assessment = assess_evidence_sufficiency(initial_results, max_results, self.qcfg)
            quality_metrics["avg_rerank_score"] = evidence_assessment.get("avg_rerank_score", 0.0)
            quality_metrics["unique_papers"] = evidence_assessment.get("unique_papers", 0)
            quality_metrics["evidence_ok"] = evidence_assessment.get("ok", False)
            
            # Step 3: Decide on fallback
            fallback_decision = self._should_fallback_to_core_api(
                initial_results, quality_metrics, query, max_results
            )
            print(f"[DEBUG] Fallback decision: {fallback_decision}")
            
            final_results = initial_results
            fallback_info = None
            
            # Step 4: Execute fallback if needed
            if enable_fallback and fallback_decision["should_fallback"]:
                print(f"[DEBUG] Step 4: Executing CORE API fallback...")
                print(f"[DEBUG] Fallback reasons: {fallback_decision['reasons']}")
                
                # Extract new documents from CORE API
                extraction_result = await self.extraction_service.extract_and_store_documents(
                    query=query,
                    research_domain=research_domain,
                    max_results=max_results
                )
                
                if extraction_result["success"]:
                    print(f"[DEBUG] Extraction successful, re-querying vector store...")
                    
                    # Re-query vector store with higher limit to get mix of old + new
                    fresh_candidate_k = max_results * 2 * max(1, self.qcfg.candidate_multiplier)
                    fresh_candidates = self.vector_store_manager.similarity_search(query, fresh_candidate_k, research_domain)
                    print(f"[DEBUG] Fresh search returned {len(fresh_candidates)} candidates")

                    fresh_ranked = attach_rerank_scores(query, fresh_candidates, top_k=len(fresh_candidates))
                    fresh_threshold = adaptive_rerank_threshold(fresh_ranked, self.qcfg) if reranker_available else 0.0
                    fresh_filtered = filter_by_rerank_threshold(
                        fresh_ranked,
                        min_score=fresh_threshold,
                        reranker_available=reranker_available,
                        min_keep=min(self.qcfg.min_results_after_filter, max_results),
                    )
                    # Combine candidate pools and diversify by paper (avoid chunk-dominance)
                    combined = list(filtered_candidates) + list(fresh_filtered)
                    combined_ranked = attach_rerank_scores(query, combined, top_k=len(combined))
                    combined_threshold = adaptive_rerank_threshold(combined_ranked, self.qcfg) if reranker_available else 0.0
                    combined_filtered = filter_by_rerank_threshold(
                        combined_ranked,
                        min_score=combined_threshold,
                        reranker_available=reranker_available,
                        min_keep=min(self.qcfg.min_results_after_filter, max_results),
                    )
                    final_results = diversify_by_paper(
                        combined_filtered,
                        max_papers=max_results,
                        max_chunks_per_paper=self.qcfg.max_chunks_per_paper,
                    )[:max_results]
                    
                    fallback_info = {
                        "extraction_used": True,
                        "extraction_result": extraction_result,
                        "papers_fetched": extraction_result.get("papers_fetched", 0),
                        "chunks_stored": extraction_result.get("chunks_stored", 0),
                        "fresh_search_count": len(fresh_candidates),
                        "final_merged_count": len(final_results),
                        "thresholds_used": {
                            "initial": threshold,
                            "fresh": fresh_threshold,
                            "combined": combined_threshold,
                        }
                    }
                else:
                    print(f"[DEBUG] Extraction failed, using original results")
                    fallback_info = {
                        "extraction_used": False,
                        "extraction_error": extraction_result.get("error", "Unknown error"),
                        "fallback_to_original": True
                    }
            else:
                print(f"[DEBUG] No fallback needed or disabled")
                fallback_info = {
                    "extraction_used": False,
                    "reason": "Quality sufficient" if not fallback_decision["should_fallback"] else "Fallback disabled"
                }
            
            # Step 5: Final quality assessment
            final_quality_metrics = self._calculate_quality_metrics(final_results, query, requested_max_results=max_results)
            final_evidence_assessment = assess_evidence_sufficiency(final_results, max_results, self.qcfg)
            final_quality_metrics["avg_rerank_score"] = final_evidence_assessment.get("avg_rerank_score", 0.0)
            final_quality_metrics["unique_papers"] = final_evidence_assessment.get("unique_papers", 0)
            final_quality_metrics["evidence_ok"] = final_evidence_assessment.get("ok", False)

            # Debug payload to make failures explainable (especially when 0 docs are returned)
            debug = {
                "reranker": reranker_info,
                "initial": {
                    "candidate_k": candidate_k,
                    "candidates_count": len(initial_candidates),
                    "score_stats": rerank_score_stats(ranked),
                    "threshold_used": threshold,
                    "kept_after_filter": len(filtered_candidates),
                    "returned": len(initial_results),
                },
            }
            if fallback_info and fallback_info.get("extraction_used"):
                debug["fallback"] = {
                    "fresh_candidates_count": fallback_info.get("fresh_search_count", 0),
                    "thresholds_used": fallback_info.get("thresholds_used", {}),
                }
            
            # Log retrieval record
            retrieval_record = {
                "retrieval_id": retrieval_id,
                "query": query,
                "research_domain": research_domain,
                "max_results": max_results,
                "initial_count": len(initial_results),
                "final_count": len(final_results),
                "fallback_used": fallback_decision["should_fallback"] and enable_fallback,
                "quality_improved": final_quality_metrics["overall_score"] > quality_metrics["overall_score"],
                "processing_time": (datetime.now(timezone.utc) - start_time).total_seconds(),
                "timestamp": start_time.isoformat()
            }
            self.retrieval_history.append(retrieval_record)

            print(f"[DEBUG] ✅ Smart retrieval completed!")
            print(f"[DEBUG] Final results: {len(final_results)} documents")
            print(f"[DEBUG] Quality score: {final_quality_metrics['overall_score']:.2f}")

            # Debug: show a sample of the actual retrieved chunks so we can see
            # what evidence the gate is judging.
            if final_results:
                print(f"[DEBUG] Sample of retrieved documents/chunks (up to 5):")
                for idx, doc in enumerate(final_results[:5], 1):
                    title = str(doc.get("title", "Untitled"))[:120]
                    source = str(doc.get("source", "unknown"))
                    year = doc.get("year", "N/A")

                    # Content may live either at top-level 'content' or under 'metadata'
                    content = doc.get("content")
                    if not content:
                        meta = doc.get("metadata", {})
                        content = meta.get("content", "")

                    text = content or ""
                    # Rough token estimate (heuristic)
                    word_count = len(text.split())
                    approx_tokens = int(word_count * 1.3)

                    metadata = doc.get("metadata", {})
                    rerank_score = metadata.get("rerank_score")

                    preview = text[:300].replace("\n", " ")
                    print(
                        f"[DEBUG]   {idx}. '{title}' "
                        f"(source='{source}', year={year}, "
                        f"words={word_count}, ~tokens={approx_tokens}, "
                        f"rerank_score={rerank_score})"
                    )
                    print(f"[DEBUG]        Content preview: {preview}...")
            else:
                print("[DEBUG] No documents returned from vector store after filtering; "
                      "nothing to show for evidence sample.")
            
            return {
                "success": True,
                "documents": final_results,
                "quality_metrics": final_quality_metrics,
                "fallback_used": fallback_decision["should_fallback"] and enable_fallback,
                "fallback_info": fallback_info,
                "evidence_assessment": final_evidence_assessment,
                "debug": debug,
                "retrieval_id": retrieval_id,
                "query": query,
                "research_domain": research_domain,
                "processing_time_seconds": (datetime.now(timezone.utc) - start_time).total_seconds(),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            print(f"[ERROR] Smart retrieval failed: {e}")
            
            return {
                "success": False,
                "error": f"Smart retrieval failed: {str(e)}",
                "retrieval_id": retrieval_id,
                "query": query,
                "research_domain": research_domain,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
    
    def get_retrieval_stats(self) -> Dict[str, Any]:
        """Get retrieval statistics."""
        if not self.retrieval_history:
            return {
                "total_retrievals": 0,
                "fallback_usage_rate": 0.0,
                "average_quality_improvement": 0.0,
                "average_processing_time": 0.0
            }
        
        fallback_used = sum(1 for r in self.retrieval_history if r.get("fallback_used", False))
        quality_improved = sum(1 for r in self.retrieval_history if r.get("quality_improved", False))
        avg_time = sum(r.get("processing_time", 0) for r in self.retrieval_history) / len(self.retrieval_history)
        
        return {
            "total_retrievals": len(self.retrieval_history),
            "fallback_usage_rate": fallback_used / len(self.retrieval_history),
            "quality_improvement_rate": quality_improved / len(self.retrieval_history),
            "average_processing_time": avg_time,
            "last_retrieval": self.retrieval_history[-1]["timestamp"] if self.retrieval_history else None
        } 