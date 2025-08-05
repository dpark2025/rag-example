"""
Comprehensive error handling system for RAG application.
Provides graceful error handling, recovery options, and user-friendly messages.
"""

import logging
import traceback
from typing import Dict, Any, Optional, Callable
from datetime import datetime
from enum import Enum
import json

logger = logging.getLogger(__name__)


class ErrorSeverity(Enum):
    """Error severity levels for appropriate handling."""
    LOW = "low"          # Informational, doesn't block functionality
    MEDIUM = "medium"    # Partial functionality affected
    HIGH = "high"        # Major functionality affected
    CRITICAL = "critical" # System-wide failure


class ErrorCategory(Enum):
    """Error categories for grouping and handling."""
    NETWORK = "network"
    DATABASE = "database"
    LLM = "llm"
    FILE_PROCESSING = "file_processing"
    VALIDATION = "validation"
    AUTHENTICATION = "authentication"
    SYSTEM = "system"
    CIRCUIT_BREAKER = "circuit_breaker"
    RETRY_EXHAUSTED = "retry_exhausted"
    EMBEDDING = "embedding"
    UNKNOWN = "unknown"


class RecoveryAction(Enum):
    """Suggested recovery actions for users."""
    RETRY = "retry"
    REFRESH = "refresh"
    CHECK_CONNECTION = "check_connection"
    CHECK_FILE = "check_file"
    CONTACT_SUPPORT = "contact_support"
    RESTART_SERVICE = "restart_service"
    WAIT = "wait"
    NONE = "none"


class ApplicationError(Exception):
    """Base application error with enhanced context."""
    
    def __init__(
        self,
        message: str,
        category: ErrorCategory = ErrorCategory.UNKNOWN,
        severity: ErrorSeverity = ErrorSeverity.MEDIUM,
        recovery_action: RecoveryAction = RecoveryAction.NONE,
        user_message: Optional[str] = None,
        technical_details: Optional[Dict[str, Any]] = None,
        error_code: Optional[str] = None
    ):
        super().__init__(message)
        self.category = category
        self.severity = severity
        self.recovery_action = recovery_action
        self.user_message = user_message or self._generate_user_message(message, category)
        self.technical_details = technical_details or {}
        self.error_code = error_code or f"{category.value.upper()}_{severity.value.upper()}"
        self.timestamp = datetime.now()
        
    def _generate_user_message(self, message: str, category: ErrorCategory) -> str:
        """Generate user-friendly error message based on category."""
        user_messages = {
            ErrorCategory.NETWORK: "We're having trouble connecting to the service. Please check your connection and try again.",
            ErrorCategory.DATABASE: "We're experiencing issues accessing your documents. Please try again in a moment.",
            ErrorCategory.LLM: "The AI service is temporarily unavailable. Your documents are safe, please try again shortly.",
            ErrorCategory.FILE_PROCESSING: "There was an issue processing your file. Please check the file format and try again.",
            ErrorCategory.VALIDATION: "The provided information doesn't appear to be valid. Please check and try again.",
            ErrorCategory.AUTHENTICATION: "There was an authentication issue. Please check your credentials.",
            ErrorCategory.SYSTEM: "We're experiencing a system issue. Our team has been notified.",
            ErrorCategory.UNKNOWN: "An unexpected error occurred. Please try again or contact support if the issue persists."
        }
        return user_messages.get(category, message)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert error to dictionary for JSON serialization."""
        return {
            "error_code": self.error_code,
            "message": str(self),
            "user_message": self.user_message,
            "category": self.category.value,
            "severity": self.severity.value,
            "recovery_action": self.recovery_action.value,
            "timestamp": self.timestamp.isoformat(),
            "technical_details": self.technical_details
        }


class ErrorHandler:
    """Central error handling and recovery system."""
    
    def __init__(self):
        self.error_history: list = []
        self.max_history_size = 100
        self.error_callbacks: Dict[ErrorCategory, list] = {}
        self.recovery_strategies: Dict[ErrorCategory, Callable] = {}
        self._setup_default_strategies()
    
    def _setup_default_strategies(self):
        """Set up default recovery strategies for common errors."""
        self.recovery_strategies[ErrorCategory.NETWORK] = self._network_recovery
        self.recovery_strategies[ErrorCategory.LLM] = self._llm_recovery
        self.recovery_strategies[ErrorCategory.DATABASE] = self._database_recovery
        self.recovery_strategies[ErrorCategory.FILE_PROCESSING] = self._file_recovery
    
    def handle_error(self, error: Exception) -> ApplicationError:
        """
        Convert any exception to ApplicationError with appropriate context.
        
        Args:
            error: The exception to handle
            
        Returns:
            ApplicationError with user-friendly message and recovery options
        """
        # If already an ApplicationError, enrich it
        if isinstance(error, ApplicationError):
            app_error = error
        else:
            # Categorize the error
            category, severity = self._categorize_error(error)
            recovery_action = self._suggest_recovery(category, error)
            
            app_error = ApplicationError(
                message=str(error),
                category=category,
                severity=severity,
                recovery_action=recovery_action,
                technical_details={
                    "type": type(error).__name__,
                    "traceback": traceback.format_exc()
                }
            )
        
        # Log the error
        self._log_error(app_error)
        
        # Add to history
        self._add_to_history(app_error)
        
        # Execute callbacks
        self._execute_callbacks(app_error)
        
        # Attempt recovery if available
        if app_error.category in self.recovery_strategies:
            self.recovery_strategies[app_error.category](app_error)
        
        return app_error
    
    def _categorize_error(self, error: Exception) -> tuple[ErrorCategory, ErrorSeverity]:
        """Categorize error based on type and content."""
        error_type = type(error).__name__
        error_msg = str(error).lower()
        
        # Network errors
        if any(keyword in error_msg for keyword in ['connection', 'timeout', 'network', 'refused']):
            return ErrorCategory.NETWORK, ErrorSeverity.HIGH
        
        # Database errors
        if any(keyword in error_msg for keyword in ['database', 'chromadb', 'vector', 'collection']):
            return ErrorCategory.DATABASE, ErrorSeverity.HIGH
        
        # LLM errors
        if any(keyword in error_msg for keyword in ['ollama', 'llm', 'model', 'language model']):
            return ErrorCategory.LLM, ErrorSeverity.HIGH
        
        # File processing errors
        if any(keyword in error_msg for keyword in ['file', 'pdf', 'upload', 'processing']):
            return ErrorCategory.FILE_PROCESSING, ErrorSeverity.MEDIUM
        
        # Validation errors
        if any(keyword in error_msg for keyword in ['invalid', 'validation', 'format']):
            return ErrorCategory.VALIDATION, ErrorSeverity.LOW
        
        # Default
        return ErrorCategory.UNKNOWN, ErrorSeverity.MEDIUM
    
    def _suggest_recovery(self, category: ErrorCategory, error: Exception) -> RecoveryAction:
        """Suggest recovery action based on error category."""
        recovery_map = {
            ErrorCategory.NETWORK: RecoveryAction.CHECK_CONNECTION,
            ErrorCategory.DATABASE: RecoveryAction.WAIT,
            ErrorCategory.LLM: RecoveryAction.RETRY,
            ErrorCategory.FILE_PROCESSING: RecoveryAction.CHECK_FILE,
            ErrorCategory.VALIDATION: RecoveryAction.NONE,
            ErrorCategory.AUTHENTICATION: RecoveryAction.REFRESH,
            ErrorCategory.SYSTEM: RecoveryAction.CONTACT_SUPPORT,
            ErrorCategory.UNKNOWN: RecoveryAction.RETRY
        }
        return recovery_map.get(category, RecoveryAction.NONE)
    
    def _log_error(self, error: ApplicationError):
        """Log error with appropriate level."""
        log_levels = {
            ErrorSeverity.LOW: logger.info,
            ErrorSeverity.MEDIUM: logger.warning,
            ErrorSeverity.HIGH: logger.error,
            ErrorSeverity.CRITICAL: logger.critical
        }
        
        log_func = log_levels.get(error.severity, logger.error)
        log_func(
            f"[{error.error_code}] {error.message}",
            extra={
                "error_details": error.to_dict()
            }
        )
    
    def _add_to_history(self, error: ApplicationError):
        """Add error to history for pattern analysis."""
        self.error_history.append(error.to_dict())
        
        # Maintain size limit
        if len(self.error_history) > self.max_history_size:
            self.error_history.pop(0)
    
    def _execute_callbacks(self, error: ApplicationError):
        """Execute registered callbacks for error category."""
        callbacks = self.error_callbacks.get(error.category, [])
        for callback in callbacks:
            try:
                callback(error)
            except Exception as e:
                logger.error(f"Error in callback: {e}")
    
    def register_callback(self, category: ErrorCategory, callback: Callable):
        """Register a callback for specific error category."""
        if category not in self.error_callbacks:
            self.error_callbacks[category] = []
        self.error_callbacks[category].append(callback)
    
    def get_error_stats(self) -> Dict[str, Any]:
        """Get error statistics for monitoring."""
        if not self.error_history:
            return {"total": 0, "by_category": {}, "by_severity": {}}
        
        stats = {
            "total": len(self.error_history),
            "by_category": {},
            "by_severity": {},
            "recent_errors": self.error_history[-10:]  # Last 10 errors
        }
        
        for error in self.error_history:
            # Count by category
            category = error.get("category", "unknown")
            stats["by_category"][category] = stats["by_category"].get(category, 0) + 1
            
            # Count by severity
            severity = error.get("severity", "unknown")
            stats["by_severity"][severity] = stats["by_severity"].get(severity, 0) + 1
        
        return stats
    
    # Recovery strategies
    def _network_recovery(self, error: ApplicationError):
        """Attempt network error recovery."""
        logger.info(f"Attempting network recovery for: {error.error_code}")
        # In a real application, this might:
        # - Check connectivity
        # - Retry with exponential backoff
        # - Switch to offline mode
        # - Use cached data
    
    def _llm_recovery(self, error: ApplicationError):
        """Attempt LLM error recovery."""
        logger.info(f"Attempting LLM recovery for: {error.error_code}")
        # In a real application, this might:
        # - Check Ollama service status
        # - Attempt to restart Ollama
        # - Switch to a fallback model
        # - Use cached responses
    
    def _database_recovery(self, error: ApplicationError):
        """Attempt database error recovery."""
        logger.info(f"Attempting database recovery for: {error.error_code}")
        # In a real application, this might:
        # - Check ChromaDB status
        # - Attempt reconnection
        # - Clear corrupted data
        # - Rebuild indexes
    
    def _file_recovery(self, error: ApplicationError):
        """Attempt file processing error recovery."""
        logger.info(f"Attempting file recovery for: {error.error_code}")
        # In a real application, this might:
        # - Validate file format
        # - Try alternative parsers
        # - Extract partial content
        # - Suggest file conversion


# Global error handler instance
error_handler = ErrorHandler()


# Convenience functions
def handle_error(error: Exception) -> ApplicationError:
    """Global error handling function."""
    return error_handler.handle_error(error)


def get_error_stats() -> Dict[str, Any]:
    """Get global error statistics."""
    return error_handler.get_error_stats()