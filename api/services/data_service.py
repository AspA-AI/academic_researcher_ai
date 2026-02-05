"""
Data Service - Manages document retrieval, storage, and vector database operations.
Enhanced with smart retrieval and CORE API fallback capabilities.
"""

import asyncio
import uuid
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
import sys
import os

# Add the parent directory to the path to import utils

from api.utils.vector_store_manager import VectorStoreManager
from api.utils.weaviate_client import get_weaviate_manager
from api.services.data_extraction_service import DataExtractionService
from api.services.smart_retrieval_service import SmartRetrievalService

class DataService:
    """
    Enhanced service layer for managing data operations.
    
    Provides unified interface for:
    1. Smart document retrieval with fallback
    2. Manual data extraction from CORE API
    3. Vector store operations
    4. Analytics and monitoring
    """
    
    def __init__(self):
        """Initialize data service with enhanced capabilities."""
        # Core services
        self.extraction_service = DataExtractionService()
        self.smart_retrieval_service = SmartRetrievalService()
        
        # Legacy vector store support
        self.vector_store_manager = None
        self.collection_name = "ResearchPaper"
        self.research_domain = "General"
        
        # Initialize weaviate manager for collection operations
        self.weaviate = get_weaviate_manager()
        
        # Track all operations
        self.operation_history = []
    
    def _initialize_vector_store(self, collection_name: str = "ResearchPaper", research_domain: str = "General"):
        """Initialize vector store manager for legacy operations."""
        if not self.vector_store_manager or self.collection_name != collection_name or self.research_domain != research_domain:
            self.vector_store_manager = VectorStoreManager(collection_name=collection_name, research_domain=research_domain)
            self.collection_name = collection_name
            self.research_domain = research_domain

    async def retrieve_documents(self, query: str, research_domain: str = "General", max_results: int = 10) -> Dict[str, Any]:
        """
        Enhanced document retrieval with smart fallback to CORE API.
        
        This method now:
        1. Tries vector store first
        2. Evaluates result quality
        3. Falls back to CORE API if needed
        4. Re-queries and merges results
        
        Args:
            query: Search query
            research_domain: Research domain/topic
            max_results: Maximum number of results to return
            
        Returns:
            Dict containing retrieved documents and metadata
        """
        try:
            print(f"\n" + "🔍"*50)
            print(f"🔍 ENHANCED DATA SERVICE - SMART RETRIEVAL")
            print(f"🔍"*50)
            print(f"[DATA_SERVICE]   Query: '{query}'")
            print(f"[DATA_SERVICE]   Research Domain: '{research_domain}'")
            print(f"[DATA_SERVICE]   Max Results: {max_results}")
            # Log operation
            operation_id = str(uuid.uuid4())
            self.operation_history.append({
                "operation_id": operation_id,
                "operation": "enhanced_retrieve_documents",
                "query": query,
                "research_domain": research_domain,
                "max_results": max_results,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "status": "running"
            })
            
            # Use smart retrieval service
            retrieval_result = await self.smart_retrieval_service.smart_retrieve_documents(
                query=query,
                research_domain=research_domain,
                max_results=max_results,
                # Pipeline already performs a multi-source extraction fallback.
                # Keeping this False avoids redundant (slow) nested CORE extraction calls.
                enable_fallback=False
            )
            
            print(f"[DATA_SERVICE] 📊 SmartRetrievalService response:")
            print(f"[DATA_SERVICE]   Success: {retrieval_result.get('success', False)}")
            print(f"[DATA_SERVICE]   Documents count: {len(retrieval_result.get('documents', []))}")
            print(f"[DATA_SERVICE]   Fallback used: {retrieval_result.get('fallback_used', False)}")
            if retrieval_result.get('fallback_used'):
                fallback_info = retrieval_result.get('fallback_info', {})
                print(f"[DATA_SERVICE]   📈 Fallback details:")
                print(f"[DATA_SERVICE]     Extraction used: {fallback_info.get('extraction_used', False)}")
                if fallback_info.get('extraction_used'):
                    print(f"[DATA_SERVICE]     Papers fetched: {fallback_info.get('papers_fetched', 0)}")
                    print(f"[DATA_SERVICE]     Chunks stored: {fallback_info.get('chunks_stored', 0)}")
                    print(f"[DATA_SERVICE]     Fresh search count: {fallback_info.get('fresh_search_count', 0)}")
            
            quality_metrics = retrieval_result.get('quality_metrics', {})
            print(f"[DATA_SERVICE] 🎯 Quality metrics:")
            print(f"[DATA_SERVICE]   Overall score: {quality_metrics.get('overall_score', 0.0):.2f}")
            print(f"[DATA_SERVICE]   Certainty score: {quality_metrics.get('certainty_score', 0.0):.2f}")
            print(f"[DATA_SERVICE]   Recency score: {quality_metrics.get('recency_score', 0.0):.2f}")
            print(f"[DATA_SERVICE]   Recent results: {quality_metrics.get('recent_results', 0)}")
            print(f"[DATA_SERVICE]   Evidence OK: {quality_metrics.get('evidence_ok', False)}")
            
            if not retrieval_result["success"]:
                # Update operation status
                for op in self.operation_history:
                    if op["operation_id"] == operation_id:
                        op["status"] = "failed"
                        op["error"] = retrieval_result.get("error", "Unknown error")
                        break
                
                print(f"[DATA_SERVICE] ❌ Smart retrieval failed!")
                print(f"[DATA_SERVICE]   Error: {retrieval_result.get('error', 'Unknown error')}")
                print(f"🔍"*50 + "\n")
                
                return {
                    "success": False,
                    "error": retrieval_result.get("error", "Smart retrieval failed"),
                    "operation_id": operation_id,
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
            
            documents = retrieval_result["documents"]
            
            # Update operation status with enhanced metadata
            for op in self.operation_history:
                if op["operation_id"] == operation_id:
                    op.update({
                        "status": "completed",
                        "result_count": len(documents),
                        "fallback_used": retrieval_result.get("fallback_used", False),
                        "quality_score": retrieval_result.get("quality_metrics", {}).get("overall_score", 0.0),
                        "processing_time": retrieval_result.get("processing_time_seconds", 0.0)
                    })
                    break
            
            print(f"[DATA_SERVICE] ✅ Enhanced retrieval completed successfully!")
            print(f"[DATA_SERVICE]   Final document count: {len(documents)}")
            print(f"[DATA_SERVICE]   Fallback was used: {retrieval_result.get('fallback_used', False)}")
            print(f"[DATA_SERVICE]   Final quality score: {quality_metrics.get('overall_score', 0.0):.2f}")
            print(f"[DATA_SERVICE]   Processing time: {retrieval_result.get('processing_time_seconds', 0.0):.2f}s")
            
            # Log sample document titles for verification
            if documents:
                print(f"[DATA_SERVICE] 📚 Sample retrieved documents:")
                for i, doc in enumerate(documents[:3]):
                    title = doc.get('title', 'No title')[:50] + "..." if len(doc.get('title', '')) > 50 else doc.get('title', 'No title')
                    domain = doc.get('research_domain', 'Unknown')
                    year = doc.get('year', 'Unknown')
                    source_priority = doc.get('source_priority', 'N/A')
                    print(f"[DATA_SERVICE]     {i+1}. {title}")
                    print(f"[DATA_SERVICE]        Domain: {domain}, Year: {year}, Source: {source_priority}")
                
                if len(documents) > 3:
                    print(f"[DATA_SERVICE]     ... and {len(documents) - 3} more documents")
            
            print(f"🔍"*50 + "\n")
            
            return {
                "success": True,
                "data": {
                    "documents": documents or [],
                    "query": query,
                    "research_domain": research_domain,
                    "total_count": len(documents) if documents else 0,
                    "max_results": max_results,
                    # Enhanced metadata
                    "quality_metrics": retrieval_result.get("quality_metrics", {}),
                    "fallback_used": retrieval_result.get("fallback_used", False),
                    "fallback_info": retrieval_result.get("fallback_info", {}),
                    "evidence_assessment": retrieval_result.get("evidence_assessment", {}),
                    "debug": retrieval_result.get("debug", {}),
                    "retrieval_id": retrieval_result.get("retrieval_id", ""),
                    "processing_time_seconds": retrieval_result.get("processing_time_seconds", 0.0)
                },
                "operation_id": operation_id,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            import traceback
            print(f"[DATA_SERVICE]   Traceback: {traceback.format_exc()}")
            print(f"🔍"*50 + "\n")
            
            # Update operation status
            for op in self.operation_history:
                if op["operation_id"] == operation_id:
                    op["status"] = "failed"
                    op["error"] = str(e)
                    break
            
            return {
                "success": False,
                "error": f"Document retrieval failed: {str(e)}",
                "operation_id": operation_id,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }

    async def extract_documents_from_core_api(
        self, 
        query: str, 
        research_domain: str = "General", 
        max_results: int = 20,
        year_from: int = 2020,
        year_to: int = 2024
    ) -> Dict[str, Any]:
        """
        Manual document extraction from CORE API.
        
        Use this when you specifically want to fetch fresh documents
        without the smart retrieval logic.
        
        Args:
            query: Search query for CORE API
            research_domain: Research domain/field
            max_results: Maximum number of papers to fetch
            year_from: Start year for search
            year_to: End year for search
            
        Returns:
            Dict containing extraction results
        """
        try:
            print(f"[DEBUG] ===== MANUAL CORE API EXTRACTION =====")
            print(f"[DEBUG] Query: '{query}'")
            print(f"[DEBUG] Research Domain: {research_domain}")
            
            # Log operation
            operation_id = str(uuid.uuid4())
            self.operation_history.append({
                "operation_id": operation_id,
                "operation": "manual_core_api_extraction",
                "query": query,
                "research_domain": research_domain,
                "max_results": max_results,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "status": "running"
            })
            
            # Use extraction service
            extraction_result = await self.extraction_service.extract_and_store_documents(
                query=query,
                research_domain=research_domain,
                max_results=max_results,
                year_from=year_from,
                year_to=year_to
            )
            
            # Update operation status
            for op in self.operation_history:
                if op["operation_id"] == operation_id:
                    if extraction_result["success"]:
                        op.update({
                            "status": "completed",
                            "papers_fetched": extraction_result.get("papers_fetched", 0),
                            "chunks_stored": extraction_result.get("chunks_stored", 0),
                            "processing_time": extraction_result.get("processing_time_seconds", 0.0)
                        })
                    else:
                        op.update({
                            "status": "failed",
                            "error": extraction_result.get("error", "Unknown error")
                        })
                    break
            
            return {
                "success": extraction_result["success"],
                "data": extraction_result if extraction_result["success"] else {},
                "error": extraction_result.get("error") if not extraction_result["success"] else None,
                "operation_id": operation_id,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            print(f"[ERROR] Manual extraction failed: {e}")
            
            # Update operation status
            for op in self.operation_history:
                if op["operation_id"] == operation_id:
                    op["status"] = "failed"
                    op["error"] = str(e)
                    break
            
            return {
                "success": False,
                "error": f"Manual extraction failed: {str(e)}",
                "operation_id": operation_id,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }

    async def legacy_retrieve_documents(self, query: str, research_domain: str = "General", max_results: int = 10) -> Dict[str, Any]:
        """
        Legacy document retrieval (vector store only, no fallback).
        
        This is the old behavior - only searches existing vector store.
        Kept for backward compatibility.
        
        Args:
            query: Search query
            research_domain: Research domain/topic
            max_results: Maximum number of results to return
            
        Returns:
            Dict containing retrieved documents and metadata
        """
        try:
            self._initialize_vector_store(self.collection_name, research_domain)
            
            # Log operation
            operation_id = str(uuid.uuid4())
            self.operation_history.append({
                "operation_id": operation_id,
                "operation": "legacy_retrieve_documents",
                "query": query,
                "research_domain": research_domain,
                "max_results": max_results,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "status": "running"
            })
            
            # Perform legacy retrieval using similarity search only
            documents = self.vector_store_manager.similarity_search(query, max_results)
            
            # Update operation status
            for op in self.operation_history:
                if op["operation_id"] == operation_id:
                    op["status"] = "completed"
                    op["result_count"] = len(documents) if documents else 0
                    break
            
            return {
                "success": True,
                "data": {
                    "documents": documents or [],
                    "query": query,
                    "research_domain": research_domain,
                    "total_count": len(documents) if documents else 0,
                    "max_results": max_results,
                    "method": "legacy_vector_store_only"
                },
                "operation_id": operation_id,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            print(f"[ERROR] Legacy document retrieval failed: {e}")
            
            # Update operation status
            for op in self.operation_history:
                if op["operation_id"] == operation_id:
                    op["status"] = "failed"
                    op["error"] = str(e)
                    break
            
            return {
                "success": False,
                "error": f"Legacy document retrieval failed: {str(e)}",
                "operation_id": operation_id,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }

    def get_service_stats(self) -> Dict[str, Any]:
        """
        Get comprehensive service statistics.
        
        Returns:
            Dict containing service statistics from all components
        """
        # Get stats from sub-services
        extraction_stats = self.extraction_service.get_extraction_stats()
        retrieval_stats = self.smart_retrieval_service.get_retrieval_stats()
        
        # Calculate operation stats
        if self.operation_history:
            successful_ops = [op for op in self.operation_history if op.get("status") == "completed"]
            failed_ops = [op for op in self.operation_history if op.get("status") == "failed"]
            
            operation_stats = {
                "total_operations": len(self.operation_history),
                "successful_operations": len(successful_ops),
                "failed_operations": len(failed_ops),
                "success_rate": len(successful_ops) / len(self.operation_history),
                "last_operation": self.operation_history[-1]["timestamp"]
            }
        else:
            operation_stats = {
                "total_operations": 0,
                "successful_operations": 0,
                "failed_operations": 0,
                "success_rate": 0.0,
                "last_operation": None
            }
        
        return {
            "service_overview": operation_stats,
            "extraction_service": extraction_stats,
            "smart_retrieval_service": retrieval_stats,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

    def get_operation_history(self, limit: int = 20, operation_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get recent operation history.
        
        Args:
            limit: Maximum number of operations to return
            operation_type: Optional filter by operation type
            
        Returns:
            List of operation records
        """
        history = self.operation_history[-limit:] if self.operation_history else []
        
        # Filter by operation type if specified
        if operation_type:
            history = [op for op in history if op.get("operation") == operation_type]
        
        return history

    # ===== WEAVIATE DIRECT OPERATIONS =====
    
    async def store_documents(self, documents: List[Dict[str, Any]], research_domain: str = "General", collection_name: str = "ResearchPaper") -> Dict[str, Any]:
        """
        Store documents directly in Weaviate vector database.
        
        Args:
            documents: List of documents to store
            research_domain: Research domain for the documents
            collection_name: Name of the collection to store in
            
        Returns:
            Dict containing storage results
        """
        try:
            print(f"[DATA_SERVICE] 📥 Storing {len(documents)} documents in Weaviate...")
            
            # Initialize vector store
            self._initialize_vector_store(collection_name, research_domain)
            
            # Log operation
            operation_id = str(uuid.uuid4())
            self.operation_history.append({
                "operation_id": operation_id,
                "operation": "store_documents",
                "document_count": len(documents),
                "collection_name": collection_name,
                "research_domain": research_domain,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "status": "running"
            })
            
            # Store documents using vector store manager
            stored_count = 0
            for doc in documents:
                try:
                    # Prepare document for storage
                    doc_data = {
                        "content": doc.get("content", doc.get("abstract", "")),
                        "title": doc.get("title", ""),
                        "authors": doc.get("authors", ""),
                        "year": doc.get("year", 2024),
                        "doi": doc.get("doi", ""),
                        "source": doc.get("source", ""),
                        "paper_id": doc.get("paper_id", doc.get("doi", "")),
                        "chunk_index": doc.get("chunk_index", 0),
                        "research_domain": research_domain
                    }
                    
                    # Store in vector database
                    self.vector_store_manager.add_document(doc_data)
                    stored_count += 1
                    
                except Exception as e:
                    print(f"[DATA_SERVICE] ⚠️ Failed to store document {doc.get('title', 'Unknown')}: {e}")
                    continue
            
            # Update operation status
            for op in self.operation_history:
                if op["operation_id"] == operation_id:
                    op.update({
                        "status": "completed",
                        "stored_count": stored_count,
                        "failed_count": len(documents) - stored_count
                    })
                    break
            
            print(f"[DATA_SERVICE] ✅ Stored {stored_count}/{len(documents)} documents successfully")
            
            return {
                "success": True,
                "data": {
                    "stored_count": stored_count,
                    "total_documents": len(documents),
                    "failed_count": len(documents) - stored_count,
                    "collection_name": collection_name,
                    "research_domain": research_domain
                },
                "operation_id": operation_id,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            print(f"[DATA_SERVICE] ❌ Document storage failed: {e}")
            
            # Update operation status
            for op in self.operation_history:
                if op["operation_id"] == operation_id:
                    op["status"] = "failed"
                    op["error"] = str(e)
                    break
            
            return {
                "success": False,
                "error": f"Document storage failed: {str(e)}",
                "operation_id": operation_id,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }

    def list_collections(self) -> Dict[str, Any]:
        """
        List all available Weaviate collections.
        
        Returns:
            Dict containing collection information
        """
        try:
            print(f"[DATA_SERVICE] 📋 Listing Weaviate collections...")
            
            # Initialize vector store to get Weaviate client
            self._initialize_vector_store()
            
            # Get collections from Weaviate
            collections = self.vector_store_manager.list_collections()
            
            print(f"[DATA_SERVICE] ✅ Found {len(collections)} collections")
            
            return {
                "success": True,
                "data": {
                    "collections": collections,
                    "total_collections": len(collections)
                },
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            print(f"[DATA_SERVICE] ❌ Failed to list collections: {e}")
            return {
                "success": False,
                "error": f"Failed to list collections: {str(e)}",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }

    def get_collection_info(self, collection_name: str) -> Dict[str, Any]:
        """
        Get detailed information about a specific collection.
        
        Args:
            collection_name: Name of the collection
            
        Returns:
            Dict containing collection details
        """
        try:
            print(f"[DATA_SERVICE] 📊 Getting info for collection: {collection_name}")
            
            # Initialize vector store
            self._initialize_vector_store(collection_name)
            
            # Get collection info from Weaviate
            collection_info = self.vector_store_manager.get_collection_info()
            
            print(f"[DATA_SERVICE] ✅ Retrieved collection info")
            
            return {
                "success": True,
                "data": collection_info,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            print(f"[DATA_SERVICE] ❌ Failed to get collection info: {e}")
            return {
                "success": False,
                "error": f"Failed to get collection info: {str(e)}",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }

    def delete_collection(self, collection_name: str) -> Dict[str, Any]:
        """
        Delete a collection from Weaviate.
        
        Args:
            collection_name: Name of the collection to delete
            
        Returns:
            Dict containing deletion results
        """
        try:
            print(f"[DATA_SERVICE] 🗑️ Deleting collection: {collection_name}")
            
            # Initialize vector store
            self._initialize_vector_store(collection_name)
            
            # Delete collection from Weaviate
            self.vector_store_manager.delete_collection()
            
            print(f"[DATA_SERVICE] ✅ Collection {collection_name} deleted successfully")
            
            return {
                "success": True,
                "data": {
                    "collection_name": collection_name,
                    "deleted": True
                },
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            print(f"[DATA_SERVICE] ❌ Failed to delete collection: {e}")
            return {
                "success": False,
                "error": f"Failed to delete collection: {str(e)}",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }

    def delete_documents(self, document_ids: List[str], collection_name: str = "ResearchPaper") -> Dict[str, Any]:
        """
        Delete specific documents from a collection.
        
        Args:
            document_ids: List of document IDs to delete
            collection_name: Name of the collection
            
        Returns:
            Dict containing deletion results
        """
        try:
            print(f"[DATA_SERVICE] 🗑️ Deleting {len(document_ids)} documents from {collection_name}")
            
            # Initialize vector store
            self._initialize_vector_store(collection_name)
            
            # Delete documents from Weaviate
            deleted_count = 0
            for doc_id in document_ids:
                try:
                    self.vector_store_manager.delete_document(doc_id)
                    deleted_count += 1
                except Exception as e:
                    print(f"[DATA_SERVICE] ⚠️ Failed to delete document {doc_id}: {e}")
                    continue
            
            print(f"[DATA_SERVICE] ✅ Deleted {deleted_count}/{len(document_ids)} documents")
            
            return {
                "success": True,
                "data": {
                    "deleted_count": deleted_count,
                    "total_requested": len(document_ids),
                    "failed_count": len(document_ids) - deleted_count,
                    "collection_name": collection_name
                },
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            print(f"[DATA_SERVICE] ❌ Failed to delete documents: {e}")
            return {
                "success": False,
                "error": f"Failed to delete documents: {str(e)}",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }

    def get_data_statistics(self, collection_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Get comprehensive data statistics.
        
        Args:
            collection_name: Optional collection filter
            
        Returns:
            Dict containing data statistics
        """
        try:
            print(f"[DATA_SERVICE] 📊 Getting data statistics...")
            
            # Get statistics without creating collections
            if collection_name:
                # Check if collection exists first
                existing_collections = self.weaviate.list_collections()
                if collection_name not in existing_collections:
                    return {
                        "success": False,
                        "error": f"Collection '{collection_name}' does not exist",
                        "timestamp": datetime.now(timezone.utc).isoformat()
                    }
                
                # Only initialize if collection exists
                self._initialize_vector_store(collection_name, "General")
                stats = self.vector_store_manager.get_statistics()
            else:
                # Get overall statistics without specific collection
                stats = {
                    "total_documents": 0,
                    "collection_name": "overall",
                    "research_domain_distribution": {},
                    "last_updated": "Unknown"
                }
            
            # Return only essential statistics
            combined_stats = {
                "collection_name": stats.get("collection_name", collection_name or "overall"),
                "total_documents": stats.get("total_documents", 0),
                "last_updated": stats.get("last_updated", "Unknown")
            }
            
            print(f"[DATA_SERVICE] ✅ Retrieved data statistics")
            
            return {
                "success": True,
                "data": combined_stats,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            print(f"[DATA_SERVICE] ❌ Failed to get data statistics: {e}")
            return {
                "success": False,
                "error": f"Failed to get data statistics: {str(e)}",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }

    async def find_similar_documents(self, query: Optional[str] = None, documents: Optional[List[Dict[str, Any]]] = None, 
                                   research_domain: str = "General", max_results: int = 10, 
                                   similarity_threshold: float = 0.7) -> Dict[str, Any]:
        """
        Find documents similar to a given query or document.
        
        Args:
            query: Search query
            documents: Reference documents for similarity search
            research_domain: Research domain filter
            max_results: Maximum number of results
            similarity_threshold: Minimum similarity threshold
            
        Returns:
            Dict containing similar documents
        """
        try:
            print(f"[DATA_SERVICE] 🔍 Finding similar documents...")
            
            # Initialize vector store
            self._initialize_vector_store(self.collection_name, research_domain)
            
            # Log operation
            operation_id = str(uuid.uuid4())
            self.operation_history.append({
                "operation_id": operation_id,
                "operation": "find_similar_documents",
                "query": query,
                "document_count": len(documents) if documents else 0,
                "research_domain": research_domain,
                "max_results": max_results,
                "similarity_threshold": similarity_threshold,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "status": "running"
            })
            
            # Perform similarity search
            if query:
                similar_docs = self.vector_store_manager.similarity_search(query, max_results)
            elif documents:
                # Use first document as reference
                ref_doc = documents[0]
                similar_docs = self.vector_store_manager.similarity_search(
                    ref_doc.get("content", ""), max_results
                )
            else:
                raise ValueError("Either query or documents must be provided")
            
            # Filter by similarity threshold
            filtered_docs = []
            for doc in similar_docs:
                if doc.get("metadata", {}).get("certainty", 0) >= similarity_threshold:
                    filtered_docs.append(doc)
            
            # Update operation status
            for op in self.operation_history:
                if op["operation_id"] == operation_id:
                    op.update({
                        "status": "completed",
                        "result_count": len(filtered_docs),
                        "total_found": len(similar_docs)
                    })
                    break
            
            print(f"[DATA_SERVICE] ✅ Found {len(filtered_docs)} similar documents")
            
            return {
                "success": True,
                "data": {
                    "similar_documents": filtered_docs,
                    "total_found": len(similar_docs),
                    "filtered_count": len(filtered_docs),
                    "similarity_threshold": similarity_threshold,
                    "query": query,
                    "research_domain": research_domain
                },
                "operation_id": operation_id,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            print(f"[DATA_SERVICE] ❌ Similarity search failed: {e}")
            
            # Update operation status
            for op in self.operation_history:
                if op["operation_id"] == operation_id:
                    op["status"] = "failed"
                    op["error"] = str(e)
                    break
            
            return {
                "success": False,
                "error": f"Similarity search failed: {str(e)}",
                "operation_id": operation_id,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }

    async def rebuild_index(self, collection_name: str, force: bool = False) -> Dict[str, Any]:
        """
        Rebuild the vector index for a collection.
        
        Args:
            collection_name: Name of the collection
            force: Force rebuild even if index exists
            
        Returns:
            Dict containing rebuild results
        """
        try:
            print(f"[DATA_SERVICE] 🔧 Rebuilding index for collection: {collection_name}")
            
            # Initialize vector store
            self._initialize_vector_store(collection_name)
            
            # Log operation
            operation_id = str(uuid.uuid4())
            self.operation_history.append({
                "operation_id": operation_id,
                "operation": "rebuild_index",
                "collection_name": collection_name,
                "force": force,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "status": "running"
            })
            
            # Rebuild index using vector store manager
            self.vector_store_manager.rebuild_index(force=force)
            
            # Update operation status
            for op in self.operation_history:
                if op["operation_id"] == operation_id:
                    op["status"] = "completed"
                    break
            
            print(f"[DATA_SERVICE] ✅ Index rebuilt successfully")
            
            return {
                "success": True,
                "data": {
                    "collection_name": collection_name,
                    "index_rebuilt": True,
                    "force_rebuild": force
                },
                "operation_id": operation_id,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            print(f"[DATA_SERVICE] ❌ Index rebuild failed: {e}")
            
            # Update operation status
            for op in self.operation_history:
                if op["operation_id"] == operation_id:
                    op["status"] = "failed"
                    op["error"] = str(e)
                    break
            
            return {
                "success": False,
                "error": f"Index rebuild failed: {str(e)}",
                "operation_id": operation_id,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }

    def get_health_status(self) -> Dict[str, Any]:
        """
        Get the health status of the data service.
        
        Returns:
            Dict containing health information
        """
        try:
            print(f"[DATA_SERVICE] 🏥 Checking data service health...")
            
            # Initialize vector store to test connection
            self._initialize_vector_store()
            
            # Test Weaviate connection
            connection_status = self.vector_store_manager.test_connection()
            
            # Get service stats
            service_stats = self.get_service_stats()
            
            health_status = {
                "status": "healthy" if connection_status else "unhealthy",
                "weaviate_connection": connection_status,
                "service_stats": service_stats,
                "last_check": datetime.now(timezone.utc).isoformat()
            }
            
            print(f"[DATA_SERVICE] ✅ Health check completed: {health_status['status']}")
            
            return {
                "success": True,
                "data": health_status,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            print(f"[DATA_SERVICE] ❌ Health check failed: {e}")
            return {
                "success": False,
                "error": f"Health check failed: {str(e)}",
                "timestamp": datetime.now(timezone.utc).isoformat()
            } 

    async def retrieve_all_documents(self, collection_name: str) -> Dict[str, Any]:
        """
        Retrieve all documents from a specific collection.
        
        Args:
            collection_name: Name of the collection to retrieve documents from
            
        Returns:
            Dict containing all documents from the collection
        """
        try:
            print(f"[DATA_SERVICE] 📥 Retrieving all documents from collection: {collection_name}")
            
            # Check if collection exists
            existing_collections = self.weaviate.list_collections()
            if collection_name not in existing_collections:
                return {
                    "success": False,
                    "error": f"Collection '{collection_name}' does not exist",
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
            
            # Initialize vector store for the specific collection
            self._initialize_vector_store(collection_name, "General")
            
            # Get all documents from the collection
            documents = self.vector_store_manager.get_all_documents(collection_name)
            
            print(f"[DATA_SERVICE] ✅ Retrieved {len(documents)} documents from {collection_name}")
            
            return {
                "success": True,
                "data": {
                    "collection_name": collection_name,
                    "total_documents": len(documents),
                    "documents": documents
                },
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            print(f"[DATA_SERVICE] ❌ Failed to retrieve documents: {e}")
            return {
                "success": False,
                "error": f"Failed to retrieve documents: {str(e)}",
                "timestamp": datetime.now(timezone.utc).isoformat()
            } 