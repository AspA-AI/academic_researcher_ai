import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
import uuid
from .weaviate_client import get_weaviate_manager

logger = logging.getLogger(__name__)

class PipelineStorageManager:
    """
    Manages pipeline data storage using Weaviate for traditional CRUD operations.
    Falls back to in-memory storage if Weaviate is not available.
    """
    
    def __init__(self):
        self.weaviate = get_weaviate_manager()
        self.collection_name = "ResearchPipeline"
        self._use_weaviate = False
        self._in_memory_pipelines = {}  # Fallback storage
        self._pipeline_mappings = {}  # pipeline_id -> uuid mapping
        
        # Try to initialize Weaviate, but don't fail if unavailable
        try:
            if self.weaviate.is_available():
                self._ensure_collection_exists()
                self._use_weaviate = True
                print(f"[DEBUG] PipelineStorageManager: Using Weaviate storage")
            else:
                print(f"[DEBUG] PipelineStorageManager: Weaviate not available, using in-memory storage")
        except Exception as e:
            print(f"[DEBUG] PipelineStorageManager: Weaviate initialization failed: {e}, using in-memory storage")
    
    def _ensure_collection_exists(self):
        """Ensure the pipeline collection exists with proper schema."""
        if not self.weaviate.is_available():
            return  # Don't raise error, just return
        
        existing_collections = self.weaviate.list_collections()
        if self.collection_name not in existing_collections:
            print(f"[DEBUG] Creating pipeline collection {self.collection_name}...")
            schema = {
                "class": self.collection_name,
                "description": "Research pipeline data and results",
                "vectorizer": "none",  # No vectorization needed for CRUD operations
                "properties": [
                    {"name": "pipeline_id", "dataType": ["text"]},
                    {"name": "status", "dataType": ["text"]},
                    {"name": "research_domain", "dataType": ["text"]},
                    {"name": "query", "dataType": ["text"]},
                    {"name": "created_at", "dataType": ["text"]},
                    {"name": "updated_at", "dataType": ["text"]},
                    {"name": "completed_at", "dataType": ["text"]},
                    {"name": "current_step", "dataType": ["int"]},
                    {"name": "total_steps", "dataType": ["int"]},
                    {"name": "pipeline_data", "dataType": ["text"]},  # JSON string
                    {"name": "results", "dataType": ["text"]},  # JSON string
                    {"name": "error_message", "dataType": ["text"]},
                    {"name": "quality_scores", "dataType": ["text"]},  # JSON string
                    {"name": "supervisor_decisions", "dataType": ["text"]},  # JSON string
                ]
            }
            self.weaviate.create_collection(self.collection_name, schema)
            print(f"[DEBUG] Created pipeline collection: {self.collection_name}")
        else:
            print(f"[DEBUG] Pipeline collection {self.collection_name} already exists")
    
    def create_pipeline(self, pipeline_data: Dict[str, Any]) -> str:
        """
        Create a new pipeline record.
        Returns the Weaviate-generated pipeline_id.
        """
        
        # Remove any existing pipeline_id from the data - we'll use Weaviate's ID
        pipeline_data.pop("pipeline_id", None)
        
        now = datetime.now(timezone.utc).isoformat()
        print(f"[DEBUG] Current timestamp: {now}")
        
        # Prepare the document
        doc = {
            "properties": {
                "status": pipeline_data.get("status", "created"),
                "research_domain": pipeline_data.get("research_domain", "General"),
                "query": pipeline_data.get("query", ""),
                "created_at": now,
                "updated_at": now,
                "completed_at": "",
                "current_step": pipeline_data.get("current_step", 0),
                "total_steps": pipeline_data.get("total_steps", 6),
                "pipeline_data": self._serialize_json(pipeline_data),
                "results": "",
                "error_message": "",
                "quality_scores": "{}",
                "supervisor_decisions": "{}"
            }
        }
        
        if self._use_weaviate:
            print(f"[DEBUG] Using Weaviate storage")
            print(f"[DEBUG] Collection name: {self.collection_name}")
            
            try:
                print(f"[DEBUG] Weaviate client available: {self.weaviate is not None}")
                # Let Weaviate generate the ID
                result_uuid = self.weaviate.insert_single_document(self.collection_name, doc)
                print(f"[DEBUG] Weaviate insert_single_document returned UUID: {result_uuid}")
                
                if result_uuid:                    
                    # Verify the document was actually stored
                    try:
                        verification_doc = self.weaviate.get_document_by_id(self.collection_name, result_uuid)
                        if verification_doc:
                            print(f"[DEBUG] ✅ Document verification successful")
                        else:
                            print(f"[ERROR] ❌ Document verification failed - document not found")
                    except Exception as verify_error:
                        print(f"[ERROR] Document verification failed: {verify_error}")
                    
                    return result_uuid  # Return Weaviate's ID as the pipeline_id
                else:
                    raise RuntimeError("Failed to get UUID from document insertion")
                    
            except Exception as e:
                print(f"[ERROR] Failed to create pipeline in Weaviate: {e}")
                print(f"[ERROR] Exception type: {type(e)}")
                import traceback
                print(f"[ERROR] Exception traceback: {traceback.format_exc()}")
                # Don't fall back to in-memory storage - this would create ID inconsistency
                # Instead, raise the error to maintain consistency
                raise RuntimeError(f"Failed to create pipeline in Weaviate: {str(e)}")
        
        # Use in-memory storage (only when Weaviate is completely unavailable from the start)
        print(f"[DEBUG] Using in-memory storage")
        # Generate a simple ID for in-memory storage
        in_memory_id = str(uuid.uuid4())
        pipeline_data["pipeline_id"] = in_memory_id
        self._in_memory_pipelines[in_memory_id] = pipeline_data
        print(f"[DEBUG] Created pipeline in memory with ID: {in_memory_id}")
        return in_memory_id
    
    def get_pipeline(self, pipeline_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a pipeline by its ID (which is now Weaviate's UUID).
        """
        print(f"[DEBUG] Getting pipeline {pipeline_id}")
        print(f"[DEBUG] Using Weaviate: {self._use_weaviate}")
        
        if self._use_weaviate:
            try:
                # Since pipeline_id is now Weaviate's UUID, we can get it directly
                print(f"[DEBUG] Looking for pipeline {pipeline_id}")
                result = self.weaviate.get_document_by_id(self.collection_name, pipeline_id)
                
                if result:
                    print(f"[DEBUG] Found pipeline {pipeline_id}")
                    return self._deserialize_pipeline(result)
                else:
                    print(f"[DEBUG] Pipeline {pipeline_id} not found")
                    return None
                    
            except Exception as e:
                print(f"[ERROR] Weaviate query failed: {e}")
                # Don't fall back to in-memory storage - this would create ID inconsistency
                # Instead, raise the error to maintain consistency
                raise RuntimeError(f"Failed to get pipeline from Weaviate: {str(e)}")
        
        # Use in-memory storage (only when Weaviate is completely unavailable from the start)
        if not self._use_weaviate:
            print(f"[DEBUG] Using in-memory storage")
            if pipeline_id in self._in_memory_pipelines:
                doc = self._in_memory_pipelines[pipeline_id]
                print(f"[DEBUG] Found pipeline {pipeline_id} in memory")
                return self._deserialize_pipeline(doc)
            else:
                print(f"[DEBUG] Pipeline {pipeline_id} not found in memory")
                return None
        
        return None
    
    def update_pipeline(self, pipeline_id: str, updates: Dict[str, Any]) -> bool:
        """
        Update a pipeline record.
        """
        print(f"[DEBUG] Updating pipeline {pipeline_id}")
        print(f"[DEBUG] Using Weaviate: {self._use_weaviate}")
        
        if self._use_weaviate:
            try:
                # Since pipeline_id is now Weaviate's UUID, we can update it directly
                print(f"[DEBUG] Looking for pipeline {pipeline_id}")
                
                # Get current pipeline data
                current_pipeline = self.get_pipeline(pipeline_id)
                if not current_pipeline:
                    print(f"[ERROR] Pipeline {pipeline_id} not found for update")
                    return False
                
                # Merge updates
                updated_data = {**current_pipeline, **updates}
                updated_data["updated_at"] = datetime.now(timezone.utc).isoformat()
                
                # Prepare update properties
                update_properties = {
                    "status": updated_data.get("status"),
                    "research_domain": updated_data.get("research_domain"),
                    "query": updated_data.get("query"),
                    "updated_at": updated_data.get("updated_at"),
                    "completed_at": updated_data.get("completed_at", ""),
                    "current_step": updated_data.get("current_step"),
                    "total_steps": updated_data.get("total_steps"),
                    "pipeline_data": self._serialize_json(updated_data.get("pipeline_data", {})),
                    "results": self._serialize_json(updated_data.get("results", {})),
                    "error_message": updated_data.get("error_message", ""),
                    "quality_scores": self._serialize_json(updated_data.get("quality_scores", {})),
                    "supervisor_decisions": self._serialize_json(updated_data.get("supervisor_decisions", {}))
                }
                
                # Update the object directly using pipeline_id as UUID
                success = self.weaviate.update_document(self.collection_name, pipeline_id, update_properties)
                
                if success:
                    print(f"[DEBUG] Updated pipeline {pipeline_id}")
                    return True
                else:
                    print(f"[ERROR] Failed to update pipeline {pipeline_id}")
                    return False
                
            except Exception as e:
                print(f"[ERROR] Failed to update pipeline {pipeline_id} in Weaviate: {e}")
                # Don't fall back to in-memory storage - this would create ID inconsistency
                # Instead, raise the error to maintain consistency
                raise RuntimeError(f"Failed to update pipeline in Weaviate: {str(e)}")
        
        # Use in-memory storage (only when Weaviate is completely unavailable from the start)
        if not self._use_weaviate:
            print(f"[DEBUG] Using in-memory storage")
            if pipeline_id in self._in_memory_pipelines:
                # Update the in-memory pipeline
                current_data = self._in_memory_pipelines[pipeline_id]
                updated_data = {**current_data, **updates}
                updated_data["updated_at"] = datetime.now(timezone.utc).isoformat()
                self._in_memory_pipelines[pipeline_id] = updated_data
                print(f"[DEBUG] Updated pipeline {pipeline_id} in memory")
                return True
            else:
                print(f"[ERROR] Pipeline {pipeline_id} not found in memory")
                return False
        
        return False
    
    def list_pipelines(self, limit: int = 20, offset: int = 0, 
                      status: Optional[str] = None, 
                      research_domain: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        List pipelines with optional filtering.
        """
        print(f"\n🗄️ ===== STORAGE MANAGER LIST_PIPELINES DEBUG =====")
        print(f"🗄️ Parameters:")
        print(f"🗄️   Limit: {limit}")
        print(f"🗄️   Offset: {offset}")
        print(f"🗄️   Status filter: {status}")
        print(f"🗄️   Research domain filter: {research_domain}")
        print(f"🗄️   Using Weaviate: {self._use_weaviate}")
        
        pipelines = []
        
        if self._use_weaviate:
            print(f"🗄️ Using Weaviate storage")
            try:
                # Get all documents from the collection
                print(f"🗄️ Calling weaviate.get_all_documents({self.collection_name}, limit={limit + offset + 50})")
                results = self.weaviate.get_all_documents(
                    self.collection_name,
                    limit=limit + offset + 50
                )
                print(f"🗄️ get_all_documents returned {len(results)} results")
                
                for i, result in enumerate(results):
                    # Deserialize each pipeline
                    pipeline_data = self._deserialize_pipeline(result)
                    if pipeline_data:
                        pipelines.append(pipeline_data)
                        print(f"🗄️   ✅ Found pipeline {i+1}: {pipeline_data['pipeline_id']} ({pipeline_data['status']})")
                    else:
                        print(f"🗄️   ⚠️ Skipping invalid pipeline document {i+1}")
                        
            except Exception as e:
                print(f"🗄️ ❌ get_all_documents failed: {e}")
                print(f"🗄️ Falling back to in-memory storage")
                self._use_weaviate = False
        
        # Use in-memory storage (either as fallback or primary)
        if not self._use_weaviate:
            print(f"🗄️ Using in-memory storage")
            for pipeline_id, doc in self._in_memory_pipelines.items():
                pipeline_data = self._deserialize_pipeline(doc)
                if pipeline_data:
                    pipelines.append(pipeline_data)
                    print(f"🗄️   ✅ Found in-memory pipeline: {pipeline_id}")
        
        print(f"🗄️ Raw pipelines found: {len(pipelines)}")
        
        # Apply filtering
        print(f"🗄️ Applying filters...")
        filtered_results = []
        for pipeline in pipelines:
            print(f"🗄️   Checking pipeline {pipeline['pipeline_id']}:")
            print(f"🗄️     Status: {pipeline.get('status')} (filter: {status})")
            print(f"🗄️     Domain: {pipeline.get('research_domain')} (filter: {research_domain})")
            
            # Apply filters
            if status and pipeline.get("status") != status:
                print(f"🗄️     ❌ Filtered out by status")
                continue
            if research_domain and pipeline.get("research_domain") != research_domain:
                print(f"🗄️     ❌ Filtered out by domain")
                continue
            
            print(f"🗄️     ✅ Passed filters")
            filtered_results.append(pipeline)
        
        print(f"🗄️ After filtering: {len(filtered_results)} pipelines")
        
        # Sort latest to oldest by created_at (fallback to updated_at)
        try:
            from datetime import datetime
            def _parse_dt(p):
                ts = p.get("created_at") or p.get("updated_at") or "1970-01-01T00:00:00+00:00"
                try:
                    return datetime.fromisoformat(ts)
                except Exception:
                    return datetime.min.replace(tzinfo=None)
            sorted_results = sorted(filtered_results, key=_parse_dt, reverse=True)
        except Exception:
            sorted_results = filtered_results
        
        # Apply offset and limit
        final_results = sorted_results[offset:offset + limit]
        print(f"🗄️ After pagination: {len(final_results)} pipelines")
        
        print(f"🗄️ Final pipeline list:")
        for i, pipeline in enumerate(final_results):
            print(f"🗄️   {i+1}. {pipeline['pipeline_id']} - {pipeline['status']} - {pipeline['research_domain']}")
        
        print(f"🗄️ ===== STORAGE MANAGER COMPLETED =====\n")
        return final_results
    
    def delete_pipeline(self, pipeline_id: str) -> bool:
        """
        Delete a pipeline by ID.
        """
        print(f"[DEBUG] Deleting pipeline {pipeline_id}")
        print(f"[DEBUG] Using Weaviate: {self._use_weaviate}")
        
        if self._use_weaviate:
            try:
                # Since pipeline_id is now Weaviate's UUID, we can delete it directly
                print(f"[DEBUG] Deleting pipeline {pipeline_id}")
                
                # Delete the object directly using pipeline_id as UUID
                success = self.weaviate.delete_document(self.collection_name, pipeline_id)
                
                if success:
                    print(f"[DEBUG] Deleted pipeline {pipeline_id}")
                    return True
                else:
                    print(f"[ERROR] Failed to delete pipeline {pipeline_id}")
                    return False
                
            except Exception as e:
                print(f"[ERROR] Failed to delete pipeline {pipeline_id} in Weaviate: {e}")
                # Don't fall back to in-memory storage - this would create ID inconsistency
                # Instead, raise the error to maintain consistency
                raise RuntimeError(f"Failed to delete pipeline in Weaviate: {str(e)}")
        
        # Use in-memory storage (only when Weaviate is completely unavailable from the start)
        if not self._use_weaviate:
            print(f"[DEBUG] Using in-memory storage")
            if pipeline_id in self._in_memory_pipelines:
                # Remove from in-memory storage
                del self._in_memory_pipelines[pipeline_id]
                print(f"[DEBUG] Deleted pipeline {pipeline_id} from memory")
                return True
            else:
                print(f"[ERROR] Pipeline {pipeline_id} not found in memory")
                return False
        
        return False
    
    def _serialize_json(self, data: Any) -> str:
        """Serialize data to JSON string."""
        import json
        try:
            return json.dumps(data, default=str)
        except Exception as e:
            print(f"[WARNING] Failed to serialize JSON: {e}")
            return "{}"
    
    def _deserialize_pipeline(self, pipeline_obj: Dict[str, Any]) -> Dict[str, Any]:
        """Deserialize pipeline object from Weaviate."""
        import json
        
        try:
            # Extract properties from the Weaviate response format
            properties = pipeline_obj.get("properties", pipeline_obj)
            
            # Get the pipeline_id from Weaviate's document ID
            # Weaviate might return it as 'id', 'uuid', or in the properties
            pipeline_id = pipeline_obj.get("id") or pipeline_obj.get("uuid") or "unknown"
            
            # Helper function to safely parse JSON
            def safe_json_loads(value, default=None):
                if not value or value == "":
                    return default or {}
                try:
                    return json.loads(value)
                except json.JSONDecodeError:
                    print(f"[WARNING] Failed to parse JSON: {value}")
                    return default or {}
            
            return {
                "pipeline_id": str(pipeline_id),  # Convert to string to ensure consistency
                "status": properties["status"],
                "research_domain": properties["research_domain"],
                "query": properties["query"],
                "created_at": properties["created_at"],
                "updated_at": properties["updated_at"],
                "completed_at": properties.get("completed_at", ""),
                "current_step": properties["current_step"],
                "total_steps": properties["total_steps"],
                "pipeline_data": safe_json_loads(properties.get("pipeline_data")),
                "results": safe_json_loads(properties.get("results")),
                "error_message": properties.get("error_message", ""),
                "quality_scores": safe_json_loads(properties.get("quality_scores")),
                "supervisor_decisions": safe_json_loads(properties.get("supervisor_decisions"))
            }
        except Exception as e:
            print(f"[WARNING] Failed to deserialize pipeline: {e}")
            return {} 