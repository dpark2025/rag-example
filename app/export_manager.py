"""
Authored by: Integration Specialist (Barry Young)
Date: 2025-08-05

Export Manager Service

Comprehensive document and chat export system supporting multiple formats including PDF generation,
bulk operations with ZIP compression, and integration with external systems.
"""

import asyncio
import io
import json
import logging
import os
import zipfile
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Optional, Any, Tuple, Union
from dataclasses import dataclass, asdict
from enum import Enum
import hashlib
import base64

from pydantic import BaseModel, Field
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle
from reportlab.platypus.flowables import HRFlowable
import markdown
from bs4 import BeautifulSoup

from document_manager import get_document_manager, DocumentMetadata
from error_handlers import handle_error, ApplicationError, ErrorCategory, ErrorSeverity, RecoveryAction

# Configure logging
logger = logging.getLogger(__name__)

class ExportFormat(str, Enum):
    """Supported export formats."""
    PDF = "pdf"
    MARKDOWN = "markdown"
    HTML = "html"
    JSON = "json"
    TEXT = "text"
    CSV = "csv"

class ExportType(str, Enum):
    """Types of exports supported."""
    DOCUMENT = "document"
    CHAT_CONVERSATION = "chat_conversation"
    DOCUMENT_COLLECTION = "document_collection"
    SYSTEM_REPORT = "system_report"
    ANALYTICS_REPORT = "analytics_report"

@dataclass
class ExportOptions:
    """Export configuration options."""
    format: ExportFormat
    include_metadata: bool = True
    include_sources: bool = True
    include_timestamps: bool = True
    include_metrics: bool = False
    page_size: str = "letter"  # letter, a4, legal
    font_size: int = 11
    margins: Dict[str, float] = None
    watermark: Optional[str] = None
    password_protect: bool = False
    password: Optional[str] = None
    
    def __post_init__(self):
        if self.margins is None:
            self.margins = {"top": 1.0, "bottom": 1.0, "left": 1.0, "right": 1.0}

class ExportRequest(BaseModel):
    """Export request model."""
    export_type: ExportType
    format: ExportFormat
    item_ids: List[str]  # Document IDs or conversation IDs
    options: Optional[Dict[str, Any]] = None
    filename: Optional[str] = None
    compression: bool = False
    bulk_operation: bool = False

class ExportResult(BaseModel):
    """Export operation result."""
    success: bool
    export_id: str
    filename: str
    file_path: Optional[str] = None
    file_size: int = 0
    format: ExportFormat
    export_type: ExportType
    created_at: datetime
    expires_at: Optional[datetime] = None
    download_count: int = 0
    error_message: str = ""
    metadata: Dict[str, Any] = Field(default_factory=dict)

class BulkExportResult(BaseModel):
    """Bulk export operation result."""
    success: bool
    export_id: str
    zip_filename: str
    file_path: Optional[str] = None
    file_size: int = 0
    individual_exports: List[ExportResult] = Field(default_factory=list)
    total_items: int = 0
    successful_exports: int = 0
    failed_exports: int = 0
    processing_time: float = 0.0
    created_at: datetime
    expires_at: Optional[datetime] = None

class ExportManager:
    """
    Comprehensive export management system supporting multiple formats,
    bulk operations, and external system integrations.
    """
    
    def __init__(self, export_dir: str = "exports", temp_dir: str = "temp_exports"):
        """Initialize export manager."""
        self.export_dir = Path(export_dir)
        self.temp_dir = Path(temp_dir)
        self.export_dir.mkdir(exist_ok=True)
        self.temp_dir.mkdir(exist_ok=True)
        
        # Export tracking
        self.active_exports: Dict[str, ExportResult] = {}
        self.export_history: List[ExportResult] = []
        
        # PDF styles
        self.styles = getSampleStyleSheet()
        self._setup_pdf_styles()
        
        # Document manager instance
        self._doc_manager = None
    
    @property
    def doc_manager(self):
        """Lazy-loaded document manager."""
        if self._doc_manager is None:
            self._doc_manager = get_document_manager()
        return self._doc_manager
    
    def _setup_pdf_styles(self):
        """Setup custom PDF styles."""
        # Title style
        self.styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=self.styles['Title'],
            fontSize=18,
            spaceAfter=20,
            textColor=colors.HexColor('#2E3440')
        ))
        
        # Subtitle style
        self.styles.add(ParagraphStyle(
            name='CustomSubtitle',
            parent=self.styles['Heading2'],
            fontSize=14,
            spaceAfter=12,
            textColor=colors.HexColor('#4C566A')
        ))
        
        # Message style for chat exports
        self.styles.add(ParagraphStyle(
            name='ChatMessage',
            parent=self.styles['Normal'],
            fontSize=10,
            spaceAfter=8,
            leftIndent=20
        ))
        
        # Metadata style
        self.styles.add(ParagraphStyle(
            name='Metadata',
            parent=self.styles['Normal'],
            fontSize=9,
            textColor=colors.HexColor('#6C7B95'),
            leftIndent=10
        ))
    
    async def export_document(
        self, 
        doc_id: str, 
        format: ExportFormat, 
        options: Optional[ExportOptions] = None
    ) -> ExportResult:
        """Export a single document to specified format."""
        try:
            if options is None:
                options = ExportOptions(format=format)
            
            # Get document data
            doc_metadata = await self.doc_manager.get_document_metadata(doc_id)
            if not doc_metadata:
                raise ApplicationError(
                    message=f"Document {doc_id} not found",
                    category=ErrorCategory.VALIDATION,
                    severity=ErrorSeverity.ERROR,
                    recovery_action=RecoveryAction.USER_INTERVENTION
                )
            
            # Get document content
            doc_content = await self.doc_manager.get_document_content(doc_id)
            
            # Generate export ID
            export_id = self._generate_export_id()
            
            # Create filename if not provided
            filename = self._generate_filename(
                doc_metadata.title, 
                format, 
                ExportType.DOCUMENT
            )
            
            # Export based on format
            if format == ExportFormat.PDF:
                file_path = await self._export_document_pdf(
                    doc_metadata, doc_content, filename, options
                )
            elif format == ExportFormat.MARKDOWN:
                file_path = await self._export_document_markdown(
                    doc_metadata, doc_content, filename, options
                )
            elif format == ExportFormat.HTML:
                file_path = await self._export_document_html(
                    doc_metadata, doc_content, filename, options
                )
            elif format == ExportFormat.JSON:
                file_path = await self._export_document_json(
                    doc_metadata, doc_content, filename, options
                )
            elif format == ExportFormat.TEXT:
                file_path = await self._export_document_text(
                    doc_metadata, doc_content, filename, options
                )
            else:
                raise ApplicationError(
                    message=f"Unsupported export format: {format}",
                    category=ErrorCategory.VALIDATION,
                    severity=ErrorSeverity.ERROR,
                    recovery_action=RecoveryAction.USER_INTERVENTION
                )
            
            # Get file size
            file_size = os.path.getsize(file_path) if file_path else 0
            
            # Create export result
            result = ExportResult(
                success=True,
                export_id=export_id,
                filename=filename,
                file_path=str(file_path),
                file_size=file_size,
                format=format,
                export_type=ExportType.DOCUMENT,
                created_at=datetime.now(),
                expires_at=datetime.now() + timedelta(days=7),
                metadata={
                    "doc_id": doc_id,
                    "title": doc_metadata.title,
                    "original_filename": doc_metadata.original_filename
                }
            )
            
            # Track export
            self.active_exports[export_id] = result
            self.export_history.append(result)
            
            logger.info(f"Document {doc_id} exported successfully as {format.value}")
            return result
            
        except Exception as e:
            error_msg = f"Failed to export document {doc_id}: {str(e)}"
            logger.error(error_msg)
            
            return ExportResult(
                success=False,
                export_id=self._generate_export_id(),
                filename="",
                format=format,
                export_type=ExportType.DOCUMENT,
                created_at=datetime.now(),
                error_message=error_msg
            )
    
    async def export_chat_conversation(
        self, 
        conversation_data: List[Dict[str, Any]], 
        format: ExportFormat,
        options: Optional[ExportOptions] = None
    ) -> ExportResult:
        """Export chat conversation to specified format."""
        try:
            if options is None:
                options = ExportOptions(format=format)
            
            # Generate export ID and filename
            export_id = self._generate_export_id()
            filename = self._generate_filename(
                "chat_conversation", 
                format, 
                ExportType.CHAT_CONVERSATION
            )
            
            # Export based on format
            if format == ExportFormat.PDF:
                file_path = await self._export_chat_pdf(
                    conversation_data, filename, options
                )
            elif format == ExportFormat.MARKDOWN:
                file_path = await self._export_chat_markdown(
                    conversation_data, filename, options
                )
            elif format == ExportFormat.HTML:
                file_path = await self._export_chat_html(
                    conversation_data, filename, options
                )
            elif format == ExportFormat.JSON:
                file_path = await self._export_chat_json(
                    conversation_data, filename, options
                )
            elif format == ExportFormat.TEXT:
                file_path = await self._export_chat_text(
                    conversation_data, filename, options
                )
            else:
                raise ApplicationError(
                    message=f"Unsupported export format: {format}",
                    category=ErrorCategory.VALIDATION,
                    severity=ErrorSeverity.ERROR,
                    recovery_action=RecoveryAction.USER_INTERVENTION
                )
            
            # Get file size
            file_size = os.path.getsize(file_path) if file_path else 0
            
            # Create export result
            result = ExportResult(
                success=True,
                export_id=export_id,
                filename=filename,
                file_path=str(file_path),
                file_size=file_size,
                format=format,
                export_type=ExportType.CHAT_CONVERSATION,
                created_at=datetime.now(),
                expires_at=datetime.now() + timedelta(days=7),
                metadata={
                    "message_count": len(conversation_data),
                    "export_timestamp": datetime.now().isoformat()
                }
            )
            
            # Track export
            self.active_exports[export_id] = result
            self.export_history.append(result)
            
            logger.info(f"Chat conversation exported successfully as {format.value}")
            return result
            
        except Exception as e:
            error_msg = f"Failed to export chat conversation: {str(e)}"
            logger.error(error_msg)
            
            return ExportResult(
                success=False,
                export_id=self._generate_export_id(),
                filename="",
                format=format,
                export_type=ExportType.CHAT_CONVERSATION,
                created_at=datetime.now(),
                error_message=error_msg
            )
    
    async def bulk_export(
        self, 
        export_requests: List[ExportRequest]
    ) -> BulkExportResult:
        """Perform bulk export operations with ZIP compression."""
        start_time = datetime.now()
        export_id = self._generate_export_id()
        zip_filename = f"bulk_export_{export_id}_{start_time.strftime('%Y%m%d_%H%M%S')}.zip"
        zip_path = self.export_dir / zip_filename
        
        individual_exports = []
        successful_exports = 0
        failed_exports = 0
        
        try:
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                
                for request in export_requests:
                    try:
                        if request.export_type == ExportType.DOCUMENT:
                            for doc_id in request.item_ids:
                                options = ExportOptions(**request.options) if request.options else ExportOptions(format=request.format)
                                result = await self.export_document(doc_id, request.format, options)
                                
                                if result.success and result.file_path:
                                    # Add to ZIP
                                    zip_file.write(result.file_path, result.filename)
                                    # Clean up temporary file
                                    os.remove(result.file_path)
                                    result.file_path = None  # Clear path since it's in ZIP
                                    successful_exports += 1
                                else:
                                    failed_exports += 1
                                
                                individual_exports.append(result)
                        
                        elif request.export_type == ExportType.CHAT_CONVERSATION:
                            # For chat exports, we'd need conversation data
                            # This would be passed in the request or retrieved from storage
                            logger.warning("Chat conversation bulk export not fully implemented")
                            failed_exports += len(request.item_ids)
                        
                    except Exception as e:
                        logger.error(f"Failed to process export request: {str(e)}")
                        failed_exports += len(request.item_ids)
            
            # Get ZIP file size
            file_size = os.path.getsize(zip_path)
            
            # Create bulk export result
            result = BulkExportResult(
                success=successful_exports > 0,
                export_id=export_id,
                zip_filename=zip_filename,
                file_path=str(zip_path),
                file_size=file_size,
                individual_exports=individual_exports,
                total_items=sum(len(req.item_ids) for req in export_requests),
                successful_exports=successful_exports,
                failed_exports=failed_exports,
                processing_time=(datetime.now() - start_time).total_seconds(),
                created_at=start_time,
                expires_at=datetime.now() + timedelta(days=7)
            )
            
            logger.info(f"Bulk export completed: {successful_exports} successful, {failed_exports} failed")
            return result
            
        except Exception as e:
            error_msg = f"Bulk export failed: {str(e)}"
            logger.error(error_msg)
            
            # Clean up ZIP file if it exists
            if zip_path.exists():
                os.remove(zip_path)
            
            return BulkExportResult(
                success=False,
                export_id=export_id,
                zip_filename="",
                total_items=sum(len(req.item_ids) for req in export_requests),
                failed_exports=sum(len(req.item_ids) for req in export_requests),
                processing_time=(datetime.now() - start_time).total_seconds(),
                created_at=start_time
            )
    
    # Document export format implementations
    
    async def _export_document_pdf(
        self, 
        metadata: DocumentMetadata, 
        content: str,
        filename: str, 
        options: ExportOptions
    ) -> str:
        """Export document as PDF."""
        file_path = self.export_dir / filename
        
        # Create PDF document
        doc = SimpleDocTemplate(
            str(file_path),
            pagesize=letter if options.page_size == "letter" else A4,
            rightMargin=options.margins["right"] * inch,
            leftMargin=options.margins["left"] * inch,
            topMargin=options.margins["top"] * inch,
            bottomMargin=options.margins["bottom"] * inch
        )
        
        # Build content
        story = []
        
        # Title
        story.append(Paragraph(metadata.title, self.styles['CustomTitle']))
        story.append(Spacer(1, 12))
        
        # Metadata section
        if options.include_metadata:
            story.append(Paragraph("Document Information", self.styles['CustomSubtitle']))
            
            metadata_info = [
                f"<b>Filename:</b> {metadata.original_filename}",
                f"<b>File Type:</b> {metadata.file_type}",
                f"<b>File Size:</b> {self._format_file_size(metadata.file_size)}",
                f"<b>Upload Date:</b> {metadata.upload_timestamp}",
                f"<b>Document Type:</b> {metadata.document_type}",
                f"<b>Chunks:</b> {metadata.chunk_count}"
            ]
            
            if metadata.page_count:
                metadata_info.append(f"<b>Pages:</b> {metadata.page_count}")
            
            for info in metadata_info:
                story.append(Paragraph(info, self.styles['Metadata']))
            
            story.append(Spacer(1, 20))
            story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#E5E9F0')))
            story.append(Spacer(1, 20))
        
        # Document content
        story.append(Paragraph("Content", self.styles['CustomSubtitle']))
        
        # Split content into paragraphs and add to story
        paragraphs = content.split('\n\n')
        for paragraph in paragraphs:
            if paragraph.strip():
                story.append(Paragraph(paragraph.strip(), self.styles['Normal']))
                story.append(Spacer(1, 6))
        
        # Build PDF
        doc.build(story)
        
        return str(file_path)
    
    async def _export_document_markdown(
        self, 
        metadata: DocumentMetadata, 
        content: str,
        filename: str, 
        options: ExportOptions
    ) -> str:
        """Export document as Markdown."""
        file_path = self.export_dir / filename
        
        markdown_content = []
        
        # Title
        markdown_content.append(f"# {metadata.title}\n")
        
        # Metadata
        if options.include_metadata:
            markdown_content.append("## Document Information\n")
            markdown_content.append(f"- **Filename:** {metadata.original_filename}")
            markdown_content.append(f"- **File Type:** {metadata.file_type}")
            markdown_content.append(f"- **File Size:** {self._format_file_size(metadata.file_size)}")
            markdown_content.append(f"- **Upload Date:** {metadata.upload_timestamp}")
            markdown_content.append(f"- **Document Type:** {metadata.document_type}")
            markdown_content.append(f"- **Chunks:** {metadata.chunk_count}")
            
            if metadata.page_count:
                markdown_content.append(f"- **Pages:** {metadata.page_count}")
            
            markdown_content.append("\n---\n")
        
        # Content
        markdown_content.append("## Content\n")
        markdown_content.append(content)
        
        # Write to file
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(markdown_content))
        
        return str(file_path)
    
    async def _export_document_html(
        self, 
        metadata: DocumentMetadata, 
        content: str,
        filename: str, 
        options: ExportOptions
    ) -> str:
        """Export document as HTML."""
        file_path = self.export_dir / filename
        
        html_content = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>{metadata.title}</title>
            <style>
                body {{
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                    line-height: 1.6;
                    color: #333;
                    max-width: 800px;
                    margin: 0 auto;
                    padding: 20px;
                }}
                .metadata {{
                    background: #f8f9fa;
                    padding: 20px;
                    border-radius: 8px;
                    margin: 20px 0;
                }}
                .content {{
                    white-space: pre-wrap;
                }}
                hr {{
                    border: none;
                    border-top: 1px solid #e1e5e9;
                    margin: 30px 0;
                }}
            </style>
        </head>
        <body>
            <h1>{metadata.title}</h1>
        """
        
        if options.include_metadata:
            html_content += f"""
            <div class="metadata">
                <h2>Document Information</h2>
                <ul>
                    <li><strong>Filename:</strong> {metadata.original_filename}</li>
                    <li><strong>File Type:</strong> {metadata.file_type}</li>
                    <li><strong>File Size:</strong> {self._format_file_size(metadata.file_size)}</li>
                    <li><strong>Upload Date:</strong> {metadata.upload_timestamp}</li>
                    <li><strong>Document Type:</strong> {metadata.document_type}</li>
                    <li><strong>Chunks:</strong> {metadata.chunk_count}</li>
            """
            
            if metadata.page_count:
                html_content += f"<li><strong>Pages:</strong> {metadata.page_count}</li>"
            
            html_content += """
                </ul>
            </div>
            <hr>
            """
        
        html_content += f"""
            <h2>Content</h2>
            <div class="content">{self._escape_html(content)}</div>
        </body>
        </html>
        """
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        return str(file_path)
    
    async def _export_document_json(
        self, 
        metadata: DocumentMetadata, 
        content: str,
        filename: str, 
        options: ExportOptions
    ) -> str:
        """Export document as JSON."""
        file_path = self.export_dir / filename
        
        export_data = {
            "document": {
                "metadata": metadata.to_dict(),
                "content": content,
                "export_info": {
                    "format": ExportFormat.JSON.value,
                    "export_timestamp": datetime.now().isoformat(),
                    "options": asdict(options)
                }
            }
        }
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)
        
        return str(file_path)
    
    async def _export_document_text(
        self, 
        metadata: DocumentMetadata, 
        content: str,
        filename: str, 
        options: ExportOptions
    ) -> str:
        """Export document as plain text."""
        file_path = self.export_dir / filename
        
        text_content = []
        
        # Title
        text_content.append(f"DOCUMENT: {metadata.title}")
        text_content.append("=" * (len(metadata.title) + 10))
        text_content.append("")
        
        # Metadata
        if options.include_metadata:
            text_content.append("DOCUMENT INFORMATION:")
            text_content.append(f"Filename: {metadata.original_filename}")
            text_content.append(f"File Type: {metadata.file_type}")
            text_content.append(f"File Size: {self._format_file_size(metadata.file_size)}")
            text_content.append(f"Upload Date: {metadata.upload_timestamp}")
            text_content.append(f"Document Type: {metadata.document_type}")
            text_content.append(f"Chunks: {metadata.chunk_count}")
            
            if metadata.page_count:
                text_content.append(f"Pages: {metadata.page_count}")
            
            text_content.append("")
            text_content.append("-" * 50)
            text_content.append("")
        
        # Content
        text_content.append("CONTENT:")
        text_content.append("")
        text_content.append(content)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(text_content))
        
        return str(file_path)
    
    # Chat export format implementations
    
    async def _export_chat_pdf(
        self, 
        conversation_data: List[Dict[str, Any]], 
        filename: str, 
        options: ExportOptions
    ) -> str:
        """Export chat conversation as PDF."""
        file_path = self.export_dir / filename
        
        doc = SimpleDocTemplate(
            str(file_path),
            pagesize=letter if options.page_size == "letter" else A4,
            rightMargin=options.margins["right"] * inch,
            leftMargin=options.margins["left"] * inch,
            topMargin=options.margins["top"] * inch,
            bottomMargin=options.margins["bottom"] * inch
        )
        
        story = []
        
        # Title
        story.append(Paragraph("Chat Conversation", self.styles['CustomTitle']))
        story.append(Spacer(1, 12))
        
        # Metadata
        if options.include_metadata:
            story.append(Paragraph("Conversation Information", self.styles['CustomSubtitle']))
            story.append(Paragraph(f"<b>Messages:</b> {len(conversation_data)}", self.styles['Metadata']))
            story.append(Paragraph(f"<b>Exported:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", self.styles['Metadata']))
            story.append(Spacer(1, 20))
            story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#E5E9F0')))
            story.append(Spacer(1, 20))
        
        # Messages
        for i, message in enumerate(conversation_data):
            role = message.get('role', 'unknown')
            content = message.get('content', '')
            timestamp = message.get('timestamp', '')
            
            # Message header
            header_text = f"<b>{role.upper()}</b>"
            if options.include_timestamps and timestamp:
                header_text += f" - {timestamp}"
            
            story.append(Paragraph(header_text, self.styles['CustomSubtitle']))
            
            # Message content
            story.append(Paragraph(content, self.styles['ChatMessage']))
            
            # Sources if available
            if options.include_sources and 'sources' in message and message['sources']:
                story.append(Paragraph("<b>Sources:</b>", self.styles['Metadata']))
                for source in message['sources']:
                    source_text = f"• {source.get('title', 'Unknown')} (Score: {source.get('score', 'N/A')})"
                    story.append(Paragraph(source_text, self.styles['Metadata']))
            
            # Add spacing between messages
            story.append(Spacer(1, 15))
            
            # Page break every 10 messages for readability
            if (i + 1) % 10 == 0 and i < len(conversation_data) - 1:
                story.append(PageBreak())
        
        doc.build(story)
        return str(file_path)
    
    async def _export_chat_markdown(
        self, 
        conversation_data: List[Dict[str, Any]], 
        filename: str, 
        options: ExportOptions
    ) -> str:
        """Export chat conversation as Markdown."""
        file_path = self.export_dir / filename
        
        markdown_content = []
        
        # Title
        markdown_content.append("# Chat Conversation\n")
        
        # Metadata
        if options.include_metadata:
            markdown_content.append("## Conversation Information\n")
            markdown_content.append(f"- **Messages:** {len(conversation_data)}")
            markdown_content.append(f"- **Exported:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            markdown_content.append("\n---\n")
        
        # Messages
        for message in conversation_data:
            role = message.get('role', 'unknown')
            content = message.get('content', '')
            timestamp = message.get('timestamp', '')
            
            # Message header
            header = f"## {role.upper()}"
            if options.include_timestamps and timestamp:
                header += f" - {timestamp}"
            
            markdown_content.append(header)
            markdown_content.append("")
            markdown_content.append(content)
            markdown_content.append("")
            
            # Sources if available
            if options.include_sources and 'sources' in message and message['sources']:
                markdown_content.append("**Sources:**")
                for source in message['sources']:
                    source_text = f"- {source.get('title', 'Unknown')} (Score: {source.get('score', 'N/A')})"
                    markdown_content.append(source_text)
                markdown_content.append("")
            
            markdown_content.append("---\n")
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(markdown_content))
        
        return str(file_path)
    
    async def _export_chat_html(
        self, 
        conversation_data: List[Dict[str, Any]], 
        filename: str, 
        options: ExportOptions
    ) -> str:
        """Export chat conversation as HTML."""
        file_path = self.export_dir / filename
        
        html_content = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Chat Conversation</title>
            <style>
                body {{
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                    line-height: 1.6;
                    color: #333;
                    max-width: 800px;
                    margin: 0 auto;
                    padding: 20px;
                }}
                .message {{
                    margin: 20px 0;
                    padding: 15px;
                    border-radius: 8px;
                    border-left: 4px solid #007acc;
                }}
                .user {{
                    background: #f0f7ff;
                    border-left-color: #007acc;
                }}
                .assistant {{
                    background: #f8f9fa;
                    border-left-color: #28a745;
                }}
                .message-header {{
                    font-weight: bold;
                    margin-bottom: 10px;
                    color: #495057;
                }}
                .sources {{
                    margin-top: 10px;
                    font-size: 0.9em;
                    color: #6c757d;
                }}
                .metadata {{
                    background: #f8f9fa;
                    padding: 20px;
                    border-radius: 8px;
                    margin: 20px 0;
                }}
            </style>
        </head>
        <body>
            <h1>Chat Conversation</h1>
        """
        
        if options.include_metadata:
            html_content += f"""
            <div class="metadata">
                <h2>Conversation Information</h2>
                <ul>
                    <li><strong>Messages:</strong> {len(conversation_data)}</li>
                    <li><strong>Exported:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</li>
                </ul>
            </div>
            """
        
        for message in conversation_data:
            role = message.get('role', 'unknown')
            content = message.get('content', '')
            timestamp = message.get('timestamp', '')
            
            role_class = 'user' if role == 'user' else 'assistant'
            
            html_content += f'<div class="message {role_class}">'
            
            # Message header
            header = f"{role.upper()}"
            if options.include_timestamps and timestamp:
                header += f" - {timestamp}"
            
            html_content += f'<div class="message-header">{header}</div>'
            html_content += f'<div class="message-content">{self._escape_html(content)}</div>'
            
            # Sources if available
            if options.include_sources and 'sources' in message and message['sources']:
                html_content += '<div class="sources"><strong>Sources:</strong><ul>'
                for source in message['sources']:
                    source_title = source.get('title', 'Unknown')
                    source_score = source.get('score', 'N/A')
                    html_content += f'<li>{self._escape_html(source_title)} (Score: {source_score})</li>'
                html_content += '</ul></div>'
            
            html_content += '</div>'
        
        html_content += """
        </body>
        </html>
        """
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        return str(file_path)
    
    async def _export_chat_json(
        self, 
        conversation_data: List[Dict[str, Any]], 
        filename: str, 
        options: ExportOptions
    ) -> str:
        """Export chat conversation as JSON."""
        file_path = self.export_dir / filename
        
        export_data = {
            "conversation": {
                "messages": conversation_data,
                "export_info": {
                    "format": ExportFormat.JSON.value,
                    "export_timestamp": datetime.now().isoformat(),
                    "message_count": len(conversation_data),
                    "options": asdict(options)
                }
            }
        }
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)
        
        return str(file_path)
    
    async def _export_chat_text(
        self, 
        conversation_data: List[Dict[str, Any]], 
        filename: str, 
        options: ExportOptions
    ) -> str:
        """Export chat conversation as plain text."""
        file_path = self.export_dir / filename
        
        text_content = []
        
        # Title
        text_content.append("CHAT CONVERSATION")
        text_content.append("=" * 20)
        text_content.append("")
        
        # Metadata
        if options.include_metadata:
            text_content.append("CONVERSATION INFORMATION:")
            text_content.append(f"Messages: {len(conversation_data)}")
            text_content.append(f"Exported: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            text_content.append("")
            text_content.append("-" * 50)
            text_content.append("")
        
        # Messages
        for message in conversation_data:
            role = message.get('role', 'unknown')
            content = message.get('content', '')
            timestamp = message.get('timestamp', '')
            
            # Message header
            header = f"{role.upper()}"
            if options.include_timestamps and timestamp:
                header += f" - {timestamp}"
            
            text_content.append(header)
            text_content.append("-" * len(header))
            text_content.append(content)
            text_content.append("")
            
            # Sources if available
            if options.include_sources and 'sources' in message and message['sources']:
                text_content.append("SOURCES:")
                for source in message['sources']:
                    source_text = f"  • {source.get('title', 'Unknown')} (Score: {source.get('score', 'N/A')})"
                    text_content.append(source_text)
                text_content.append("")
            
            text_content.append("=" * 50)
            text_content.append("")
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(text_content))
        
        return str(file_path)
    
    # Utility methods
    
    def _generate_export_id(self) -> str:
        """Generate unique export ID."""
        timestamp = datetime.now().isoformat()
        return hashlib.md5(timestamp.encode()).hexdigest()[:12]
    
    def _generate_filename(self, base_name: str, format: ExportFormat, export_type: ExportType) -> str:
        """Generate filename for export."""
        # Clean base name
        safe_name = "".join(c for c in base_name if c.isalnum() or c in ('-', '_', ' ')).strip()
        safe_name = safe_name.replace(' ', '_')[:50]  # Limit length
        
        # Add timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Create filename
        filename = f"{safe_name}_{export_type.value}_{timestamp}.{format.value}"
        
        return filename
    
    def _format_file_size(self, size_bytes: int) -> str:
        """Format file size in human readable format."""
        if size_bytes == 0:
            return "0 B"
        
        size_names = ["B", "KB", "MB", "GB"]
        i = 0
        while size_bytes >= 1024 and i < len(size_names) - 1:
            size_bytes /= 1024.0
            i += 1
        
        return f"{size_bytes:.1f} {size_names[i]}"
    
    def _escape_html(self, text: str) -> str:
        """Escape HTML special characters."""
        return (text.replace('&', '&amp;')
                   .replace('<', '&lt;')
                   .replace('>', '&gt;')
                   .replace('"', '&quot;')
                   .replace("'", '&#x27;'))
    
    # Export management methods
    
    async def get_export_status(self, export_id: str) -> Optional[Union[ExportResult, BulkExportResult]]:
        """Get status of an export operation."""
        return self.active_exports.get(export_id)
    
    async def list_exports(self, limit: int = 50) -> List[Union[ExportResult, BulkExportResult]]:
        """List recent exports."""
        return self.export_history[-limit:]
    
    async def delete_export(self, export_id: str) -> bool:
        """Delete an export and its files."""
        try:
            export_result = self.active_exports.get(export_id)
            if not export_result:
                return False
            
            # Delete file if it exists
            if export_result.file_path and os.path.exists(export_result.file_path):
                os.remove(export_result.file_path)
            
            # Remove from tracking
            if export_id in self.active_exports:
                del self.active_exports[export_id]
            
            logger.info(f"Export {export_id} deleted successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete export {export_id}: {str(e)}")
            return False
    
    async def cleanup_expired_exports(self):
        """Clean up expired exports."""
        current_time = datetime.now()
        expired_exports = []
        
        for export_id, export_result in self.active_exports.items():
            if export_result.expires_at and current_time > export_result.expires_at:
                expired_exports.append(export_id)
        
        for export_id in expired_exports:
            await self.delete_export(export_id)
        
        logger.info(f"Cleaned up {len(expired_exports)} expired exports")

# Global export manager instance
_export_manager = None

def get_export_manager() -> ExportManager:
    """Get global export manager instance."""
    global _export_manager
    if _export_manager is None:
        _export_manager = ExportManager()
    return _export_manager