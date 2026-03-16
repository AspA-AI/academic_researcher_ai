"""
Weaviate Client Module
Comprehensive Weaviate vector database operations for the research assistant
"""

import os
import logging
from typing import Dict, List, Any, Optional, Union
from datetime import datetime, timezone
import weaviate
from weaviate import WeaviateClient
from weaviate.classes.config import Configure
from weaviate.classes.init import Auth
from weaviate.classes.query import Filter, MetadataQuery
import json
from dotenv import load_dotenv
from pathlib import Path
from api.core.config import settings


# Load env from JSON file (local dev) or use os.environ (Render, Docker, etc.)
# json_env_path = os.path.join(os.path.dirname(__file__), '../.env/vars.json')
# if os.path.exists(json_env_path):
#     with open(json_env_path) as f:
#         env_vars = json.load(f)
#     for k, v in env_vars.items():
#         if v:
#             os.environ[k] = str(v)
# When JSON not found: use platform env vars (Render, Docker, etc.) - no warning needed

logger = logging.getLogger(__name__)

class WeaviateManager:
    """Modular Weaviate client manager for research assistant"""
    
    def __init__(self, url: str = None, api_key: str = None):
        """Initialize Weaviate client"""
        if not settings.CORE_API_KEY:
            print("OPENAI_API_KEY is not set. OpenAI features will not work.")
            print(settings.CORE_API_KEY)
            print("--------------------------------")
            print(settings.WEAVIATE_API_KEY)
            print("--------------------------------")
        self.url = url or settings.WEAVIATE_URL
        self.api_key = api_key or settings.WEAVIATE_API_KEY
        self.client: Optional[WeaviateClient] = None
        self.is_connected = False
        
        if not self.url or not self.api_key:
            logger.warning("Weaviate credentials not provided")
            return
        
        self._connect()

    def _ensure_filters(self, raw_filters: Any):
        """
        Convert legacy dict filters to Weaviate Filter object when needed.
        Accepts:
          - None
          - already-built Filter/Filters object
          - dict in {"path": [..], "operator": "Equal", "valueString"|valueInt|...}
        Returns a Filters-compatible object or None.
        """
        if raw_filters is None:
            return None
        # If this already looks like a Filters object, pass through
        # Weaviate v4 uses Filter/Filters builder objects (no stable duck-type across versions),
        # so we accept anything whose class name starts with "Filter".
        cls_name = getattr(raw_filters, "__class__", type(raw_filters)).__name__
        cls_name_norm = str(cls_name).lstrip("_").lower()
        if (
            hasattr(raw_filters, "to_dict")
            or cls_name.endswith("Filters")
            or cls_name_norm.startswith("filter")
            or "filter" in cls_name_norm
        ):
            return raw_filters
        # Map simple dict to Filter
        if isinstance(raw_filters, dict):
            try:
                path = raw_filters.get("path") or raw_filters.get("paths")
                if isinstance(path, list) and path:
                    prop = path[-1]
                elif isinstance(path, str):
                    prop = path
                else:
                    return None
                operator = (raw_filters.get("operator") or "").lower()
                # Value resolution
                if "valueString" in raw_filters:
                    value = raw_filters.get("valueString")
                elif "valueText" in raw_filters:
                    value = raw_filters.get("valueText")
                elif "valueInt" in raw_filters:
                    value = raw_filters.get("valueInt")
                elif "valueNumber" in raw_filters:
                    value = raw_filters.get("valueNumber")
                elif "valueBoolean" in raw_filters:
                    value = raw_filters.get("valueBoolean")
                else:
                    value = None
                # For v3.x, we'll return a dict filter that Weaviate can handle
                if operator in ("equal", "eq"):
                    return {"path": [prop], "operator": "Equal", "valueString": str(value) if value is not None else ""}
                if operator in ("notequal", "ne"):
                    return {"path": [prop], "operator": "NotEqual", "valueString": str(value) if value is not None else ""}
                if operator in ("greaterthan", "gt"):
                    return {"path": [prop], "operator": "GreaterThan", "valueNumber": value if isinstance(value, (int, float)) else None}
                if operator in ("lessthan", "lt"):
                    return {"path": [prop], "operator": "LessThan", "valueNumber": value if isinstance(value, (int, float)) else None}
                if operator in ("like",):
                    return {"path": [prop], "operator": "Like", "valueString": str(value) if value is not None else ""}
                # Fallback to equality
                return {"path": [prop], "operator": "Equal", "valueString": str(value) if value is not None else ""}
            except Exception as _:
                return None
        return None
    
    def _connect(self) -> bool:
        """Establish connection to Weaviate with retry logic"""
        max_retries = 3
        retry_delay = 2  # seconds
        
        for attempt in range(max_retries):
            try:
                logger.info(f"Connecting to Weaviate at {self.url} (attempt {attempt + 1}/{max_retries})")
                print(f"[DEBUG] Weaviate URL: {self.url}")
                print(f"[DEBUG] Weaviate API key found: {bool(self.api_key)}")
                openai_key = os.getenv("OPENAI_API_KEY", "")
                masked_key = openai_key[:4] + "..." + openai_key[-4:] if openai_key else "<not set>"
                print(f"[DEBUG] OPENAI_API_KEY env: {masked_key}")
                
                # Create client with authentication using the new method
                self.client = weaviate.connect_to_weaviate_cloud(
                    cluster_url=self.url,
                    auth_credentials=Auth.api_key(self.api_key),
                    headers={
                        "X-OpenAI-Api-Key": openai_key
                    },
                    skip_init_checks=True
                )
                print(f"[DEBUG] Client object after connect: {self.client}")
                if self.client is not None:
                    self.is_connected = True
                    logger.info("✅ Successfully connected to Weaviate")
                    print("[DEBUG] Successfully connected to Weaviate (skip_init_checks=True)")
                    return True
                else:
                    self.is_connected = False
                    print("[ERROR] Weaviate client creation returned None!")
                    return False
                    
            except Exception as e:
                logger.error(f"❌ Failed to connect to Weaviate (attempt {attempt + 1}): {e}")
                print(f"[ERROR] Failed to connect to Weaviate (attempt {attempt + 1}): {e}")
                self.is_connected = False
                self.client = None
                
                if attempt < max_retries - 1:
                    print(f"[DEBUG] Retrying in {retry_delay} seconds...")
                    import time
                    time.sleep(retry_delay)
                    retry_delay *= 2  # Exponential backoff
                else:
                    print(f"[ERROR] All {max_retries} connection attempts failed")
                    return False
        
        return False
    
    def is_available(self) -> bool:
        """Check if Weaviate is available and connected"""
        return self.is_connected and self.client is not None
    
    def get_available_modules(self) -> Dict[str, Any]:
        """Get available modules for this Weaviate instance"""
        if not self.is_available():
            logger.error("Weaviate client not available")
            return {}
        
        try:
            logger.info("Getting available modules")
            meta = self.client.get_meta()
            modules = meta.get('modules', {})
            logger.info(f"✅ Available modules: {list(modules.keys())}")
            return modules
        except Exception as e:
            logger.error(f"❌ Failed to get modules: {e}")
            return {}
    
    # ==================== COLLECTION MANAGEMENT ====================
    
    def create_collection(self, collection_name: str, schema: Dict[str, Any]) -> bool:
        """Create a new collection with schema"""
        if not self.is_available():
            logger.error("Weaviate client not available")
            return False
        
        try:
            logger.info(f"Creating collection: {collection_name}")
            
            # Check if collection already exists
            if self.client.collections.exists(collection_name):
                logger.info(f"Collection {collection_name} already exists")
                return True
            
            # Update schema with the collection name
            schema["class"] = collection_name
            
            # Create collection using the schema directly
            self.client.collections.create_from_dict(schema)
            
            logger.info(f"✅ Collection {collection_name} created successfully")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to create collection {collection_name}: {e}")
            return False
    
    def delete_collection(self, collection_name: str) -> bool:
        """Delete a collection"""
        if not self.is_available():
            logger.error("Weaviate client not available")
            return False
        
        try:
            logger.info(f"Deleting collection: {collection_name}")
            
            if self.client.collections.exists(collection_name):
                self.client.collections.delete(collection_name)
                logger.info(f"✅ Collection {collection_name} deleted successfully")
            else:
                logger.warning(f"Collection {collection_name} does not exist")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to delete collection {collection_name}: {e}")
            return False
    
    def list_collections(self) -> List[str]:
        """List all collections"""
        if not self.is_available():
            logger.error("Weaviate client not available")
            return []
        
        try:
            logger.info("Listing all collections")
            
            # Use REST API as primary method since Python client's list_all() is unreliable
            try:
                import requests
                full_url = f"https://{self.url}/v1/schema"
                response = requests.get(full_url, headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                })
                if response.status_code == 200:
                    schema_data = response.json()
                    if 'classes' in schema_data:
                        collection_names = [cls['class'] for cls in schema_data['classes']]
                        print(f"[DEBUG] Found collections via REST API: {collection_names}")
                        logger.info(f"✅ Found {len(collection_names)} collections via REST API")
                        return collection_names
                    else:
                        print(f"[DEBUG] No 'classes' in REST API response: {schema_data}")
                else:
                    print(f"[DEBUG] REST API failed with status {response.status_code}: {response.text}")
            except Exception as rest_error:
                print(f"[DEBUG] REST API method failed: {rest_error}")
            
            # Fallback to Python client method (though it's unreliable)
            print("[DEBUG] Falling back to Python client method...")
            collections = self.client.collections.list_all()
            print(f"[DEBUG] Raw collections from list_all(): {collections}")
            print(f"[DEBUG] Type of collections: {type(collections)}")
            
            # Handle both string and object responses
            if collections and hasattr(collections[0], 'name'):
                collection_names = [col.name for col in collections]
            else:
                collection_names = list(collections) if isinstance(collections, (list, tuple)) else []
            
            print(f"[DEBUG] Processed collection names: {collection_names}")
            logger.info(f"✅ Found {len(collection_names)} collections via Python client")
            return collection_names
            
        except Exception as e:
            logger.error(f"❌ Failed to list collections: {e}")
            return []
    
    def get_collection_info(self, collection_name: str) -> Dict[str, Any]:
        """Get collection information"""
        if not self.is_available():
            logger.error("Weaviate client not available")
            return {}
        
        try:
            logger.info(f"Getting info for collection: {collection_name}")
            
            if not self.client.collections.exists(collection_name):
                logger.warning(f"Collection {collection_name} does not exist")
                return {}
            
            collection = self.client.collections.get(collection_name)
            
            # Get collection configuration
            config = collection.config.get()
            
            # Get collection statistics
            stats = collection.aggregate.over_all()
            
            info = {
                "name": collection_name,
                "exists": True,
                "properties": config.properties if hasattr(config, 'properties') else [],
                "vectorizer": config.vectorizer if hasattr(config, 'vectorizer') else None,
                "total_objects": stats.total if hasattr(stats, 'total') else 0,
                "created_at": datetime.now(timezone.utc).isoformat()
            }
            
            logger.info(f"✅ Collection info retrieved: {info['total_objects']} objects")
            return info
            
        except Exception as e:
            logger.error(f"❌ Failed to get collection info: {e}")
            return {}
    
    # ==================== BASIC CRUD OPERATIONS ====================
    
    def insert_documents(self, collection_name: str, documents: List[Dict[str, Any]]) -> bool:
        """Insert documents into collection"""
        print(f"[DEBUG] WeaviateManager.insert_documents called with {len(documents)} documents")
        print(f"[DEBUG] Collection name: {collection_name}")
        print(f"[DEBUG] Weaviate available: {self.is_available()}")
        
        if not self.is_available():
            print(f"[ERROR] Weaviate client not available")
            logger.error("Weaviate client not available")
            return False
        
        try:
            print(f"[DEBUG] Getting collection: {collection_name}")
            collection = self.client.collections.get(collection_name)
            print(f"[DEBUG] Collection retrieved successfully")
            
            logger.info(f"Inserting {len(documents)} documents into {collection_name}")
            print(f"[DEBUG] Inserting {len(documents)} documents in batches...")
            
            # Insert documents in batches
            batch_size = 100
            total_inserted = 0
            for i in range(0, len(documents), batch_size):
                batch = documents[i:i + batch_size]
                print(f"[DEBUG] Processing batch {i//batch_size + 1}: {len(batch)} documents")
                
                with collection.batch.dynamic() as batch_inserter:
                    for j, doc in enumerate(batch):
                        if j < 3:  # Show first 3 docs in each batch for debugging
                            print(f"[DEBUG] Batch doc {j}: properties={list(doc.get('properties', {}).keys())}")
                        batch_inserter.add_object(
                            properties=doc.get("properties", {}),
                            uuid=doc.get("uuid", None)
                        )
                        total_inserted += 1
            
            print(f"[DEBUG] Total documents processed: {total_inserted}")
            logger.info(f"✅ Successfully inserted {len(documents)} documents")
            print(f"[DEBUG] ✅ Successfully inserted {len(documents)} documents")
            return True
            
        except Exception as e:
            print(f"[ERROR] Failed to insert documents: {e}")
            logger.error(f"❌ Failed to insert documents: {e}")
            return False
    
    def insert_single_document(self, collection_name: str, document: Dict[str, Any]) -> Optional[str]:
        """Insert a single document and return its UUID"""
        if not self.is_available():
            logger.error("Weaviate client not available")
            return None
        
        try:
            logger.info(f"Inserting single document into {collection_name}")
            print(f"[DEBUG] Inserting document with properties: {list(document.get('properties', {}).keys())}")
            
            collection = self.client.collections.get(collection_name)
            
            result = collection.data.insert(
                properties=document.get("properties", {}),
                uuid=document.get("uuid", None)
            )
            
            print(f"[DEBUG] Insert result type: {type(result)}")
            print(f"[DEBUG] Insert result value: {result}")
            
            if result is None or result == "":
                logger.error("❌ Document insertion returned None or empty value")
                return None
            
            logger.info(f"✅ Document inserted successfully with UUID: {result}")
            return result
            
        except Exception as e:
            logger.error(f"❌ Failed to insert document: {e}")
            print(f"[ERROR] Insert document exception: {e}")
            import traceback
            print(f"[ERROR] Insert document traceback: {traceback.format_exc()}")
            return None
    
    def update_document(self, collection_name: str, uuid: str, properties: Dict[str, Any]) -> bool:
        """Update a document in collection"""
        if not self.is_available():
            logger.error("Weaviate client not available")
            return False
        
        try:
            logger.info(f"Updating document {uuid} in {collection_name}")
            
            collection = self.client.collections.get(collection_name)
            
            # Update document
            collection.data.update(
                uuid=uuid,
                properties=properties
            )
            
            logger.info(f"✅ Document {uuid} updated successfully")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to update document {uuid}: {e}")
            return False
    
    def replace_document(self, collection_name: str, uuid: str, properties: Dict[str, Any]) -> bool:
        """Replace a document in collection (PUT operation)"""
        if not self.is_available():
            logger.error("Weaviate client not available")
            return False
        
        try:
            logger.info(f"Replacing document {uuid} in {collection_name}")
            
            collection = self.client.collections.get(collection_name)
            
            # Replace document
            collection.data.replace(
                uuid=uuid,
                properties=properties
            )
            
            logger.info(f"✅ Document {uuid} replaced successfully")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to replace document {uuid}: {e}")
            return False
    
    def delete_document(self, collection_name: str, uuid: str) -> bool:
        """Delete a document from collection"""
        if not self.is_available():
            logger.error("Weaviate client not available")
            return False
        
        try:
            logger.info(f"Deleting document {uuid} from {collection_name}")
            
            collection = self.client.collections.get(collection_name)
            
            # Delete document
            collection.data.delete_by_id(uuid)
            
            logger.info(f"✅ Document {uuid} deleted successfully")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to delete document {uuid}: {e}")
            return False
    
    def delete_documents_by_filter(self, collection_name: str, filters: Dict[str, Any]) -> int:
        """Delete multiple documents by filter"""
        if not self.is_available():
            logger.error("Weaviate client not available")
            return 0
        
        try:
            logger.info(f"Deleting documents by filter in {collection_name}")
            
            collection = self.client.collections.get(collection_name)
            
            # Delete documents by filter
            result = collection.data.delete_many(where=filters)
            
            deleted_count = result.total if hasattr(result, 'total') else 0
            logger.info(f"✅ Deleted {deleted_count} documents")
            return deleted_count
            
        except Exception as e:
            logger.error(f"❌ Failed to delete documents by filter: {e}")
            return 0
    
    def get_document_by_id(self, collection_name: str, uuid: str, include_vector: bool = False) -> Optional[Dict[str, Any]]:
        """Get a single document by UUID"""
        if not self.is_available():
            logger.error("Weaviate client not available")
            return None
        
        try:
            logger.info(f"Getting document {uuid} from {collection_name}")
            
            collection = self.client.collections.get(collection_name)
            
            result = collection.query.fetch_object_by_id(
                uuid=uuid,
                include_vector=include_vector
            )
            
            if result:
                doc = {
                    "uuid": result.uuid,
                    "properties": result.properties,
                    "vector": result.vector if include_vector else None
                }
                logger.info(f"✅ Document retrieved successfully")
                return doc
            else:
                logger.warning(f"Document {uuid} not found")
                return None
            
        except Exception as e:
            logger.error(f"❌ Failed to get document {uuid}: {e}")
            return None
    
    # ==================== ADVANCED SEARCH METHODS ====================
    
    def get_all_documents(self, collection_name: str, limit: int = 100, 
                         filters: Dict[str, Any] = None, include_vector: bool = False) -> List[Dict[str, Any]]:
        """Get all documents from a collection without using vector search"""
        if not self.is_available():
            logger.error("Weaviate client not available")
            return []
        
        try:
            logger.info(f"Getting all documents from {collection_name}")
            
            collection = self.client.collections.get(collection_name)
            
            # Build query parameters
            query_params = {
                "limit": limit,
                "include_vector": include_vector
            }
            
            if filters:
                query_params["filters"] = self._ensure_filters(filters)
            
            # Use fetch_objects to get all documents without search
            response = collection.query.fetch_objects(**query_params)
            
            results = []
            for obj in response.objects:
                result = {
                    "uuid": obj.uuid,
                    "properties": obj.properties,
                    "vector": obj.vector if include_vector else None
                }
                results.append(result)
            
            logger.info(f"✅ Retrieved {len(results)} documents from {collection_name}")
            return results
            
        except Exception as e:
            logger.error(f"❌ Failed to get documents from {collection_name}: {e}")
            return []

    def search_documents(self, collection_name: str, query: str, limit: int = 10, 
                        filters: Dict[str, Any] = None, include_vector: bool = False,
                        return_metadata: bool = True) -> List[Dict[str, Any]]:
        """Search documents using near_text (vector similarity)"""
        if not self.is_available():
            logger.error("Weaviate client not available")
            return []
        
        try:
            logger.info(f"Searching in {collection_name} with query: {query[:50]}...")
            
            collection = self.client.collections.get(collection_name)
            # Build search parameters
            search_params = {
                "limit": limit,
                "include_vector": include_vector
            }
            
            if return_metadata:
                search_params["return_metadata"] = MetadataQuery(distance=True, certainty=True)
            
            # Perform search with filters if provided
            if filters:
                response = collection.query.near_text(
                    query=query,
                    filters=self._ensure_filters(filters),
                    **search_params
                )
            else:
                response = collection.query.near_text(
                    query=query,
                    **search_params
                )
            
            results = []
            for obj in response.objects:
                result = {
                    "uuid": obj.uuid,
                    "properties": obj.properties,
                    "vector": obj.vector if include_vector else None
                }
                
                if return_metadata and hasattr(obj, 'metadata'):
                    result["metadata"] = {
                        "distance": obj.metadata.distance if hasattr(obj.metadata, 'distance') else None,
                        "certainty": obj.metadata.certainty if hasattr(obj.metadata, 'certainty') else None
                    }
                
                results.append(result)
            
            logger.info(f"✅ Found {len(results)} documents")
            return results
            
        except Exception as e:
            # Weaviate collections using remote vectorizers (e.g., text2vec-openai) will call the provider
            # to vectorize the *query* at search-time. If that provider returns 429/quota errors,
            # the whole near_text search fails even if documents already exist in Weaviate.
            err = str(e)
            logger.error(f"❌ Search failed: {err}")

            # Best-effort fallback: keyword search (BM25) does not require remote vectorization.
            # This keeps the system usable during OpenAI outages/quota exhaustion.
            lowered = err.lower()
            looks_like_quota = (
                "status: 429" in lowered
                or "error code: 429" in lowered
                or "insufficient_quota" in lowered
                or "exceeded your current quota" in lowered
                or "openai api failed with status: 429" in lowered
            )
            if looks_like_quota:
                logger.warning("⚠️ near_text failed due to provider 429/quota; falling back to BM25 keyword search")
                return self.bm25_search(
                    collection_name=collection_name,
                    query=query,
                    limit=limit,
                    filters=filters,
                    return_metadata=return_metadata,
                )

            return []
    
    def bm25_search(self, collection_name: str, query: str, limit: int = 10, 
                   filters: Dict[str, Any] = None, return_metadata: bool = True) -> List[Dict[str, Any]]:
        """Search documents using BM25 (keyword search) - may require pro account"""
        if not self.is_available():
            logger.error("Weaviate client not available")
            return []
        
        try:
            logger.info(f"BM25 search in {collection_name} with query: {query[:50]}...")
            
            collection = self.client.collections.get(collection_name)
            
            # Build search parameters
            search_params = {
                "limit": limit
            }
            
            if filters:
                search_params["filters"] = self._ensure_filters(filters)
            
            if return_metadata:
                search_params["return_metadata"] = MetadataQuery(score=True)
            
            # Perform BM25 search
            response = collection.query.bm25(
                query=query,
                **search_params
            )
            
            results = []
            for obj in response.objects:
                result = {
                    "uuid": obj.uuid,
                    "properties": obj.properties
                }
                
                if return_metadata and hasattr(obj, 'metadata'):
                    result["metadata"] = {
                        "score": obj.metadata.score if hasattr(obj.metadata, 'score') else None
                    }
                
                results.append(result)
            
            logger.info(f"✅ BM25 search found {len(results)} documents")
            return results
            
        except Exception as e:
            logger.error(f"❌ BM25 search failed (may require pro account): {e}")
            return []
    
    def hybrid_search(self, collection_name: str, query: str, limit: int = 10, 
                     alpha: float = 0.5, filters: Dict[str, Any] = None, 
                     return_metadata: bool = True) -> List[Dict[str, Any]]:
        """Search documents using hybrid (vector + keyword) - may require pro account"""
        if not self.is_available():
            logger.error("Weaviate client not available")
            return []
        
        try:
            logger.info(f"Hybrid search in {collection_name} with query: {query[:50]}...")
            
            collection = self.client.collections.get(collection_name)
            
            # Build search parameters
            search_params = {
                "limit": limit,
                "alpha": alpha
            }
            
            if filters:
                search_params["filters"] = self._ensure_filters(filters)
            
            if return_metadata:
                search_params["return_metadata"] = MetadataQuery(distance=True, score=True)
            
            # Perform hybrid search
            response = collection.query.hybrid(
                query=query,
                **search_params
            )
            
            results = []
            for obj in response.objects:
                result = {
                    "uuid": obj.uuid,
                    "properties": obj.properties
                }
                
                if return_metadata and hasattr(obj, 'metadata'):
                    result["metadata"] = {
                        "distance": obj.metadata.distance if hasattr(obj.metadata, 'distance') else None,
                        "score": obj.metadata.score if hasattr(obj.metadata, 'score') else None
                    }
                
                results.append(result)
            
            logger.info(f"✅ Hybrid search found {len(results)} documents")
            return results
            
        except Exception as e:
            logger.error(f"❌ Hybrid search failed (may require pro account): {e}")
            return []
    
    def near_vector_search(self, collection_name: str, vector: List[float], limit: int = 10,
                          filters: Dict[str, Any] = None, include_vector: bool = False,
                          return_metadata: bool = True) -> List[Dict[str, Any]]:
        """
        Search documents using near_vector (raw vector similarity).
        Compatible with Weaviate v4.15+ (uses near_vector=... argument).
        Works on free accounts.
        """
        if not self.is_available():
            logger.error("Weaviate client not available")
            return []
        try:
            logger.info(f"Near vector search in {collection_name}")
            collection = self.client.collections.get(collection_name)
            search_params = {
                "limit": limit,
                "include_vector": include_vector
            }
            if filters:
                search_params["where"] = filters
            if return_metadata:
                search_params["return_metadata"] = MetadataQuery(distance=True)
            # v4.15+ expects near_vector=...
            response = collection.query.near_vector(
                near_vector=vector,
                **search_params
            )
            results = []
            for obj in response.objects:
                result = {
                    "uuid": obj.uuid,
                    "properties": obj.properties,
                    "vector": obj.vector if include_vector else None
                }
                if return_metadata and hasattr(obj, 'metadata'):
                    result["metadata"] = {
                        "distance": getattr(obj.metadata, 'distance', None)
                    }
                results.append(result)
            logger.info(f"✅ Near vector search found {len(results)} documents")
            return results
        except Exception as e:
            logger.error(f"❌ Near vector search failed: {e}")
            return []
    
    def generative_search(self, collection_name: str, query: str, limit: int = 10,
                         single_prompt: str = None, grouped_task: str = None,
                         filters: Dict[str, Any] = None) -> Dict[str, Any]:
        """Search documents using generative search (RAG) - may require pro account"""
        if not self.is_available():
            logger.error("Weaviate client not available")
            return {}
        
        try:
            logger.info(f"Generative search in {collection_name} with query: {query[:50]}...")
            
            collection = self.client.collections.get(collection_name)
            
            # Build search parameters
            search_params = {
                "limit": limit
            }
            
            if filters:
                search_params["filters"] = self._ensure_filters(filters)
            
            if single_prompt:
                search_params["single_prompt"] = single_prompt
            
            if grouped_task:
                search_params["grouped_task"] = grouped_task
            
            # Perform generative search
            response = collection.generate.near_text(
                query=query,
                **search_params
            )
            
            results = {
                "objects": [],
                "generated": response.generated if hasattr(response, 'generated') else None
            }
            
            for obj in response.objects:
                result = {
                    "uuid": obj.uuid,
                    "properties": obj.properties,
                    "generated": obj.generated if hasattr(obj, 'generated') else None
                }
                results["objects"].append(result)
            
            logger.info(f"✅ Generative search found {len(results['objects'])} documents")
            return results
            
        except Exception as e:
            logger.error(f"❌ Generative search failed (may require pro account): {e}")
            return {}
    
    def rerank_search(self, collection_name: str, query: str, limit: int = 10,
                     rerank_limit: int = 50, filters: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Search documents using reranker - may require pro account"""
        if not self.is_available():
            logger.error("Weaviate client not available")
            return []
        
        try:
            logger.info(f"Reranker search in {collection_name} with query: {query[:50]}...")
            
            collection = self.client.collections.get(collection_name)
            
            # Build search parameters
            search_params = {
                "limit": limit,
                "rerank_limit": rerank_limit
            }
            
            if filters:
                search_params["filters"] = self._ensure_filters(filters)
            
            # Perform reranker search
            response = collection.query.rerank(
                query=query,
                **search_params
            )
            
            results = []
            for obj in response.objects:
                result = {
                    "uuid": obj.uuid,
                    "properties": obj.properties
                }
                
                if hasattr(obj, 'metadata'):
                    result["metadata"] = {
                        "rerank_score": obj.metadata.rerank_score if hasattr(obj.metadata, 'rerank_score') else None
                    }
                
                results.append(result)
            
            logger.info(f"✅ Reranker search found {len(results)} documents")
            return results
            
        except Exception as e:
            logger.error(f"❌ Reranker search failed (may require pro account): {e}")
            return []
    
    # ==================== REFERENCE MANAGEMENT ====================
    
    def add_reference(self, collection_name: str, from_uuid: str, from_property: str, 
                     to_uuid: str, to_collection: str = None) -> bool:
        """
        Add a reference between objects (v4.15+ signature).
        This feature may be limited on free accounts.
        """
        if not self.is_available():
            logger.error("Weaviate client not available")
            return False
        try:
            logger.info(f"Adding reference from {from_uuid} to {to_uuid}")
            collection = self.client.collections.get(collection_name)
            # v4.15+ expects positional args: from_property, from_uuid, to=to_uuid
            collection.data.reference_add(from_property, from_uuid, to=to_uuid)
            logger.info(f"✅ Reference added successfully")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to add reference: {e}")
            return False
    
    def delete_reference(self, collection_name: str, from_uuid: str, from_property: str, 
                        to_uuid: str) -> bool:
        """
        Delete a reference between objects (v4.15+ signature).
        This feature may be limited on free accounts.
        """
        if not self.is_available():
            logger.error("Weaviate client not available")
            return False
        try:
            logger.info(f"Deleting reference from {from_uuid} to {to_uuid}")
            collection = self.client.collections.get(collection_name)
            # v4.15+ expects positional args: from_property, from_uuid, to=to_uuid
            collection.data.reference_delete(from_property, from_uuid, to=to_uuid)
            logger.info(f"✅ Reference deleted successfully")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to delete reference: {e}")
            return False
    
    def search_with_references(self, collection_name: str, query: str, limit: int = 10,
                              reference_property: str = None, reference_limit: int = 5,
                              filters: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Search documents with references"""
        if not self.is_available():
            logger.error("Weaviate client not available")
            return []
        
        try:
            logger.info(f"Searching with references in {collection_name}")
            
            collection = self.client.collections.get(collection_name)
            
            # Build search parameters
            search_params = {
                "limit": limit
            }
            
            if filters:
                search_params["filters"] = self._ensure_filters(filters)
            
            if reference_property:
                search_params["return_references"] = {
                    "link_on": reference_property,
                    "return_properties": ["*"],
                    "limit": reference_limit
                }
            
            # Perform search with references
            response = collection.query.near_text(
                query=query,
                **search_params
            )
            
            results = []
            for obj in response.objects:
                result = {
                    "uuid": obj.uuid,
                    "properties": obj.properties,
                    "references": obj.references if hasattr(obj, 'references') else None
                }
                results.append(result)
            
            logger.info(f"✅ Search with references found {len(results)} documents")
            return results
            
        except Exception as e:
            logger.error(f"❌ Search with references failed: {e}")
            return []
    
    # ==================== BATCH OPERATIONS ====================
    
    def batch_update_documents(self, collection_name: str, updates: List[Dict[str, Any]]) -> int:
        """
        Update multiple documents in batch.
        v4.15+ does not support batch update; fallback to individual update calls.
        Works on free accounts.
        """
        if not self.is_available():
            logger.error("Weaviate client not available")
            return 0
        try:
            logger.info(f"Batch updating {len(updates)} documents in {collection_name}")
            collection = self.client.collections.get(collection_name)
            updated_count = 0
            for update in updates:
                try:
                    collection.data.update(uuid=update["uuid"], properties=update["properties"])
                    updated_count += 1
                except Exception as e:
                    logger.error(f"Failed to update document {update['uuid']}: {e}")
            logger.info(f"✅ Successfully updated {updated_count} documents")
            return updated_count
        except Exception as e:
            logger.error(f"❌ Failed to batch update documents: {e}")
            return 0
    
    def batch_delete_documents(self, collection_name: str, uuids: List[str]) -> int:
        """
        Delete multiple documents in batch.
        v4.15+ does not support batch delete; fallback to individual delete_by_id calls.
        Works on free accounts.
        """
        if not self.is_available():
            logger.error("Weaviate client not available")
            return 0
        try:
            logger.info(f"Batch deleting {len(uuids)} documents from {collection_name}")
            collection = self.client.collections.get(collection_name)
            deleted_count = 0
            for uuid in uuids:
                try:
                    collection.data.delete_by_id(uuid)
                    deleted_count += 1
                except Exception as e:
                    logger.error(f"Failed to delete document {uuid}: {e}")
            logger.info(f"✅ Successfully deleted {deleted_count} documents")
            return deleted_count
        except Exception as e:
            logger.error(f"❌ Failed to batch delete documents: {e}")
            return 0
    
    # ==================== AGGREGATION AND ANALYTICS ====================
    
    def aggregate_collection(self, collection_name: str, group_by: str = None,
                           metrics: List[str] = None, filters: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Aggregate data in collection. Advanced metrics may require a pro account.
        v4.15+ expects metrics as a list of dicts, e.g. [{"property": "word_count", "aggregators": ["sum"]}]
        """
        if not self.is_available():
            logger.error("Weaviate client not available")
            return {}
        try:
            logger.info(f"Aggregating data in {collection_name}")
            collection = self.client.collections.get(collection_name)
            agg_params = {"total_count": True}
            if filters:
                agg_params["filters"] = filters
            if group_by:
                agg_params["group_by"] = group_by
            if metrics:
                # v4.15+ expects metrics as a list of dicts
                agg_params["metrics"] = [{"property": m, "aggregators": ["sum"]} for m in metrics]
            response = collection.aggregate.over_all(**agg_params)
            result = {
                "total_count": getattr(response, 'total', 0),
                "groups": getattr(response, 'groups', []),
                "properties": getattr(response, 'properties', {})
            }
            logger.info(f"✅ Aggregation completed: {result['total_count']} total objects")
            return result
        except Exception as e:
            logger.error(f"❌ Aggregation failed: {e}")
            return {}
    
    # ==================== SCHEMA MANAGEMENT ====================
    
    def create_research_papers_schema(self) -> Dict[str, Any]:
        """Create schema for research papers collection"""
        return {
            "class": "ResearchPaper",
            "description": "Collection for storing research papers with extracted content",
            "vectorizer": "text2vec-openai",
            "moduleConfig": {
                "text2vec-openai": {
                    "vectorizeClassName": False,
                    "model": "ada",
                    "modelVersion": "002",
                    "type": "text"
                }
            },
            "properties": [
                {
                    "name": "title",
                    "dataType": ["text"],
                    "description": "Paper title"
                },
                {
                    "name": "authors",
                    "dataType": ["text[]"],
                    "description": "Paper authors"
                },
                {
                    "name": "abstract",
                    "dataType": ["text"],
                    "description": "Paper abstract"
                },
                {
                    "name": "content",
                    "dataType": ["text"],
                    "description": "Extracted paper content"
                },
                {
                    "name": "year",
                    "dataType": ["int"],
                    "description": "Publication year"
                },
                {
                    "name": "doi",
                    "dataType": ["text"],
                    "description": "Digital Object Identifier"
                },
                {
                    "name": "url",
                    "dataType": ["text"],
                    "description": "Paper URL"
                },
                {
                    "name": "source",
                    "dataType": ["text"],
                    "description": "Data source (e.g., CORE, arXiv)"
                },
                {
                    "name": "word_count",
                    "dataType": ["int"],
                    "description": "Number of words in extracted content"
                },
                {
                    "name": "pages_extracted",
                    "dataType": ["int"],
                    "description": "Number of pages extracted"
                },
                {
                    "name": "research_domain",
                    "dataType": ["text"],
                    "description": "Research domain/category"
                },
                {
                    "name": "extracted_at",
                    "dataType": ["date"],
                    "description": "When content was extracted"
                }
            ]
        }
    
    def create_research_papers_with_references_schema(self) -> Dict[str, Any]:
        """Create schema for research papers with references to authors and topics"""
        return {
            "class": "ResearchPaper",
            "description": "Collection for storing research papers with references",
            "vectorizer": "text2vec-openai",
            "moduleConfig": {
                "text2vec-openai": {
                    "vectorizeClassName": False,
                    "model": "ada",
                    "modelVersion": "002",
                    "type": "text"
                }
            },
            "properties": [
                {
                    "name": "title",
                    "dataType": ["text"],
                    "description": "Paper title"
                },
                {
                    "name": "abstract",
                    "dataType": ["text"],
                    "description": "Paper abstract"
                },
                {
                    "name": "content",
                    "dataType": ["text"],
                    "description": "Extracted paper content"
                },
                {
                    "name": "year",
                    "dataType": ["int"],
                    "description": "Publication year"
                },
                {
                    "name": "doi",
                    "dataType": ["text"],
                    "description": "Digital Object Identifier"
                },
                {
                    "name": "url",
                    "dataType": ["text"],
                    "description": "Paper URL"
                },
                {
                    "name": "source",
                    "dataType": ["text"],
                    "description": "Data source (e.g., CORE, arXiv)"
                },
                {
                    "name": "word_count",
                    "dataType": ["int"],
                    "description": "Number of words in extracted content"
                },
                {
                    "name": "pages_extracted",
                    "dataType": ["int"],
                    "description": "Number of pages extracted"
                },
                {
                    "name": "research_domain",
                    "dataType": ["text"],
                    "description": "Research domain/category"
                },
                {
                    "name": "extracted_at",
                    "dataType": ["date"],
                    "description": "When content was extracted"
                }
            ],
            "references": [
                {
                    "name": "hasAuthors",
                    "targetCollection": "Author",
                    "description": "Authors of the paper"
                },
                {
                    "name": "hasTopics",
                    "targetCollection": "Topic",
                    "description": "Topics covered by the paper"
                }
            ]
        }
    
    def prepare_paper_document(self, paper: Dict[str, Any], research_domain: str) -> Dict[str, Any]:
        """Prepare a paper document for insertion into Weaviate"""
        return {
            "properties": {
                "title": paper.get("title", ""),
                "authors": paper.get("authors", []),
                "abstract": paper.get("abstract", ""),
                "content": paper.get("extracted_content", ""),
                "year": paper.get("year"),
                "doi": paper.get("doi", ""),
                "url": paper.get("url", ""),
                "source": paper.get("source", "CORE"),
                "word_count": paper.get("word_count", 0),
                "pages_extracted": paper.get("pages_extracted", 0),
                "research_domain": research_domain,
                "extracted_at": datetime.now(timezone.utc).isoformat()
            }
        }
    
    def get_class_schema(self, class_name: str):
        if not self.is_available():
            return None
        try:
            collection = self.client.collections.get(class_name)
            return collection.config.get()
        except Exception as e:
            print(f"[ERROR] get_class_schema failed for {class_name}: {e}")
            return None

    def close(self):
        """Close Weaviate connection"""
        if self.client:
            try:
                self.client.close()
                logger.info("Weaviate connection closed")
            except Exception as e:
                logger.error(f"Error closing Weaviate connection: {e}")
            finally:
                self.client = None
                self.is_connected = False

# Global Weaviate manager instance
_weaviate_manager: Optional[WeaviateManager] = None

def get_weaviate_manager() -> WeaviateManager:
    """Get or create global Weaviate manager instance"""
    global _weaviate_manager
    if _weaviate_manager is None:
        _weaviate_manager = WeaviateManager()
    return _weaviate_manager

def close_weaviate_manager():
    """Close global Weaviate manager"""
    global _weaviate_manager
    if _weaviate_manager:
        _weaviate_manager.close()
        _weaviate_manager = None 