import logging
from typing import List, Dict, Any, Optional
from .weaviate_client import get_weaviate_manager
from weaviate.classes.query import Filter

logger = logging.getLogger(__name__)

class VectorStoreManager:
    """
    Manages vector storage and retrieval using Weaviate only.
    """
    def __init__(self, collection_name: str = "ResearchPaper", research_domain: str = "General"):
        self.collection_name = collection_name
        self.research_domain = research_domain
        self.weaviate = get_weaviate_manager()

        # Ensure the collection exists with a vectorizer
        if self.weaviate.is_available():
            existing_collections = self.weaviate.list_collections()
            if self.collection_name not in existing_collections:
                print(f"[DEBUG] Creating collection {self.collection_name} with text2vec-openai vectorizer...")
                schema = {
                    "class": self.collection_name,
                    "description": "Academic research papers",
                    "vectorizer": "text2vec-openai",
                    "moduleConfig": {
                        "text2vec-openai": {
                            "model": "ada",
                            "type": "text"
                        }
                    },
                    "properties": [
                        {"name": "content", "dataType": ["text"]},
                        {"name": "research_domain", "dataType": ["text"]},
                        {"name": "title", "dataType": ["text"]},
                        {"name": "authors", "dataType": ["text"]},
                        {"name": "year", "dataType": ["int"]},
                        {"name": "doi", "dataType": ["text"]},
                        {"name": "source", "dataType": ["text"]},
                        {"name": "paper_id", "dataType": ["text"]},
                        {"name": "chunk_index", "dataType": ["int"]},
                    ]
                }
                self.weaviate.create_collection(self.collection_name, schema)
            # Debug print the schema after creation or if it exists
            try:
                schema = self.weaviate.get_class_schema(self.collection_name)
                print(f"[DEBUG] Current schema for {self.collection_name}: {schema}")
            except Exception as e:
                print(f"[ERROR] Could not fetch schema for {self.collection_name}: {e}")
        else:
            print(f"[ERROR] Weaviate is not available! Cannot initialize VectorStoreManager")
            raise RuntimeError("Weaviate is not available")

    def add_chunks(self, chunks: List[str], metadata_list: Optional[List[Dict[str, Any]]] = None) -> bool:
        """
        Add chunks to Weaviate only.
        metadata_list: List of dicts with metadata for each chunk (optional).
        """
        print(f"[DEBUG] VectorStoreManager.add_chunks called with {len(chunks)} chunks")
        print(f"[DEBUG] Weaviate available: {self.weaviate.is_available()}")
        
        if not self.weaviate.is_available():
            error_msg = "Weaviate is not available. Cannot store chunks."
            print(f"[ERROR] {error_msg}")
            logger.error(error_msg)
            raise RuntimeError(error_msg)
        
        try:
            print(f"[DEBUG] Preparing {len(chunks)} documents for Weaviate insertion")
            docs = []
            for i, chunk in enumerate(chunks):
                meta = metadata_list[i] if metadata_list and i < len(metadata_list) else {}
                
                # Ensure all metadata values are strings or numbers
                cleaned_meta = {}
                for key, value in meta.items():
                    if key == 'year' and value is None:
                        # Skip year if it's None, or set to 0 as fallback
                        cleaned_meta[key] = 0
                    elif key == 'chunk_index' and value is None:
                        # Skip chunk_index if it's None, or set to 0 as fallback
                        cleaned_meta[key] = 0
                    elif isinstance(value, (str, int, float, bool)):
                        cleaned_meta[key] = value
                    else:
                        cleaned_meta[key] = str(value)
                
                doc = {
                    "properties": {
                        "content": chunk,
                        "research_domain": self.research_domain,
                        **cleaned_meta
                    }
                }
                docs.append(doc)
                
                if i < 3:  # Show first 3 docs for debugging
                    print(f"[DEBUG] Doc {i}: content_length={len(chunk)}, metadata={cleaned_meta}")
            
            print(f"[DEBUG] Calling weaviate.insert_documents with {len(docs)} documents")
            print(f"[DEBUG] Collection name: {self.collection_name}")
            
            # Log the first document structure
            if docs:
                print(f"[DEBUG] First document structure: {docs[0]}")
            
            insert_result = self.weaviate.insert_documents(self.collection_name, docs)
            print(f"[DEBUG] Weaviate insert_documents returned: {insert_result}")
            
            # Verify insertion by checking collection count
            try:
                count_result = self.weaviate.client.collections.get(self.collection_name).aggregate.over_all(total_count=True)
                total_count = count_result.total_count
                print(f"[DEBUG] Collection count after insertion: {total_count}")
                
                if total_count > 0:
                    print(f"[DEBUG] ✅ Successfully inserted documents. Collection now has {total_count} documents")
                else:
                    print(f"[DEBUG] ⚠️ Insertion may have failed - collection still has 0 documents")
                    
            except Exception as count_error:
                print(f"[ERROR] Could not verify insertion count: {count_error}")
            
            logger.info(f"✅ Added {len(chunks)} chunks to Weaviate")
            return True
        except Exception as e:
            print(f"[ERROR] Failed to add chunks to Weaviate: {e}")
            print(f"[ERROR] Exception type: {type(e)}")
            import traceback
            print(f"[ERROR] Full traceback: {traceback.format_exc()}")
            logger.error(f"❌ Failed to add chunks to Weaviate: {e}")
            raise RuntimeError(f"Failed to add chunks to Weaviate: {e}")

    def similarity_search(self, query: str, top_k: int = 2, research_domain: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Retrieve similar chunks using Weaviate only.
        Returns a list of document dictionaries with metadata.
        
        Args:
            query: Search query for semantic similarity
            top_k: Maximum number of results to return
            research_domain: Optional filter by research domain
        """
        if not self.weaviate.is_available():
            error_msg = "Weaviate is not available. Cannot perform similarity search."
            print(f"[ERROR] {error_msg}")
            logger.error(error_msg)
            raise RuntimeError(error_msg)
        
        try:
            print(f"[DEBUG] Performing similarity search with query: '{query}', top_k: {top_k}, research_domain: {research_domain}")
            
            # Add research domain filter if specified
            # filters = None
            # if research_domain and research_domain.lower() != "general":
            #     filters = {
            #         "path": ["research_domain"],
            #         "operator": "Equal",
            #         "valueString": research_domain
            #     }
            #     print(f"[DEBUG] Adding research domain filter: {research_domain}")
            
            filters = None
            if research_domain and research_domain.lower() != "general":
                filters = Filter.by_property("research_domain").equal(research_domain)


            raw_results = self.weaviate.search_documents(self.collection_name, query, limit=top_k, filters=filters)
            if not raw_results:
                print(f"[DEBUG] Search returned 0 results for query='{query}' domain='{research_domain or 'None'}'")
                return []
            else:
                first_title = (raw_results[0].get("properties", {}) or {}).get("title", "")
                print(f"[DEBUG] Search returned {len(raw_results)} results. First title: {first_title}")
            
            # Transform results to expected format
            transformed_results = []
            for result in raw_results:
                properties = result.get("properties", {})
                transformed_result = {
                    "title": properties.get("title", "Unknown"),
                    "authors": properties.get("authors", "Unknown"),
                    "year": properties.get("year", "Unknown"),
                    "content": properties.get("content", ""),
                    "doi": properties.get("doi", ""),
                    "source": properties.get("source", ""),
                    "paper_id": properties.get("paper_id", ""),
                    "chunk_index": properties.get("chunk_index", 0),
                    "research_domain": properties.get("research_domain", ""),
                    "uuid": result.get("uuid", ""),
                    "metadata": result.get("metadata", {})
                }
                transformed_results.append(transformed_result)
            
            if transformed_results:
                logger.info(f"✅ Retrieved {len(transformed_results)} chunks from Weaviate")
                return transformed_results
            else:
                print(f"[DEBUG] No results found for query: '{query}' with domain filter: {research_domain}")
                return []
                
        except Exception as e:
            print(f"[ERROR] Weaviate similarity search failed: {e}")
            logger.error(f"❌ Weaviate similarity search failed: {e}")
            raise RuntimeError(f"Similarity search failed for query='{query}' domain='{research_domain or 'None'}': {e}")

    def add_document(self, document: Dict[str, Any]) -> bool:
        """
        Add a single document to Weaviate.
        
        Args:
            document: Document dictionary with properties
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Prepare document for insertion
            doc = {
                "properties": {
                    "content": document.get("content", ""),
                    "research_domain": document.get("research_domain", self.research_domain),
                    "title": document.get("title", ""),
                    "authors": document.get("authors", ""),
                    "year": document.get("year", 2024),
                    "doi": document.get("doi", ""),
                    "source": document.get("source", ""),
                    "paper_id": document.get("paper_id", ""),
                    "chunk_index": document.get("chunk_index", 0)
                }
            }
            
            # Insert document
            self.weaviate.insert_documents(self.collection_name, [doc])
            return True
            
        except Exception as e:
            print(f"[ERROR] Failed to add document: {e}")
            return False

    def list_collections(self) -> List[Dict[str, Any]]:
        """
        List all available collections in Weaviate.
        
        Returns:
            List of collection information dictionaries
        """
        try:
            # Try to get collections from Weaviate
            collections = self.weaviate.list_collections()
            collection_info = []
            
            print(f"[DEBUG] Found {len(collections)} collections: {collections}")
            
            
            # Process any collections that were found
            for collection_name in collections:
                try:
                    # Get collection details using the Weaviate client directly
                    collection = self.weaviate.client.collections.get(collection_name)
                    count_result = collection.aggregate.over_all(total_count=True)
                    total_count = count_result.total_count
                    
                    collection_info.append({
                        "name": collection_name,
                        "document_count": total_count,
                        "created_at": "Unknown",  # Weaviate doesn't provide creation date by default
                        "description": "Academic research papers"
                    })
                    print(f"[DEBUG] Collection {collection_name}: {total_count} documents")
                except Exception as e:
                    print(f"[WARNING] Could not get details for collection {collection_name}: {e}")
                    collection_info.append({
                        "name": collection_name,
                        "document_count": 0,
                        "created_at": "Unknown",
                        "description": "Academic research papers"
                    })
            
            print(f"[DEBUG] Returning {len(collection_info)} collection info items")
            return collection_info
            
        except Exception as e:
            print(f"[ERROR] Failed to list collections: {e}")
            return []

    def get_collection_info(self) -> Dict[str, Any]:
        """
        Get essential information about the current collection.
        
        Returns:
            Dictionary containing essential collection information
        """
        try:
            # Get document count
            count_result = self.weaviate.client.collections.get(self.collection_name).aggregate.over_all(total_count=True)
            total_count = count_result.total_count
            
            # Get basic schema info (just property names and types)
            try:
                schema = self.weaviate.get_class_schema(self.collection_name)
                properties = []
                if hasattr(schema, 'properties') and schema.properties:
                    properties = [
                        {
                            "name": prop.name,
                            "data_type": str(prop.data_type),
                            "index_searchable": prop.index_searchable
                        }
                        for prop in schema.properties
                    ]
            except Exception as schema_error:
                print(f"[WARNING] Could not get schema details: {schema_error}")
                properties = []
            
            return {
                "name": self.collection_name,
                "document_count": total_count,
                "research_domain": self.research_domain,
                "properties": properties,
                "created_at": "Unknown",
                "description": "Academic research papers"
            }
            
        except Exception as e:
            print(f"[ERROR] Failed to get collection info: {e}")
            return {
                "name": self.collection_name,
                "document_count": 0,
                "research_domain": self.research_domain,
                "error": str(e)
            }

    def delete_collection(self) -> bool:
        """
        Delete the current collection from Weaviate.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            self.weaviate.client.collections.delete(self.collection_name)
            print(f"[INFO] Collection {self.collection_name} deleted successfully")
            return True
            
        except Exception as e:
            print(f"[ERROR] Failed to delete collection {self.collection_name}: {e}")
            return False

    def delete_document(self, document_id: str) -> bool:
        """
        Delete a specific document from the collection.
        
        Args:
            document_id: UUID of the document to delete
            
        Returns:
            True if successful, False otherwise
        """
        try:
            self.weaviate.client.data_object.delete_by_id(document_id, self.collection_name)
            return True
            
        except Exception as e:
            print(f"[ERROR] Failed to delete document {document_id}: {e}")
            return False

    def get_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about the current collection.
        
        Returns:
            Dictionary containing collection statistics
        """
        try:
            # Get document count
            count_result = self.weaviate.client.collections.get(self.collection_name).aggregate.over_all(total_count=True)
            total_count = count_result.total_count
            
            # For now, skip research domain distribution to avoid API compatibility issues
            # TODO: Implement proper domain distribution when Weaviate API is stable
            domain_distribution = {}
            
            return {
                "total_documents": total_count,
                "collection_name": self.collection_name,
                "research_domain_distribution": domain_distribution,
                "last_updated": "Unknown"
            }
            
        except Exception as e:
            print(f"[ERROR] Failed to get statistics: {e}")
            return {
                "total_documents": 0,
                "collection_name": self.collection_name,
                "error": str(e)
            }

    def rebuild_index(self, force: bool = False) -> bool:
        """
        Rebuild the vector index for the collection.
        
        Args:
            force: Force rebuild even if index exists
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Note: Weaviate automatically manages indexes, so this is mostly a placeholder
            # In a real implementation, you might want to trigger a reindexing operation
            print(f"[INFO] Index rebuild requested for collection {self.collection_name}")
            print(f"[INFO] Weaviate automatically manages indexes - no manual rebuild needed")
            return True
            
        except Exception as e:
            print(f"[ERROR] Failed to rebuild index: {e}")
            return False

    def test_connection(self) -> bool:
        """
        Test the connection to Weaviate.
        
        Returns:
            True if connection is successful, False otherwise
        """
        try:
            # Try to list collections as a connection test
            self.weaviate.list_collections()
            return True
            
        except Exception as e:
            print(f"[ERROR] Weaviate connection test failed: {e}")
            return False 

    def get_all_documents(self, collection_name: str, limit: int = 1000) -> List[Dict[str, Any]]:
        """
        Get all documents from a specific collection.
        
        Args:
            collection_name: Name of the collection to retrieve documents from
            limit: Maximum number of documents to retrieve (default: 1000)
            
        Returns:
            List of documents with their properties and metadata
        """
        try:
            print(f"[DEBUG] Getting all documents from collection: {collection_name}")
            
            # Get all documents from the collection
            documents = self.weaviate.get_all_documents(collection_name, limit=limit)
            
            # Transform results to expected format
            transformed_results = []
            for result in documents:
                properties = result.get("properties", {})
                transformed_result = {
                    "title": properties.get("title", "Unknown"),
                    "authors": properties.get("authors", "Unknown"),
                    "year": properties.get("year", "Unknown"),
                    "content": properties.get("content", ""),
                    "doi": properties.get("doi", ""),
                    "source": properties.get("source", ""),
                    "paper_id": properties.get("paper_id", ""),
                    "chunk_index": properties.get("chunk_index", 0),
                    "research_domain": properties.get("research_domain", ""),
                    "uuid": result.get("uuid", ""),
                    "metadata": result.get("metadata", {})
                }
                transformed_results.append(transformed_result)
            
            print(f"[DEBUG] Retrieved {len(transformed_results)} documents from {collection_name}")
            return transformed_results
            
        except Exception as e:
            print(f"[ERROR] Failed to get all documents from {collection_name}: {e}")
            return [] 