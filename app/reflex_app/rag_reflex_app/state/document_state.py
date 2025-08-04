"""Document management state for upload, display, and operations."""

import reflex as rx
from typing import List, Dict, Optional, Any
from datetime import datetime
import asyncio
import httpx

class DocumentInfo(rx.Base):
    """Document information model."""
    doc_id: str = ""
    title: str = ""
    file_type: str = ""
    upload_date: str = ""
    chunk_count: int = 0
    file_size: int = 0
    status: str = "ready"  # ready, processing, error
    error_message: str = ""

class UploadProgress(rx.Base):
    """Upload progress tracking."""
    filename: str = ""
    progress: float = 0.0
    status: str = "pending"  # pending, uploading, processing, completed, error
    error_message: str = ""

class DocumentState(rx.State):
    """State management for document operations."""
    
    # Document list management
    documents: List[DocumentInfo] = []
    is_loading_documents: bool = False
    
    # Upload management
    upload_progress: Dict[str, UploadProgress] = {}
    is_upload_modal_open: bool = False
    
    # Selection and operations
    selected_documents: List[str] = []
    is_deleting: bool = False
    
    # Search and filtering
    search_query: str = ""
    filter_type: str = "all"  # all, txt, processing, error
    sort_by: str = "newest"  # newest, oldest, name, size
    
    # Error handling
    error_message: str = ""
    show_error: bool = False
    
    # Modal state
    show_upload_modal: bool = False
    upload_status: str = ""
    
    def toggle_upload_modal(self):
        """Toggle the upload modal visibility."""
        self.show_upload_modal = not self.show_upload_modal
        if not self.show_upload_modal:
            self.upload_status = ""
    
    def clear_completed_uploads(self):
        """Clear completed upload progress items."""
        self.upload_progress = {
            filename: progress 
            for filename, progress in self.upload_progress.items()
            if progress.status not in ["completed", "error"]
        }
    
    async def load_documents(self):
        """Load document list from backend."""
        self.is_loading_documents = True
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get("http://localhost:8000/documents")
                if response.status_code == 200:
                    docs_data = response.json()
                    self.documents = [
                        DocumentInfo(
                            doc_id=str(doc.get("doc_id", "")),
                            title=doc.get("title", "Unknown"),
                            file_type=doc.get("file_type", "txt"),
                            upload_date=doc.get("upload_date", ""),
                            chunk_count=doc.get("chunk_count", 0),
                            file_size=doc.get("file_size", 0),
                            status=doc.get("status", "ready")
                        )
                        for doc in docs_data.get("documents", [])
                    ]
                else:
                    self.show_error_message(f"Failed to load documents: {response.status_code}")
        except Exception as e:
            self.show_error_message(f"Error loading documents: {str(e)}")
        finally:
            self.is_loading_documents = False
    
    def open_upload_modal(self):
        """Open the upload modal."""
        self.is_upload_modal_open = True
    
    def close_upload_modal(self):
        """Close the upload modal."""
        self.is_upload_modal_open = False
        self.upload_progress = {}
    
    async def handle_file_upload(self, files: List[rx.UploadFile]):
        """Handle file upload process."""
        if not files:
            return
        
        for file in files:
            filename = file.filename or "unknown"
            
            # Initialize progress tracking
            self.upload_progress[filename] = UploadProgress(
                filename=filename,
                progress=0.0,
                status="uploading"
            )
            
            try:
                # Read file content
                content = await file.read()
                
                # Update progress
                self.upload_progress[filename].progress = 50.0
                self.upload_progress[filename].status = "processing"
                
                # Upload to backend
                async with httpx.AsyncClient() as client:
                    files_data = {
                        "files": (filename, content, "text/plain")
                    }
                    response = await client.post(
                        "http://localhost:8000/documents/upload",
                        files=files_data
                    )
                    
                    if response.status_code == 200:
                        self.upload_progress[filename].progress = 100.0
                        self.upload_progress[filename].status = "completed"
                        # Reload documents list
                        await self.load_documents()
                    else:
                        self.upload_progress[filename].status = "error"
                        self.upload_progress[filename].error_message = f"Upload failed: {response.status_code}"
                        
            except Exception as e:
                self.upload_progress[filename].status = "error"
                self.upload_progress[filename].error_message = str(e)
    
    def toggle_document_selection(self, doc_id: str):
        """Toggle document selection for bulk operations."""
        if doc_id in self.selected_documents:
            self.selected_documents.remove(doc_id)
        else:
            self.selected_documents.append(doc_id)
    
    def is_document_selected(self, doc_id: str) -> bool:
        """Check if document is selected."""
        return doc_id in self.selected_documents
    
    def select_all_documents(self):
        """Select all visible documents."""
        visible_docs = self.get_filtered_documents()
        self.selected_documents = [doc.doc_id for doc in visible_docs]
    
    def clear_selection(self):
        """Clear all document selection."""
        self.selected_documents = []
    
    def toggle_select_all(self, checked: bool):
        """Toggle select all documents."""
        if checked:
            self.select_all_documents()
        else:
            self.clear_selection()
    
    async def delete_selected_documents(self):
        """Delete selected documents."""
        if not self.selected_documents:
            return
        
        self.is_deleting = True
        try:
            async with httpx.AsyncClient() as client:
                for doc_id in self.selected_documents:
                    response = await client.delete(f"http://localhost:8000/documents/{doc_id}")
                    if response.status_code != 200:
                        self.show_error_message(f"Failed to delete document {doc_id}")
                        
            # Clear selection and reload
            self.selected_documents = []
            await self.load_documents()
            
        except Exception as e:
            self.show_error_message(f"Error deleting documents: {str(e)}")
        finally:
            self.is_deleting = False
    
    async def delete_single_document(self, doc_id: str):
        """Delete a single document."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.delete(f"http://localhost:8000/documents/{doc_id}")
                if response.status_code == 200:
                    await self.load_documents()
                else:
                    self.show_error_message(f"Failed to delete document: {response.status_code}")
        except Exception as e:
            self.show_error_message(f"Error deleting document: {str(e)}")
    
    def set_search_query(self, query: str):
        """Set search query."""
        self.search_query = query
    
    def set_filter_type(self, filter_type: str):
        """Set document filter type."""
        self.filter_type = filter_type
    
    def set_sort_by(self, sort_by: str):
        """Set document sorting method."""
        self.sort_by = sort_by
    
    @rx.var
    def get_filtered_documents(self) -> List[DocumentInfo]:
        """Get filtered and sorted document list."""
        docs = self.documents.copy()
        
        # Apply type filter
        if self.filter_type != "all":
            if self.filter_type == "txt":
                docs = [d for d in docs if d.file_type == "txt"]
            elif self.filter_type == "processing":
                docs = [d for d in docs if d.status == "processing"]
            elif self.filter_type == "error":
                docs = [d for d in docs if d.status == "error"]
        
        # Apply search filter
        if self.search_query:
            query_lower = self.search_query.lower()
            docs = [d for d in docs if query_lower in d.title.lower()]
        
        # Apply sorting
        if self.sort_by == "newest":
            docs.sort(key=lambda x: x.upload_date, reverse=True)
        elif self.sort_by == "oldest":
            docs.sort(key=lambda x: x.upload_date)
        elif self.sort_by == "name":
            docs.sort(key=lambda x: x.title.lower())
        elif self.sort_by == "size":
            docs.sort(key=lambda x: x.file_size, reverse=True)
        
        return docs
    
    @rx.var
    def selected_count(self) -> int:
        """Get count of selected documents."""
        return len(self.selected_documents)
    
    @rx.var
    def total_documents(self) -> int:
        """Get total document count."""
        return len(self.documents)
    
    @rx.var
    def uploading_files(self) -> List[UploadProgress]:
        """Get list of files currently being uploaded."""
        return list(self.upload_progress.values())
    
    @rx.var 
    def filtered_count(self) -> int:
        """Get count of filtered documents."""
        docs = self.documents.copy()
        
        # Apply type filter
        if self.filter_type != "all":
            if self.filter_type == "txt":
                docs = [d for d in docs if d.file_type == "txt"]
            elif self.filter_type == "processing":
                docs = [d for d in docs if d.status == "processing"]
            elif self.filter_type == "error":
                docs = [d for d in docs if d.status == "error"]
        
        # Apply search filter
        if self.search_query:
            query_lower = self.search_query.lower()
            docs = [d for d in docs if query_lower in d.title.lower()]
            
        return len(docs)
    
    def show_error_message(self, message: str):
        """Show error message to user."""
        self.error_message = message
        self.show_error = True
    
    def clear_error(self):
        """Clear error message."""
        self.error_message = ""
        self.show_error = False
    
    def format_file_size(self, size_bytes: int) -> str:
        """Format file size for display."""
        if size_bytes < 1024:
            return f"{size_bytes} B"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:.1f} KB"
        else:
            return f"{size_bytes / (1024 * 1024):.1f} MB"
    
    def format_upload_date(self, date_str: str) -> str:
        """Format upload date for display."""
        try:
            dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            return dt.strftime("%Y-%m-%d %H:%M")
        except:
            return date_str