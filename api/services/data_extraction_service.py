"""
Data Extraction Service - Handles CORE API fetching, extraction, and vector storage.
"""

import asyncio
import uuid
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
import sys
import os

# Add the parent directory to the path to import agents

from api.agents.data_extractor_agent import DataExtractorAgent

class DataExtractionService:
    """
    Service for extracting documents from external sources and storing in vector database.
    
    This service provides a clean interface for:
    1. Fetching papers from CORE API
    2. Extracting PDF content
    3. Chunking and embedding
    4. Storing in vector database
    """
    
    def __init__(self):
        """Initialize data extraction service."""
        self.data_extractor = DataExtractorAgent()
        self.extraction_history = []
    
    async def extract_and_store_documents(
        self, 
        query: str, 
        research_domain: str = "General", 
        max_results: int = 20,
        year_from: int = 2020,
        year_to: int = 2024
    ) -> Dict[str, Any]:
        """
        Complete CORE API pipeline: Fetch → Extract → Chunk → Embed → Store
        
        Args:
            query: Search query for CORE API
            research_domain: Research domain/field
            max_results: Maximum number of papers to fetch
            year_from: Start year for search
            year_to: End year for search
            
        Returns:
            Dict containing:
                - success: bool
                - papers_fetched: int
                - papers_extracted: int  
                - chunks_stored: int
                - extraction_id: str (for tracking)
                - timestamp: str
                - error: str (if failed)
        """
        extraction_id = str(uuid.uuid4())
        start_time = datetime.now(timezone.utc)
        
        print(f"[DEBUG] ===== DATA EXTRACTION SERVICE =====")
        print(f"[DEBUG] Extraction ID: {extraction_id}")
        print(f"[DEBUG] Query: '{query}'")
        print(f"[DEBUG] Research Domain: {research_domain}")
        print(f"[DEBUG] Max Results: {max_results}")
        
        try:
            # Log extraction attempt
            extraction_record = {
                "extraction_id": extraction_id,
                "query": query,
                "research_domain": research_domain,
                "max_results": max_results,
                "year_from": year_from,
                "year_to": year_to,
                "status": "running",
                "started_at": start_time.isoformat(),
                "completed_at": None,
                "error": None
            }
            self.extraction_history.append(extraction_record)
            
            # Call DataExtractorAgent
            print(f"[DEBUG] Calling DataExtractorAgent.run()...")
            extraction_result = await self.data_extractor.run(
                query=query,
                max_results=max_results,
                year_from=year_from,
                year_to=year_to,
                research_domain=research_domain
            )
            
            print(f"[DEBUG] DataExtractorAgent result: {extraction_result}")
            
            # Parse results
            papers_fetched = extraction_result.get("papers_fetched", 0)
            papers_extracted = extraction_result.get("papers_extracted", 0)
            
            # Get vector store result details
            vector_store_result = extraction_result.get("vector_store_result", {})
            chunks_stored = vector_store_result.get("chunks_stored", 0)
            
            # Update extraction record
            extraction_record.update({
                "status": "completed",
                "completed_at": datetime.now(timezone.utc).isoformat(),
                "papers_fetched": papers_fetched,
                "papers_extracted": papers_extracted,
                "chunks_stored": chunks_stored
            })
            
            print(f"[DEBUG] ✅ Extraction completed successfully!")
            print(f"[DEBUG] Papers fetched: {papers_fetched}")
            print(f"[DEBUG] Papers extracted: {papers_extracted}")
            print(f"[DEBUG] Chunks stored: {chunks_stored}")
            
            return {
                "success": True,
                "extraction_id": extraction_id,
                "papers_fetched": papers_fetched,
                "papers_extracted": papers_extracted,
                "chunks_stored": chunks_stored,
                "research_domain": research_domain,
                "query": query,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "processing_time_seconds": (datetime.now(timezone.utc) - start_time).total_seconds()
            }
            
        except Exception as e:
            print(f"[ERROR] Data extraction failed: {e}")
            
            # Update extraction record with error
            for record in self.extraction_history:
                if record["extraction_id"] == extraction_id:
                    record.update({
                        "status": "failed",
                        "completed_at": datetime.now(timezone.utc).isoformat(),
                        "error": str(e)
                    })
                    break
            
            return {
                "success": False,
                "extraction_id": extraction_id,
                "error": f"Data extraction failed: {str(e)}",
                "query": query,
                "research_domain": research_domain,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
    
    def get_extraction_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get recent extraction history.
        
        Args:
            limit: Maximum number of records to return
            
        Returns:
            List of extraction records
        """
        return self.extraction_history[-limit:] if self.extraction_history else []
    
    def get_extraction_stats(self) -> Dict[str, Any]:
        """
        Get extraction statistics.
        
        Returns:
            Dict containing extraction statistics
        """
        if not self.extraction_history:
            return {
                "total_extractions": 0,
                "successful_extractions": 0,
                "failed_extractions": 0,
                "success_rate": 0.0,
                "total_papers_fetched": 0,
                "total_chunks_stored": 0
            }
        
        successful = [r for r in self.extraction_history if r["status"] == "completed"]
        failed = [r for r in self.extraction_history if r["status"] == "failed"]
        
        total_papers = sum(r.get("papers_fetched", 0) for r in successful)
        total_chunks = sum(r.get("chunks_stored", 0) for r in successful)
        
        return {
            "total_extractions": len(self.extraction_history),
            "successful_extractions": len(successful),
            "failed_extractions": len(failed),
            "success_rate": len(successful) / len(self.extraction_history) if self.extraction_history else 0.0,
            "total_papers_fetched": total_papers,
            "total_chunks_stored": total_chunks,
            "last_extraction": self.extraction_history[-1]["started_at"] if self.extraction_history else None
        } 