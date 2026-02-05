"""
Data management route handlers for the Research Pipeline API.
Contains endpoints for document retrieval and vector database operations.
"""

import sys
import os
from datetime import datetime, timezone
from typing import List, Optional

# Add the parent directory to the path for imports

from fastapi import APIRouter, HTTPException, Query, Path
from fastapi.responses import JSONResponse

from api.models.requests import DataRequest
from api.models.responses import (
    DataResponse, DataStatisticsResponse
)
from api.services.data_service import DataService

router = APIRouter()

# Initialize data service
data_service = DataService()

@router.get("/retrieve/{collection_name}", response_model=DataResponse)
async def retrieve_all_documents(
    collection_name: str = Path(..., description="Name of the collection to retrieve all documents from")
):
    """
    Retrieve all documents from a specific collection.
    
    This endpoint returns all documents stored in the specified collection:
    - Returns all documents without filtering
    - No query or search parameters needed
    - Returns complete document content and metadata
    """
    try:
        result = await data_service.retrieve_all_documents(collection_name)
        
        if not result["success"]:
            raise HTTPException(
                status_code=400,
                detail=f"Document retrieval failed: {result.get('error', 'Unknown error')}"
            )
        
        response = DataResponse(
            success=True,
            data=result["data"],
            operation_id=result.get("operation_id"),
            timestamp=datetime.now(timezone.utc).isoformat()
        )
        
        return response
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Document retrieval failed: {str(e)}"
        )

@router.post("/store", response_model=DataResponse)
async def store_documents(request: DataRequest):
    """
    Store documents in the vector database.
    
    This endpoint stores documents for later retrieval:
    - Processes and chunks documents
    - Generates embeddings
    - Stores in vector database with metadata
    - Supports batch document storage
    """
    try:
        if not request.documents:
            raise HTTPException(
                status_code=400,
                detail="Documents are required for storage"
            )
        
        result = await data_service.store_documents(
            documents=request.documents,
            research_domain=request.research_domain,
            collection_name=request.collection_name
        )
        
        if not result["success"]:
            raise HTTPException(
                status_code=400,
                detail=f"Document storage failed: {result.get('error', 'Unknown error')}"
            )
        
        response = DataResponse(
            success=True,
            data=result["data"],
            operation_id=result.get("operation_id"),
            timestamp=datetime.now(timezone.utc).isoformat()
        )
        
        return response
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Document storage failed: {str(e)}"
        )

@router.get("/collections", response_model=DataResponse)
async def list_collections():
    """
    List all available vector database collections.
    
    Returns information about all collections including:
    - Collection names and descriptions
    - Document counts
    - Research domains
    - Creation dates
    """
    try:
        result = data_service.list_collections()
        
        if not result["success"]:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to list collections: {result.get('error', 'Unknown error')}"
            )
        
        response = DataResponse(
            success=True,
            data=result["data"],
            timestamp=datetime.now(timezone.utc).isoformat()
        )
        
        return response
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list collections: {str(e)}"
        )

@router.get("/collections/{collection_name}", response_model=DataResponse)
async def get_collection_info(
    collection_name: str = Path(..., description="Name of the collection")
):
    """
    Get detailed information about a specific collection.
    
    Returns collection details including:
    - Document count and metadata
    - Research domain information
    - Index statistics
    - Performance metrics
    """
    try:
        result = data_service.get_collection_info(collection_name)
        
        if not result["success"]:
            raise HTTPException(
                status_code=404,
                detail=f"Collection not found: {collection_name}"
            )
        
        response = DataResponse(
            success=True,
            data=result["data"],
            timestamp=datetime.now(timezone.utc).isoformat()
        )
        
        return response
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get collection info: {str(e)}"
        )

@router.delete("/collections/{collection_name}")
async def delete_collection(
    collection_name: str = Path(..., description="Name of the collection to delete")
):
    """
    Delete a collection and all its documents.
    
    This will permanently remove the collection and all stored documents.
    Use with caution as this action cannot be undone.
    """
    try:
        result = data_service.delete_collection(collection_name)
        
        if not result["success"]:
            raise HTTPException(
                status_code=404,
                detail=f"Collection not found: {collection_name}"
            )
        
        return {
            "success": True,
            "message": f"Collection {collection_name} deleted successfully",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete collection: {str(e)}"
        )

@router.delete("/documents")
async def delete_documents(request: DataRequest):
    """
    Delete specific documents from a collection.
    
    Removes documents by their IDs from the specified collection.
    Useful for cleaning up specific documents without deleting the entire collection.
    """
    try:
        if not request.document_ids:
            raise HTTPException(
                status_code=400,
                detail="Document IDs are required for deletion"
            )
        
        result = data_service.delete_documents(
            document_ids=request.document_ids,
            collection_name=request.collection_name
        )
        
        if not result["success"]:
            raise HTTPException(
                status_code=400,
                detail=f"Document deletion failed: {result.get('error', 'Unknown error')}"
            )
        
        return {
            "success": True,
            "message": f"Deleted {len(request.document_ids)} documents successfully",
            "data": result["data"],
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Document deletion failed: {str(e)}"
        )

@router.get("/statistics", response_model=DataStatisticsResponse)
async def get_data_statistics(
    collection_name: Optional[str] = Query(None, description="Filter by collection name")
):
    """
    Get comprehensive data statistics.
    
    Returns statistics about the vector database including:
    - Total documents and collections
    - Storage usage and performance
    - Query statistics and trends
    - Research domain distribution
    """
    try:
        result = data_service.get_data_statistics(
            collection_name=collection_name
        )
        
        if not result["success"]:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to get data statistics: {result.get('error', 'Unknown error')}"
            )
        
        response = DataStatisticsResponse(
            success=True,
            data=result["data"],
            timestamp=datetime.now(timezone.utc).isoformat()
        )
        
        return response
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get data statistics: {str(e)}"
        )

