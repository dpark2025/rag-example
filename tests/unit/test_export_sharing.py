#!/usr/bin/env python3
"""
Test script for export and sharing functionality

This script demonstrates the comprehensive export and sharing features
including PDF generation, secure link sharing, bulk operations, and 
API integrations.
"""

import asyncio
import json
import logging
import sys
from pathlib import Path
from datetime import datetime

# Add app directory to Python path
sys.path.append(str(Path(__file__).parent.parent.parent / "app"))

from export_manager import get_export_manager, ExportFormat, ExportType, ExportOptions, ExportRequest
from sharing_service import get_sharing_service, ShareRequest, ShareType, AccessLevel
from document_manager import get_document_manager

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_export_functionality():
    """Test export functionality with various formats."""
    logger.info("Testing export functionality...")
    
    export_manager = get_export_manager()
    doc_manager = get_document_manager()
    
    # Get available documents
    documents = await doc_manager.list_documents()
    if not documents:
        logger.warning("No documents available for testing. Please upload some documents first.")
        return
    
    test_doc = documents[0]
    logger.info(f"Testing with document: {test_doc.title}")
    
    # Test document exports in different formats
    formats_to_test = [ExportFormat.PDF, ExportFormat.MARKDOWN, ExportFormat.HTML, ExportFormat.JSON, ExportFormat.TEXT]
    
    for export_format in formats_to_test:
        try:
            logger.info(f"Exporting document as {export_format.value}...")
            
            options = ExportOptions(
                format=export_format,
                include_metadata=True,
                include_sources=True,
                include_timestamps=True
            )
            
            result = await export_manager.export_document(test_doc.doc_id, export_format, options)
            
            if result.success:
                logger.info(f"✅ {export_format.value} export successful: {result.filename} ({result.file_size} bytes)")
            else:
                logger.error(f"❌ {export_format.value} export failed: {result.error_message}")
                
        except Exception as e:
            logger.error(f"❌ Error exporting as {export_format.value}: {str(e)}")
    
    # Test chat conversation export
    logger.info("Testing chat conversation export...")
    
    sample_conversation = [
        {
            "role": "user",
            "content": "What is the main topic of the uploaded documents?",
            "timestamp": datetime.now().isoformat(),
            "message_id": "msg_1"
        },
        {
            "role": "assistant",
            "content": "Based on the uploaded documents, the main topics appear to be related to technical documentation and system architecture. The documents contain information about software development processes, API documentation, and system design patterns.",
            "timestamp": datetime.now().isoformat(),
            "message_id": "msg_2",
            "sources": [
                {"title": test_doc.title, "score": 0.85, "doc_id": test_doc.doc_id}
            ]
        },
        {
            "role": "user",
            "content": "Can you provide more details about the API documentation?",
            "timestamp": datetime.now().isoformat(),
            "message_id": "msg_3"
        },
        {
            "role": "assistant",
            "content": "The API documentation includes comprehensive endpoint descriptions, request/response schemas, authentication methods, and example usage. It follows RESTful principles and includes detailed error handling information.",
            "timestamp": datetime.now().isoformat(),
            "message_id": "msg_4",
            "sources": [
                {"title": test_doc.title, "score": 0.78, "doc_id": test_doc.doc_id}
            ]
        }
    ]
    
    try:
        chat_result = await export_manager.export_chat_conversation(
            sample_conversation, 
            ExportFormat.PDF,
            ExportOptions(
                format=ExportFormat.PDF,
                include_metadata=True,
                include_sources=True,
                include_timestamps=True
            )
        )
        
        if chat_result.success:
            logger.info(f"✅ Chat export successful: {chat_result.filename} ({chat_result.file_size} bytes)")
        else:
            logger.error(f"❌ Chat export failed: {chat_result.error_message}")
            
    except Exception as e:
        logger.error(f"❌ Error exporting chat: {str(e)}")
    
    # Test bulk export
    logger.info("Testing bulk export functionality...")
    
    try:
        bulk_requests = [
            ExportRequest(
                export_type=ExportType.DOCUMENT,
                format=ExportFormat.PDF,
                item_ids=[test_doc.doc_id],
                options={"include_metadata": True}
            ),
            ExportRequest(
                export_type=ExportType.DOCUMENT,
                format=ExportFormat.MARKDOWN,
                item_ids=[test_doc.doc_id],
                options={"include_metadata": True}
            )
        ]
        
        bulk_result = await export_manager.bulk_export(bulk_requests)
        
        if bulk_result.success:
            logger.info(f"✅ Bulk export successful: {bulk_result.zip_filename} ({bulk_result.file_size} bytes)")
            logger.info(f"   - Successful exports: {bulk_result.successful_exports}")
            logger.info(f"   - Failed exports: {bulk_result.failed_exports}")
            logger.info(f"   - Processing time: {bulk_result.processing_time:.2f}s")
        else:
            logger.error(f"❌ Bulk export failed")
            
    except Exception as e:
        logger.error(f"❌ Error in bulk export: {str(e)}")

async def test_sharing_functionality():
    """Test sharing functionality with access control."""
    logger.info("Testing sharing functionality...")
    
    sharing_service = get_sharing_service()
    doc_manager = get_document_manager()
    
    # Get available documents
    documents = await doc_manager.list_documents()
    if not documents:
        logger.warning("No documents available for sharing tests.")
        return
    
    test_doc = documents[0]
    logger.info(f"Testing sharing with document: {test_doc.title}")
    
    # Test document sharing with different access levels
    access_levels = [AccessLevel.VIEW, AccessLevel.DOWNLOAD, AccessLevel.EDIT]
    
    for access_level in access_levels:
        try:
            logger.info(f"Creating share link with {access_level.value} access...")
            
            share_request = ShareRequest(
                share_type=ShareType.DOCUMENT,
                item_id=test_doc.doc_id,
                access_level=access_level,
                expires_in_hours=24,
                custom_message=f"Shared document with {access_level.value} access for testing"
            )
            
            share_link = await sharing_service.create_share_link(share_request, "test_user")
            
            logger.info(f"✅ Share link created:")
            logger.info(f"   - Share ID: {share_link.share_id}")
            logger.info(f"   - Share URL: {share_link.share_url}")
            logger.info(f"   - Access Level: {share_link.access_level}")
            logger.info(f"   - Expires: {share_link.expires_at.isoformat() if share_link.expires_at else 'Never'}")
            
            # Test access validation
            is_valid, _, error_msg = await sharing_service.validate_access(
                share_link.share_token,
                ip_address="127.0.0.1",
                user_agent="Test User Agent"
            )
            
            if is_valid:
                logger.info(f"✅ Access validation successful for {access_level.value}")
                
                # Record access for analytics
                await sharing_service.record_access(
                    share_link.share_id,
                    "view",
                    ip_address="127.0.0.1",
                    user_agent="Test User Agent"
                )
                
            else:
                logger.error(f"❌ Access validation failed: {error_msg}")
                
        except Exception as e:
            logger.error(f"❌ Error creating share link for {access_level.value}: {str(e)}")
    
    # Test password-protected sharing
    try:
        logger.info("Testing password-protected sharing...")
        
        protected_request = ShareRequest(
            share_type=ShareType.DOCUMENT,
            item_id=test_doc.doc_id,
            access_level=AccessLevel.VIEW,
            expires_in_hours=24,
            password="test_password_123",
            custom_message="Password-protected share for testing"
        )
        
        protected_share = await sharing_service.create_share_link(protected_request, "test_user")
        
        logger.info(f"✅ Password-protected share created: {protected_share.share_id}")
        
        # Test access with correct password
        is_valid, _, _ = await sharing_service.validate_access(
            protected_share.share_token,
            password="test_password_123",
            ip_address="127.0.0.1"
        )
        
        if is_valid:
            logger.info("✅ Password validation successful")
        else:
            logger.error("❌ Password validation failed")
        
        # Test access with wrong password
        is_valid, _, error_msg = await sharing_service.validate_access(
            protected_share.share_token,
            password="wrong_password",
            ip_address="127.0.0.1"
        )
        
        if not is_valid:
            logger.info(f"✅ Wrong password correctly rejected: {error_msg}")
        else:
            logger.error("❌ Wrong password was accepted")
            
    except Exception as e:
        logger.error(f"❌ Error testing password protection: {str(e)}")
    
    # Test collaboration features
    try:
        logger.info("Testing collaboration features...")
        
        # Get a share link for collaboration
        shares = await sharing_service.list_user_shares("test_user")
        if shares:
            test_share = shares[0]
            
            # Create collaboration invite
            invite = await sharing_service.create_collaboration_invite(
                share_id=test_share.share_id,
                email="collaborator@example.com",
                access_level=AccessLevel.EDIT,
                invited_by="test_user",
                expires_in_hours=72,
                personal_message="Join me in collaborating on this document!"
            )
            
            logger.info(f"✅ Collaboration invite created:")
            logger.info(f"   - Invite ID: {invite.invite_id}")
            logger.info(f"   - Email: {invite.email}")
            logger.info(f"   - Access Level: {invite.access_level}")
            logger.info(f"   - Status: {invite.status}")
            
            # Test accepting the invitation
            success, share_link = await sharing_service.accept_collaboration_invite(invite.invite_id)
            
            if success:
                logger.info(f"✅ Collaboration invite accepted successfully")
            else:
                logger.error("❌ Failed to accept collaboration invite")
        
    except Exception as e:
        logger.error(f"❌ Error testing collaboration: {str(e)}")

async def test_analytics_and_management():
    """Test analytics and management features."""
    logger.info("Testing analytics and management features...")
    
    sharing_service = get_sharing_service()
    export_manager = get_export_manager()
    
    try:
        # Get user shares
        shares = await sharing_service.list_user_shares("test_user")
        logger.info(f"✅ Found {len(shares)} shares for test_user")
        
        if shares:
            test_share = shares[0]
            
            # Get analytics
            analytics = await sharing_service.get_share_analytics(test_share.share_id)
            if analytics:
                logger.info(f"✅ Share analytics:")
                logger.info(f"   - View count: {analytics.view_count}")
                logger.info(f"   - Download count: {analytics.download_count}")
                logger.info(f"   - Unique visitors: {analytics.unique_visitors}")
                logger.info(f"   - Last accessed: {analytics.last_accessed}")
                logger.info(f"   - Access history entries: {len(analytics.access_history)}")
            
            # Test extending expiration
            success = await sharing_service.extend_expiration(test_share.share_id, 24)
            if success:
                logger.info("✅ Share expiration extended successfully")
            else:
                logger.error("❌ Failed to extend share expiration")
        
        # Get export history
        exports = await export_manager.list_exports(10)
        logger.info(f"✅ Found {len(exports)} recent exports")
        
        for export in exports[:3]:  # Show first 3
            logger.info(f"   - {export.filename} ({export.format.value}) - {export.created_at}")
        
        # Generate security report
        security_report = await sharing_service.get_security_report()
        logger.info(f"✅ Security report generated:")
        logger.info(f"   - Total recent attempts: {security_report['total_recent_attempts']}")
        logger.info(f"   - Failed attempts: {security_report['failed_attempts']}")
        logger.info(f"   - Active shares: {security_report['active_shares']}")
        logger.info(f"   - Blocked IPs: {len(security_report['blocked_ips'])}")
        
    except Exception as e:
        logger.error(f"❌ Error testing analytics: {str(e)}")

async def main():
    """Main test function."""
    logger.info("Starting export and sharing functionality tests...")
    logger.info("=" * 60)
    
    try:
        # Test export functionality
        await test_export_functionality()
        logger.info("=" * 60)
        
        # Test sharing functionality  
        await test_sharing_functionality()
        logger.info("=" * 60)
        
        # Test analytics and management
        await test_analytics_and_management()
        logger.info("=" * 60)
        
        logger.info("✅ All tests completed!")
        
        # Cleanup expired items
        sharing_service = get_sharing_service()
        export_manager = get_export_manager()
        
        await sharing_service.cleanup_expired_shares()
        await export_manager.cleanup_expired_exports()
        
        logger.info("✅ Cleanup completed")
        
    except Exception as e:
        logger.error(f"❌ Test execution failed: {str(e)}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)