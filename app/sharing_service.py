"""
Authored by: Integration Specialist (Barry Young)
Date: 2025-08-05

Sharing Service

Secure link sharing system with access control, expiration management, and collaboration features.
Provides enterprise-grade sharing capabilities with permissions, analytics, and audit trails.
"""

import asyncio
import hashlib
import logging
import secrets
import uuid
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import List, Dict, Optional, Any, Set, Tuple
from dataclasses import dataclass, asdict, field
import json
import aiofiles

from pydantic import BaseModel, Field, field_validator, ConfigDict, field_serializer
from .error_handlers import handle_error, ApplicationError, ErrorCategory, ErrorSeverity, RecoveryAction

# Configure logging
logger = logging.getLogger(__name__)

class ShareType(str, Enum):
    """Types of shareable content."""
    DOCUMENT = "document"
    CHAT_CONVERSATION = "chat_conversation"
    EXPORT_FILE = "export_file"
    COLLECTION = "collection"

class AccessLevel(str, Enum):
    """Access levels for shared content."""
    VIEW = "view"
    DOWNLOAD = "download"
    EDIT = "edit"
    ADMIN = "admin"

class ShareStatus(str, Enum):
    """Status of shared links."""
    ACTIVE = "active"
    EXPIRED = "expired"
    REVOKED = "revoked"
    SUSPENDED = "suspended"

@dataclass
class SharePermissions:
    """Detailed permissions for shared content."""
    can_view: bool = True
    can_download: bool = False
    can_share: bool = False
    can_comment: bool = False
    can_edit: bool = False
    can_delete: bool = False
    max_downloads: Optional[int] = None
    allowed_ips: Optional[List[str]] = None
    allowed_domains: Optional[List[str]] = None
    require_authentication: bool = False
    
    def __post_init__(self):
        if self.allowed_ips is None:
            self.allowed_ips = []
        if self.allowed_domains is None:
            self.allowed_domains = []

@dataclass
class ShareAnalytics:
    """Analytics data for shared content."""
    view_count: int = 0
    download_count: int = 0
    unique_visitors: int = 0
    last_accessed: Optional[datetime] = None
    access_history: List[Dict[str, Any]] = field(default_factory=list)
    referrer_stats: Dict[str, int] = field(default_factory=dict)
    geographic_stats: Dict[str, int] = field(default_factory=dict)
    device_stats: Dict[str, int] = field(default_factory=dict)

class ShareRequest(BaseModel):
    """Request to create a shared link."""
    share_type: ShareType
    item_id: str  # Document ID, conversation ID, etc.
    access_level: AccessLevel = AccessLevel.VIEW
    expires_in_hours: Optional[int] = 168  # 7 days default
    password: Optional[str] = None
    permissions: Optional[Dict[str, Any]] = None
    notification_email: Optional[str] = None
    custom_message: Optional[str] = None
    
    @field_validator('expires_in_hours')
    @classmethod
    def validate_expiration(cls, v):
        if v is not None and (v < 1 or v > 8760):  # Max 1 year
            raise ValueError("Expiration must be between 1 hour and 1 year")
        return v

class ShareLink(BaseModel):
    """Shared link model."""
    share_id: str
    share_token: str
    share_url: str
    share_type: ShareType
    item_id: str
    creator_id: Optional[str] = None
    access_level: AccessLevel
    status: ShareStatus = ShareStatus.ACTIVE
    created_at: datetime
    expires_at: Optional[datetime] = None
    last_accessed: Optional[datetime] = None
    permissions: Dict[str, Any] = Field(default_factory=dict)
    analytics: Dict[str, Any] = Field(default_factory=dict)
    password_hash: Optional[str] = None
    custom_message: Optional[str] = None
    
    model_config = ConfigDict()
    
    @field_serializer('created_at', 'expires_at', 'last_accessed', when_used='json')
    def serialize_datetime(self, dt: Optional[datetime]) -> Optional[str]:
        return dt.isoformat() if dt else None

class AccessAttempt(BaseModel):
    """Access attempt record."""
    share_id: str
    ip_address: str
    user_agent: str
    timestamp: datetime
    success: bool
    access_type: str  # view, download, etc.
    error_reason: Optional[str] = None
    referrer: Optional[str] = None
    geographic_info: Optional[Dict[str, str]] = None

class CollaborationInvite(BaseModel):
    """Collaboration invitation model."""
    invite_id: str
    share_id: str
    email: str
    access_level: AccessLevel
    invited_by: Optional[str] = None
    invited_at: datetime
    expires_at: Optional[datetime] = None
    accepted_at: Optional[datetime] = None
    status: str = "pending"  # pending, accepted, declined, expired
    personal_message: Optional[str] = None

class SharingService:
    """
    Comprehensive sharing service providing secure link management,
    access control, collaboration features, and detailed analytics.
    """
    
    def __init__(self, data_dir: str = "sharing_data", base_url: str = "http://localhost:8000"):
        """Initialize sharing service."""
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
        self.base_url = base_url.rstrip('/')
        
        # Storage files
        self.shares_file = self.data_dir / "shares.json"
        self.analytics_file = self.data_dir / "analytics.json"
        self.invites_file = self.data_dir / "invites.json"
        
        # In-memory storage for active shares
        self.active_shares: Dict[str, ShareLink] = {}
        self.share_analytics: Dict[str, ShareAnalytics] = {}
        self.collaboration_invites: Dict[str, CollaborationInvite] = {}
        
        # Access tracking
        self.access_attempts: List[AccessAttempt] = []
        self.blocked_ips: Set[str] = set()
        
        # Load existing data
        asyncio.create_task(self._load_data())
    
    async def _load_data(self):
        """Load existing sharing data from storage."""
        try:
            # Load shares
            if self.shares_file.exists():
                async with aiofiles.open(self.shares_file, 'r') as f:
                    content = await f.read()
                    shares_data = json.loads(content)
                    
                    for share_data in shares_data:
                        # Convert datetime strings back to datetime objects
                        share_data['created_at'] = datetime.fromisoformat(share_data['created_at'])
                        if share_data.get('expires_at'):
                            share_data['expires_at'] = datetime.fromisoformat(share_data['expires_at'])
                        if share_data.get('last_accessed'):
                            share_data['last_accessed'] = datetime.fromisoformat(share_data['last_accessed'])
                        
                        share_link = ShareLink(**share_data)
                        self.active_shares[share_link.share_id] = share_link
            
            # Load analytics
            if self.analytics_file.exists():
                async with aiofiles.open(self.analytics_file, 'r') as f:
                    content = await f.read()
                    analytics_data = json.loads(content)
                    
                    for share_id, data in analytics_data.items():
                        if data.get('last_accessed'):
                            data['last_accessed'] = datetime.fromisoformat(data['last_accessed'])
                        
                        # Convert access history datetime strings
                        for access in data.get('access_history', []):
                            if 'timestamp' in access:
                                access['timestamp'] = datetime.fromisoformat(access['timestamp'])
                        
                        self.share_analytics[share_id] = ShareAnalytics(**data)
            
            # Load collaboration invites
            if self.invites_file.exists():
                async with aiofiles.open(self.invites_file, 'r') as f:
                    content = await f.read()
                    invites_data = json.loads(content)
                    
                    for invite_data in invites_data:
                        invite_data['invited_at'] = datetime.fromisoformat(invite_data['invited_at'])
                        if invite_data.get('expires_at'):
                            invite_data['expires_at'] = datetime.fromisoformat(invite_data['expires_at'])
                        if invite_data.get('accepted_at'):
                            invite_data['accepted_at'] = datetime.fromisoformat(invite_data['accepted_at'])
                        
                        invite = CollaborationInvite(**invite_data)
                        self.collaboration_invites[invite.invite_id] = invite
            
            logger.info(f"Loaded {len(self.active_shares)} shares, {len(self.share_analytics)} analytics records")
            
        except Exception as e:
            logger.error(f"Failed to load sharing data: {str(e)}")
    
    async def _save_data(self):
        """Save sharing data to storage."""
        try:
            # Save shares
            shares_data = []
            for share in self.active_shares.values():
                share_dict = share.dict()
                shares_data.append(share_dict)
            
            async with aiofiles.open(self.shares_file, 'w') as f:
                await f.write(json.dumps(shares_data, default=str, indent=2))
            
            # Save analytics
            analytics_data = {}
            for share_id, analytics in self.share_analytics.items():
                analytics_data[share_id] = asdict(analytics)
            
            async with aiofiles.open(self.analytics_file, 'w') as f:
                await f.write(json.dumps(analytics_data, default=str, indent=2))
            
            # Save invites
            invites_data = []
            for invite in self.collaboration_invites.values():
                invites_data.append(invite.dict())
            
            async with aiofiles.open(self.invites_file, 'w') as f:
                await f.write(json.dumps(invites_data, default=str, indent=2))
            
        except Exception as e:
            logger.error(f"Failed to save sharing data: {str(e)}")
    
    async def create_share_link(
        self, 
        request: ShareRequest, 
        creator_id: Optional[str] = None
    ) -> ShareLink:
        """Create a new shared link."""
        try:
            # Generate unique share ID and token
            share_id = str(uuid.uuid4())
            share_token = secrets.token_urlsafe(32)
            
            # Create share URL
            share_url = f"{self.base_url}/share/{share_token}"
            
            # Calculate expiration
            expires_at = None
            if request.expires_in_hours:
                expires_at = datetime.now() + timedelta(hours=request.expires_in_hours)
            
            # Hash password if provided
            password_hash = None
            if request.password:
                password_hash = hashlib.sha256(request.password.encode()).hexdigest()
            
            # Parse permissions
            permissions = {}
            if request.permissions:
                permissions = request.permissions
            elif request.access_level == AccessLevel.VIEW:
                permissions = {"can_view": True}
            elif request.access_level == AccessLevel.DOWNLOAD:
                permissions = {"can_view": True, "can_download": True}
            elif request.access_level == AccessLevel.EDIT:
                permissions = {"can_view": True, "can_download": True, "can_edit": True}
            elif request.access_level == AccessLevel.ADMIN:
                permissions = {
                    "can_view": True, 
                    "can_download": True, 
                    "can_edit": True, 
                    "can_share": True,
                    "can_delete": True
                }
            
            # Create share link
            share_link = ShareLink(
                share_id=share_id,
                share_token=share_token,
                share_url=share_url,
                share_type=request.share_type,
                item_id=request.item_id,
                creator_id=creator_id,
                access_level=request.access_level,
                created_at=datetime.now(),
                expires_at=expires_at,
                permissions=permissions,
                password_hash=password_hash,
                custom_message=request.custom_message
            )
            
            # Store share link
            self.active_shares[share_id] = share_link
            
            # Initialize analytics
            self.share_analytics[share_id] = ShareAnalytics()
            
            # Save data
            await self._save_data()
            
            logger.info(f"Created share link for {request.share_type.value} {request.item_id}")
            return share_link
            
        except Exception as e:
            error_msg = f"Failed to create share link: {str(e)}"
            logger.error(error_msg)
            raise ApplicationError(
                message=error_msg,
                category=ErrorCategory.SYSTEM,
                severity=ErrorSeverity.ERROR,
                recovery_action=RecoveryAction.RETRY
            )
    
    async def get_share_link(self, share_token: str) -> Optional[ShareLink]:
        """Get share link by token."""
        for share in self.active_shares.values():
            if share.share_token == share_token:
                # Check if expired
                if share.expires_at and datetime.now() > share.expires_at:
                    share.status = ShareStatus.EXPIRED
                    await self._save_data()
                    return None
                
                # Check if revoked or suspended
                if share.status in [ShareStatus.REVOKED, ShareStatus.SUSPENDED]:
                    return None
                
                return share
        
        return None
    
    async def validate_access(
        self, 
        share_token: str, 
        password: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        referrer: Optional[str] = None
    ) -> Tuple[bool, Optional[ShareLink], Optional[str]]:
        """Validate access to shared content."""
        try:
            # Get share link
            share_link = await self.get_share_link(share_token)
            if not share_link:
                return False, None, "Share link not found or expired"
            
            # Check if IP is blocked
            if ip_address and ip_address in self.blocked_ips:
                return False, share_link, "Access denied from this IP address"
            
            # Check password if required
            if share_link.password_hash:
                if not password:
                    return False, share_link, "Password required"
                
                password_hash = hashlib.sha256(password.encode()).hexdigest()
                if password_hash != share_link.password_hash:
                    return False, share_link, "Invalid password"
            
            # Check IP restrictions
            permissions = SharePermissions(**share_link.permissions)
            if permissions.allowed_ips and ip_address:
                if ip_address not in permissions.allowed_ips:
                    return False, share_link, "Access denied from this IP address"
            
            # Check domain restrictions (based on referrer)
            if permissions.allowed_domains and referrer:
                referrer_domain = self._extract_domain(referrer)
                if referrer_domain not in permissions.allowed_domains:
                    return False, share_link, "Access denied from this domain"
            
            # Log successful access attempt
            access_attempt = AccessAttempt(
                share_id=share_link.share_id,
                ip_address=ip_address or "unknown",
                user_agent=user_agent or "unknown",
                timestamp=datetime.now(),
                success=True,
                access_type="validation",
                referrer=referrer
            )
            self.access_attempts.append(access_attempt)
            
            return True, share_link, None
            
        except Exception as e:
            error_msg = f"Access validation failed: {str(e)}"
            logger.error(error_msg)
            return False, None, error_msg
    
    async def record_access(
        self, 
        share_id: str, 
        access_type: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        referrer: Optional[str] = None
    ):
        """Record access to shared content for analytics."""
        try:
            share_link = self.active_shares.get(share_id)
            if not share_link:
                return
            
            # Update share link last accessed
            share_link.last_accessed = datetime.now()
            
            # Update analytics
            analytics = self.share_analytics.get(share_id)
            if not analytics:
                analytics = ShareAnalytics()
                self.share_analytics[share_id] = analytics
            
            # Update counters
            if access_type == "view":
                analytics.view_count += 1
            elif access_type == "download":
                analytics.download_count += 1
            
            analytics.last_accessed = datetime.now()
            
            # Track unique visitors (simplified by IP)
            existing_ips = {access.get('ip_address') for access in analytics.access_history}
            if ip_address not in existing_ips:
                analytics.unique_visitors += 1
            
            # Record access in history
            access_record = {
                "timestamp": datetime.now(),
                "access_type": access_type,
                "ip_address": ip_address,
                "user_agent": user_agent,
                "referrer": referrer
            }
            analytics.access_history.append(access_record)
            
            # Update referrer stats
            if referrer:
                domain = self._extract_domain(referrer)
                analytics.referrer_stats[domain] = analytics.referrer_stats.get(domain, 0) + 1
            
            # Update device stats (simplified)
            device_type = self._detect_device_type(user_agent)
            analytics.device_stats[device_type] = analytics.device_stats.get(device_type, 0) + 1
            
            # Limit access history to last 1000 entries
            if len(analytics.access_history) > 1000:
                analytics.access_history = analytics.access_history[-1000:]
            
            await self._save_data()
            
        except Exception as e:
            logger.error(f"Failed to record access: {str(e)}")
    
    async def revoke_share_link(self, share_id: str) -> bool:
        """Revoke a shared link."""
        try:
            share_link = self.active_shares.get(share_id)
            if not share_link:
                return False
            
            share_link.status = ShareStatus.REVOKED
            await self._save_data()
            
            logger.info(f"Revoked share link {share_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to revoke share link {share_id}: {str(e)}")
            return False
    
    async def extend_expiration(
        self, 
        share_id: str, 
        additional_hours: int
    ) -> bool:
        """Extend expiration of a shared link."""
        try:
            share_link = self.active_shares.get(share_id)
            if not share_link:
                return False
            
            if share_link.expires_at:
                share_link.expires_at += timedelta(hours=additional_hours)
            else:
                share_link.expires_at = datetime.now() + timedelta(hours=additional_hours)
            
            await self._save_data()
            
            logger.info(f"Extended expiration for share link {share_id} by {additional_hours} hours")
            return True
            
        except Exception as e:
            logger.error(f"Failed to extend expiration for share link {share_id}: {str(e)}")
            return False
    
    async def update_permissions(
        self, 
        share_id: str, 
        permissions: Dict[str, Any]
    ) -> bool:
        """Update permissions for a shared link."""
        try:
            share_link = self.active_shares.get(share_id)
            if not share_link:
                return False
            
            share_link.permissions.update(permissions)
            await self._save_data()
            
            logger.info(f"Updated permissions for share link {share_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update permissions for share link {share_id}: {str(e)}")
            return False
    
    async def create_collaboration_invite(
        self, 
        share_id: str,
        email: str,
        access_level: AccessLevel,
        invited_by: Optional[str] = None,
        expires_in_hours: int = 168,  # 7 days
        personal_message: Optional[str] = None
    ) -> CollaborationInvite:
        """Create a collaboration invitation."""
        try:
            invite_id = str(uuid.uuid4())
            expires_at = datetime.now() + timedelta(hours=expires_in_hours)
            
            invite = CollaborationInvite(
                invite_id=invite_id,
                share_id=share_id,
                email=email,
                access_level=access_level,
                invited_by=invited_by,
                invited_at=datetime.now(),
                expires_at=expires_at,
                personal_message=personal_message
            )
            
            self.collaboration_invites[invite_id] = invite
            await self._save_data()
            
            logger.info(f"Created collaboration invite for {email} on share {share_id}")
            return invite
            
        except Exception as e:
            error_msg = f"Failed to create collaboration invite: {str(e)}"
            logger.error(error_msg)
            raise ApplicationError(
                message=error_msg,
                category=ErrorCategory.SYSTEM,
                severity=ErrorSeverity.ERROR,
                recovery_action=RecoveryAction.RETRY
            )
    
    async def accept_collaboration_invite(
        self, 
        invite_id: str
    ) -> Tuple[bool, Optional[ShareLink]]:
        """Accept a collaboration invitation."""
        try:
            invite = self.collaboration_invites.get(invite_id)
            if not invite:
                return False, None
            
            # Check if expired
            if invite.expires_at and datetime.now() > invite.expires_at:
                invite.status = "expired"
                await self._save_data()
                return False, None
            
            # Check if already accepted
            if invite.status == "accepted":
                share_link = self.active_shares.get(invite.share_id)
                return True, share_link
            
            # Accept invitation
            invite.status = "accepted"
            invite.accepted_at = datetime.now()
            
            # Get share link
            share_link = self.active_shares.get(invite.share_id)
            
            await self._save_data()
            
            logger.info(f"Accepted collaboration invite {invite_id}")
            return True, share_link
            
        except Exception as e:
            logger.error(f"Failed to accept collaboration invite {invite_id}: {str(e)}")
            return False, None
    
    async def get_share_analytics(self, share_id: str) -> Optional[ShareAnalytics]:
        """Get analytics for a shared link."""
        return self.share_analytics.get(share_id)
    
    async def list_user_shares(
        self, 
        creator_id: str, 
        status: Optional[ShareStatus] = None
    ) -> List[ShareLink]:
        """List shares created by a user."""
        shares = []
        for share in self.active_shares.values():
            if share.creator_id == creator_id:
                if status is None or share.status == status:
                    shares.append(share)
        
        return sorted(shares, key=lambda x: x.created_at, reverse=True)
    
    async def cleanup_expired_shares(self):
        """Clean up expired shares and invitations."""
        current_time = datetime.now()
        expired_shares = []
        expired_invites = []
        
        # Find expired shares
        for share_id, share in self.active_shares.items():
            if share.expires_at and current_time > share.expires_at:
                share.status = ShareStatus.EXPIRED
                expired_shares.append(share_id)
        
        # Find expired invites
        for invite_id, invite in self.collaboration_invites.items():
            if invite.expires_at and current_time > invite.expires_at:
                invite.status = "expired"
                expired_invites.append(invite_id)
        
        if expired_shares or expired_invites:
            await self._save_data()
            logger.info(f"Marked {len(expired_shares)} shares and {len(expired_invites)} invites as expired")
    
    # Utility methods
    
    def _extract_domain(self, url: str) -> str:
        """Extract domain from URL."""
        try:
            from urllib.parse import urlparse
            parsed = urlparse(url)
            return parsed.netloc.lower()
        except:
            return "unknown"
    
    def _detect_device_type(self, user_agent: Optional[str]) -> str:
        """Detect device type from user agent."""
        if not user_agent:
            return "unknown"
        
        user_agent = user_agent.lower()
        
        if any(mobile in user_agent for mobile in ['mobile', 'android', 'iphone', 'ipad']):
            return "mobile"
        elif 'tablet' in user_agent:
            return "tablet"
        else:
            return "desktop"
    
    # Security methods
    
    async def block_ip(self, ip_address: str, reason: str = ""):
        """Block an IP address from accessing shares."""
        self.blocked_ips.add(ip_address)
        logger.warning(f"Blocked IP address {ip_address}: {reason}")
    
    async def unblock_ip(self, ip_address: str):
        """Unblock an IP address."""
        self.blocked_ips.discard(ip_address)
        logger.info(f"Unblocked IP address {ip_address}")
    
    async def get_security_report(self) -> Dict[str, Any]:
        """Generate security report."""
        current_time = datetime.now()
        recent_attempts = [
            attempt for attempt in self.access_attempts
            if (current_time - attempt.timestamp).days < 7
        ]
        
        failed_attempts = [attempt for attempt in recent_attempts if not attempt.success]
        
        # Analyze patterns
        ip_failures = {}
        for attempt in failed_attempts:
            ip_failures[attempt.ip_address] = ip_failures.get(attempt.ip_address, 0) + 1
        
        suspicious_ips = [ip for ip, count in ip_failures.items() if count > 10]
        
        return {
            "total_recent_attempts": len(recent_attempts),
            "failed_attempts": len(failed_attempts),
            "suspicious_ips": suspicious_ips,
            "blocked_ips": list(self.blocked_ips),
            "active_shares": len([s for s in self.active_shares.values() if s.status == ShareStatus.ACTIVE]),
            "report_generated": current_time.isoformat()
        }

# Global sharing service instance
_sharing_service = None

def get_sharing_service() -> SharingService:
    """Get global sharing service instance."""
    global _sharing_service
    if _sharing_service is None:
        _sharing_service = SharingService()
    return _sharing_service