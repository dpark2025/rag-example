"""API client for FastAPI integration."""

import httpx
import logging
from typing import List, Dict, Optional, Any
import asyncio

logger = logging.getLogger(__name__)

class RAGAPIClient:
    """Client for communicating with the RAG FastAPI backend."""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.timeout = httpx.Timeout(30.0)
    
    async def _make_request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """Make an HTTP request with error handling."""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.request(method, f"{self.base_url}{endpoint}", **kwargs)
                response.raise_for_status()
                return response.json()
        except httpx.TimeoutException:
            logger.error(f"Timeout occurred for {method} {endpoint}")
            raise Exception("Request timed out")
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error {e.response.status_code} for {method} {endpoint}")
            raise Exception(f"API error: {e.response.status_code}")
        except Exception as e:
            logger.error(f"Unexpected error for {method} {endpoint}: {e}")
            raise Exception(f"Network error: {str(e)}")
    
    async def health_check(self) -> Dict[str, Any]:
        """Check the health of all services."""
        return await self._make_request("GET", "/health")
    
    async def query(self, question: str, max_chunks: int = 5, similarity_threshold: float = 0.7) -> Dict[str, Any]:
        """Send a query to the RAG system."""
        payload = {
            "question": question,
            "max_chunks": max_chunks,
            "similarity_threshold": similarity_threshold
        }
        return await self._make_request("POST", "/query", json=payload)
    
    async def add_documents(self, documents: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Add text documents to the RAG system."""
        return await self._make_request("POST", "/documents", json=documents)
    
    async def get_documents(self, skip: int = 0, limit: int = 100, 
                          file_type: Optional[str] = None, 
                          search: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get list of documents with optional filtering."""
        params = {"skip": skip, "limit": limit}
        if file_type:
            params["file_type"] = file_type
        if search:
            params["search"] = search
        
        return await self._make_request("GET", "/api/v1/documents", params=params)
    
    async def delete_document(self, doc_id: str) -> Dict[str, Any]:
        """Delete a specific document."""
        return await self._make_request("DELETE", f"/api/v1/documents/{doc_id}")
    
    async def delete_documents_bulk(self, doc_ids: List[str]) -> Dict[str, Any]:
        """Delete multiple documents."""
        return await self._make_request("DELETE", "/api/v1/documents/bulk", json=doc_ids)
    
    async def upload_pdf_files(self, files: List[bytes], filenames: List[str]) -> Dict[str, Any]:
        """Upload PDF files to the system."""
        files_data = []
        for file_content, filename in zip(files, filenames):
            files_data.append(("files", (filename, file_content, "application/pdf")))
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/api/v1/documents/upload/pdf",
                    files=files_data
                )
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.error(f"Error uploading PDF files: {e}")
            raise Exception(f"Upload failed: {str(e)}")
    
    async def get_document_metadata(self, doc_id: str) -> Dict[str, Any]:
        """Get detailed metadata for a document."""
        return await self._make_request("GET", f"/api/v1/documents/{doc_id}/metadata")
    
    async def get_system_stats(self) -> Dict[str, Any]:
        """Get system statistics and metrics."""
        return await self._make_request("GET", "/stats")

# Global API client instance
api_client = RAGAPIClient()