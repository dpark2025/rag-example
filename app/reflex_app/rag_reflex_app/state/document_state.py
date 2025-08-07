"""Document management state for upload, display, and operations."""

import reflex as rx
from typing import List, Dict, Optional, Any
from datetime import datetime
import asyncio
import httpx
import json
import uuid
from enum import Enum

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

class UploadStatus(str, Enum):
    """Upload processing status."""
    PENDING = "pending"
    VALIDATING = "validating"
    UPLOADING = "uploading"
    PROCESSING = "processing"
    INTELLIGENCE_ANALYSIS = "intelligence_analysis"
    INDEXING = "indexing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class UploadProgress(rx.Base):
    """Upload progress tracking."""
    task_id: str = ""
    filename: str = ""
    progress: int = 0
    status: str = "pending"
    message: str = ""
    error_message: str = ""
    doc_id: Optional[str] = None
    timestamp: str = ""

class DocumentState(rx.State):
    """State management for document operations."""
    
    # Document list management
    documents: List[DocumentInfo] = []
    is_loading_documents: bool = False
    
    # Upload management
    upload_progress: Dict[str, UploadProgress] = {}
    is_upload_modal_open: bool = False
    websocket_client_id: str = ""
    websocket_connected: bool = False
    
    # Real-time updates
    real_time_updates_enabled: bool = True
    last_update_timestamp: str = ""
    
    # Selection and operations
    selected_documents: List[str] = []
    selected_document_for_details: Optional[DocumentInfo] = None
    is_deleting: bool = False
    selection_mode: bool = False
    is_processing: bool = False
    
    # Search and filtering
    search_query: str = ""
    filter_type: str = "all"  # all, txt, processing, error
    sort_by: str = "newest"  # newest, oldest, name, size
    show_filter_panel: bool = False
    
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
            # Generate new client ID for next session
            self.websocket_client_id = str(uuid.uuid4())
    
    def clear_completed_uploads(self):
        """Clear completed upload progress items."""
        self.upload_progress = {
            filename: progress 
            for filename, progress in self.upload_progress.items()
            if progress.status not in ["completed", "error"]
        }
    
    async def load_documents(self, 
                           file_type: Optional[str] = None,
                           status: Optional[str] = None,
                           title_contains: Optional[str] = None,
                           limit: Optional[int] = None,
                           offset: Optional[int] = None):
        """Load document list from enhanced backend API."""
        self.is_loading_documents = True
        try:
            # Build query parameters
            params = {}
            if file_type:
                params["file_type"] = file_type
            if status:
                params["status"] = status
            if title_contains:
                params["title_contains"] = title_contains
            if limit is not None:
                params["limit"] = limit
            if offset is not None:
                params["offset"] = offset
            
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    "http://localhost:8000/api/v1/documents",
                    params=params
                )
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
                            status=doc.get("status", "ready"),
                            error_message=doc.get("error_message", "")
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
    
    def init_websocket_client(self):
        """Initialize WebSocket client ID for real-time updates."""
        if not self.websocket_client_id:
            self.websocket_client_id = str(uuid.uuid4())
    
    async def handle_file_upload(self, files: List[rx.UploadFile]):
        """Handle file upload with enhanced backend API and real-time tracking."""
        if not files:
            return
        
        # Initialize WebSocket client if needed
        self.init_websocket_client()
        
        # Handle single file vs bulk upload
        if len(files) == 1:
            await self._handle_single_file_upload(files[0])
        else:
            await self._handle_bulk_file_upload(files)
        
        # Reload documents list after upload
        await self.load_documents()
    
    async def _handle_single_file_upload(self, file: rx.UploadFile):
        """Handle single file upload with real-time status tracking."""
        filename = file.filename or "unknown"
        
        try:
            # Read file content
            content = await file.read()
            
            # Upload via enhanced API
            async with httpx.AsyncClient(timeout=300.0) as client:
                files_data = {
                    "file": (filename, content, file.content_type or "text/plain")
                }
                response = await client.post(
                    "http://localhost:8000/api/v1/documents/upload",
                    files=files_data
                )
                
                result = response.json()
                
                if response.status_code == 200 and result.get("success"):
                    # Track via task ID for real-time updates
                    task_id = result.get("task_id")
                    if task_id:
                        self.upload_progress[task_id] = UploadProgress(
                            task_id=task_id,
                            filename=filename,
                            progress=100.0,
                            status=result.get("status", "completed"),
                            doc_id=result.get("doc_id")
                        )
                else:
                    # Handle upload error
                    self.upload_progress[filename] = UploadProgress(
                        filename=filename,
                        progress=0.0,
                        status="failed",
                        error_message=result.get("message", "Upload failed")
                    )
                    
        except Exception as e:
            self.upload_progress[filename] = UploadProgress(
                filename=filename,
                progress=0.0,
                status="failed",
                error_message=str(e)
            )
    
    async def _handle_bulk_file_upload(self, files: List[rx.UploadFile]):
        """Handle bulk file upload with parallel processing."""
        try:
            # Prepare files for bulk upload
            files_data = []
            for file in files:
                content = await file.read()
                files_data.append(
                    ("files", (file.filename or "unknown", content, file.content_type or "text/plain"))
                )
            
            # Upload via bulk API
            async with httpx.AsyncClient(timeout=600.0) as client:
                response = await client.post(
                    "http://localhost:8000/api/v1/documents/bulk-upload",
                    files=files_data
                )
                
                if response.status_code == 200:
                    result = response.json()
                    
                    # Track bulk upload results
                    for i, task_id in enumerate(result.get("upload_tasks", [])):
                        filename = files[i].filename or f"file_{i}"
                        self.upload_progress[task_id] = UploadProgress(
                            task_id=task_id,
                            filename=filename,
                            progress=100.0,
                            status="completed"
                        )
                    
                    # Handle any errors
                    for error in result.get("errors", []):
                        filename = error.get("filename", "unknown")
                        self.upload_progress[filename] = UploadProgress(
                            filename=filename,
                            progress=0.0,
                            status="failed",
                            error_message=error.get("error", "Upload failed")
                        )
                else:
                    self.show_error_message(f"Bulk upload failed: {response.status_code}")
                    
        except Exception as e:
            self.show_error_message(f"Error in bulk upload: {str(e)}")
    
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
        visible_docs = self.get_filtered_documents
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
        """Delete selected documents using bulk delete API."""
        if not self.selected_documents:
            return
        
        self.is_deleting = True
        try:
            async with httpx.AsyncClient() as client:
                # Use bulk delete API for better performance
                response = await client.delete(
                    "http://localhost:8000/api/v1/documents/bulk",
                    json={"doc_ids": self.selected_documents}
                )
                
                if response.status_code == 200:
                    result = response.json()
                    if result.get("error_count", 0) > 0:
                        errors = result.get("errors", [])
                        error_msg = f"Some deletions failed: {'; '.join([e.get('error', '') for e in errors[:3]])}"
                        self.show_error_message(error_msg)
                else:
                    self.show_error_message(f"Bulk delete failed: {response.status_code}")
                        
            # Clear selection and reload
            self.selected_documents = []
            await self.load_documents()
            
        except Exception as e:
            self.show_error_message(f"Error deleting documents: {str(e)}")
        finally:
            self.is_deleting = False
    
    async def delete_single_document(self, doc_id: str):
        """Delete a single document using enhanced API."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.delete(f"http://localhost:8000/api/v1/documents/{doc_id}")
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
            elif self.filter_type == "pdf":
                docs = [d for d in docs if d.file_type == "pdf"]
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
    
    def open_settings(self):
        """Open settings modal or navigate to settings."""
        # For now, this is a placeholder - could navigate to settings page
        pass
    
    def toggle_filter_panel(self):
        """Toggle the filter panel visibility."""
        self.show_filter_panel = not self.show_filter_panel
    
    def toggle_sort_menu(self):
        """Toggle the sort menu visibility."""
        # For now, this is a placeholder
        pass
    
    def download_selected_documents(self):
        """Download selected documents."""
        # For now, this is a placeholder - could implement ZIP download
        pass
    
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
    
    async def get_document_status(self, doc_id: str) -> Optional[Dict[str, Any]]:
        """Get real-time document processing status."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"http://localhost:8000/api/v1/documents/{doc_id}/status")
                if response.status_code == 200:
                    return response.json()
                return None
        except Exception as e:
            self.show_error_message(f"Error getting document status: {str(e)}")
            return None
    
    async def get_storage_statistics(self) -> Optional[Dict[str, Any]]:
        """Get comprehensive storage statistics."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get("http://localhost:8000/api/v1/documents/stats")
                if response.status_code == 200:
                    return response.json()
                return None
        except Exception as e:
            self.show_error_message(f"Error getting storage stats: {str(e)}")
            return None
    
    def handle_websocket_message(self, message: str):
        """Handle incoming WebSocket progress updates."""
        try:
            data = json.loads(message)
            
            # Handle ping messages
            if data.get("type") == "ping":
                self.last_update_timestamp = data.get("timestamp", "")
                return
            
            # Handle upload progress updates
            task_id = data.get("task_id")
            if task_id:
                self.upload_progress[task_id] = UploadProgress(
                    task_id=task_id,
                    filename=data.get("filename", ""),
                    progress=data.get("progress", 0.0),
                    status=data.get("status", "unknown"),
                    message=data.get("message", ""),
                    error_message=data.get("error", ""),
                    doc_id=data.get("doc_id"),
                    timestamp=data.get("timestamp", "")
                )
                
                # Auto-reload documents when upload completes
                if data.get("status") == "completed":
                    # Schedule document reload (non-blocking)
                    asyncio.create_task(self.load_documents())
                    
        except json.JSONDecodeError as e:
            pass  # Ignore malformed messages
        except Exception as e:
            self.show_error_message(f"Error processing WebSocket message: {str(e)}")
    
    def enable_real_time_updates(self):
        """Enable real-time upload progress updates."""
        self.real_time_updates_enabled = True
        self.init_websocket_client()
    
    def disable_real_time_updates(self):
        """Disable real-time upload progress updates."""
        self.real_time_updates_enabled = False
        self.websocket_connected = False
    
    async def refresh_documents(self):
        """Refresh document list with current filters."""
        await self.load_documents(
            file_type=self.filter_type if self.filter_type != "all" else None,
            title_contains=self.search_query if self.search_query else None
        )
    
    @rx.var
    def websocket_url(self) -> str:
        """Get WebSocket URL for real-time updates."""
        if self.websocket_client_id:
            return f"ws://localhost:8000/api/v1/documents/ws/{self.websocket_client_id}"
        return ""
    
    @rx.var
    def upload_stats_summary(self) -> str:
        """Get upload statistics summary."""
        if not self.upload_progress:
            return "No active uploads"
        
        total = len(self.upload_progress)
        completed = len([p for p in self.upload_progress.values() if p.status == "completed"])
        failed = len([p for p in self.upload_progress.values() if p.status == "failed"])
        active = total - completed - failed
        
        if active > 0:
            return f"{active} uploading, {completed} completed, {failed} failed"
        else:
            return f"{completed} completed, {failed} failed"
    
    @rx.var
    def active_filter_count(self) -> int:
        """Count active filters."""
        count = 0
        if self.filter_type and self.filter_type != "all":
            count += 1
        if self.search_query and self.search_query.strip():
            count += 1
        if self.sort_by and self.sort_by != "newest":
            count += 1
        return count
    
    @rx.var
    def total_size_formatted(self) -> str:
        """Get total size of all documents formatted."""
        total_size = sum(doc.file_size for doc in self.documents)
        return self.format_file_size(total_size)
    
    @rx.var
    def total_chunks(self) -> int:
        """Get total number of chunks across all documents."""
        return sum(doc.chunk_count for doc in self.documents)
    
    @rx.var
    def all_selected(self) -> bool:
        """Check if all documents are selected."""
        if not self.documents:
            return False
        return len(self.selected_documents) == len(self.documents)
    
    @rx.var
    def some_selected(self) -> bool:
        """Check if some (but not all) documents are selected."""
        selected_count = len(self.selected_documents)
        total_count = len(self.documents)
        return selected_count > 0 and selected_count < total_count
    
    # Additional state variables for UI functionality
    view_mode: str = "grid"  # grid or list
    page_size: int = 20
    current_page: int = 1
    upload_in_progress: bool = False
    has_upload_errors: bool = False
    total_uploaded: int = 0
    show_confirmation_dialog: bool = False
    confirmation_message: str = ""
    
    def set_view_mode(self, mode: str):
        """Set document view mode (grid or list)."""
        self.view_mode = mode
    
    def next_page(self):
        """Go to next page."""
        if self.current_page < self.total_pages:
            self.current_page += 1
    
    def previous_page(self):
        """Go to previous page."""
        if self.current_page > 1:
            self.current_page -= 1
    
    def confirm_delete_selected(self):
        """Show confirmation dialog for deleting selected documents."""
        if not self.selected_documents:
            return
        
        count = len(self.selected_documents)
        self.confirmation_message = f"Are you sure you want to delete {count} selected document{'s' if count > 1 else ''}? This action cannot be undone."
        self.show_confirmation_dialog = True
    
    def cancel_confirmation(self):
        """Cancel the confirmation dialog."""
        self.show_confirmation_dialog = False
        self.confirmation_message = ""
    
    def set_show_confirmation_dialog(self, show: bool):
        """Set confirmation dialog visibility."""
        self.show_confirmation_dialog = show
    
    async def confirm_action(self):
        """Confirm and execute the pending action."""
        if self.show_confirmation_dialog:
            await self.delete_selected_documents()
        self.show_confirmation_dialog = False
        self.confirmation_message = ""
    
    def set_is_upload_modal_open(self, is_open: bool):
        """Set upload modal open state."""
        self.is_upload_modal_open = is_open
    
    def clear_all_uploads(self):
        """Clear all upload progress items."""
        self.upload_progress = {}
    
    @rx.var
    def total_pages(self) -> int:
        """Calculate total pages based on filtered documents and page size."""
        total_docs = len(self.get_filtered_documents)
        return max(1, (total_docs + self.page_size - 1) // self.page_size)
    
    @rx.var
    def start_index(self) -> int:
        """Get start index for current page."""
        return (self.current_page - 1) * self.page_size
    
    @rx.var
    def end_index(self) -> int:
        """Get end index for current page."""
        total_docs = len(self.get_filtered_documents)
        return min(self.start_index + self.page_size, total_docs)
    
    @rx.var
    def filtered_documents(self) -> List[DocumentInfo]:
        """Get paginated filtered documents for current page."""
        all_docs = self.get_filtered_documents
        start = self.start_index
        end = self.end_index
        return all_docs[start:end]
    
    @rx.var
    def completed_uploads(self) -> int:
        """Get count of completed uploads."""
        return len([p for p in self.upload_progress.values() if p.status == "completed"])
    
    @rx.var
    def total_uploads(self) -> int:
        """Get total upload count."""
        return len(self.upload_progress)
    
    def show_document_menu(self, doc_id: str):
        """Show document context menu."""
        # For now, this is a placeholder - could show a dropdown menu
        pass
    
    def view_document_details(self, doc_id: str):
        """View document details."""
        # For now, this is a placeholder - could show a details modal
        pass
    
    def download_document(self, doc_id: str):
        """Download a single document."""
        # For now, this is a placeholder - could trigger download
        pass
    
    def confirm_delete_document(self, doc_id: str):
        """Confirm deletion of a single document."""
        # Set up the confirmation for single document deletion
        doc = next((d for d in self.documents if d.doc_id == doc_id), None)
        if doc:
            self.confirmation_message = f"Are you sure you want to delete '{doc.title}'? This action cannot be undone."
            self.show_confirmation_dialog = True
            # Store the doc_id for the actual deletion
            self.selected_documents = [doc_id]
    
    # Additional UI state variables for document details modal
    show_document_details: bool = False
    selected_document_id: str = ""
    
    def set_show_document_details(self, show: bool):
        """Set document details modal visibility."""
        self.show_document_details = show
        if not show:
            self.selected_document_id = ""
    
    def close_document_details(self):
        """Close document details modal."""
        self.show_document_details = False
        self.selected_document_id = ""
    
    def is_selected(self, doc_id: str) -> bool:
        """Check if a document is selected - for use in components."""
        return doc_id in self.selected_documents