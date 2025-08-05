"""
Authored by: Harry Lewis (louie)
Date: 2025-01-08

Internationalization Manager for RAG System
Provides comprehensive i18n framework with language resource management
"""

import os
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, asdict
from datetime import datetime
from functools import lru_cache
import re

logger = logging.getLogger(__name__)

@dataclass
class LanguageConfig:
    """Configuration for a supported language."""
    code: str  # ISO 639-1 code (e.g., 'en', 'es')
    name: str  # Native name (e.g., 'English', 'Español')
    display_name: str  # Display name in English
    rtl: bool = False  # Right-to-left language
    plural_rules: str = "simple"  # Pluralization rules
    date_format: str = "%Y-%m-%d"
    time_format: str = "%H:%M:%S"
    number_format: Dict[str, str] = None
    enabled: bool = True
    fallback: str = "en"  # Fallback language
    
    def __post_init__(self):
        if self.number_format is None:
            self.number_format = {
                "decimal_separator": ".",
                "thousands_separator": ",",
                "currency_symbol": "$",
                "currency_position": "before"
            }

class I18nManager:
    """
    Comprehensive internationalization manager for the RAG system.
    
    Features:
    - Language resource loading and caching
    - Message formatting with variables
    - Pluralization support
    - Locale-specific formatting
    - Hot-reload for development
    - Fallback language support
    - Context-aware translations
    """
    
    def __init__(self, base_path: Optional[str] = None, default_language: str = "en"):
        self.base_path = Path(base_path) if base_path else Path(__file__).parent / "locales"
        self.default_language = default_language
        self.current_language = default_language
        self.languages: Dict[str, LanguageConfig] = {}
        self.messages: Dict[str, Dict[str, Any]] = {}
        self.formatters: Dict[str, Any] = {}
        
        # Initialize supported languages
        self._initialize_languages()
        
        # Load default language
        self.load_language(default_language)
        
        logger.info(f"I18n Manager initialized with default language: {default_language}")
    
    def _initialize_languages(self):
        """Initialize supported language configurations."""
        # Major languages with comprehensive configuration
        language_configs = [
            LanguageConfig("en", "English", "English", False, "simple", "%Y-%m-%d", "%H:%M:%S"),
            LanguageConfig("es", "Español", "Spanish", False, "romance", "%d/%m/%Y", "%H:%M"),
            LanguageConfig("fr", "Français", "French", False, "romance", "%d/%m/%Y", "%H:%M"),
            LanguageConfig("de", "Deutsch", "German", False, "germanic", "%d.%m.%Y", "%H:%M"),
            LanguageConfig("it", "Italiano", "Italian", False, "romance", "%d/%m/%Y", "%H:%M"),
            LanguageConfig("pt", "Português", "Portuguese", False, "romance", "%d/%m/%Y", "%H:%M"),
            LanguageConfig("ru", "Русский", "Russian", False, "slavic", "%d.%m.%Y", "%H:%M"),
            LanguageConfig("zh", "中文", "Chinese", False, "chinese", "%Y年%m月%d日", "%H:%M"),
            LanguageConfig("ja", "日本語", "Japanese", False, "japanese", "%Y年%m月%d日", "%H:%M"),
            LanguageConfig("ko", "한국어", "Korean", False, "korean", "%Y년 %m월 %d일", "%H:%M"),
            LanguageConfig("ar", "العربية", "Arabic", True, "arabic", "%d/%m/%Y", "%H:%M"),
            LanguageConfig("hi", "हिन्दी", "Hindi", False, "simple", "%d/%m/%Y", "%H:%M"),
            LanguageConfig("nl", "Nederlands", "Dutch", False, "germanic", "%d-%m-%Y", "%H:%M"),
            LanguageConfig("sv", "Svenska", "Swedish", False, "germanic", "%Y-%m-%d", "%H:%M"),
            LanguageConfig("da", "Dansk", "Danish", False, "germanic", "%d/%m/%Y", "%H:%M"),
            LanguageConfig("no", "Norsk", "Norwegian", False, "germanic", "%d.%m.%Y", "%H:%M"),
            LanguageConfig("fi", "Suomi", "Finnish", False, "finnic", "%d.%m.%Y", "%H:%M"),
            LanguageConfig("pl", "Polski", "Polish", False, "slavic", "%d.%m.%Y", "%H:%M"),
            LanguageConfig("tr", "Türkçe", "Turkish", False, "simple", "%d.%m.%Y", "%H:%M")
        ]
        
        for config in language_configs:
            self.languages[config.code] = config
    
    def get_supported_languages(self) -> List[LanguageConfig]:
        """Get list of all supported languages."""
        return [lang for lang in self.languages.values() if lang.enabled]
    
    def get_language_config(self, language_code: str) -> Optional[LanguageConfig]:
        """Get configuration for a specific language."""
        return self.languages.get(language_code)
    
    def is_language_supported(self, language_code: str) -> bool:
        """Check if a language is supported and enabled."""
        config = self.languages.get(language_code)
        return config is not None and config.enabled
    
    @lru_cache(maxsize=32)
    def load_language(self, language_code: str) -> bool:
        """
        Load language resources from files.
        Returns True if successful, False otherwise.
        """
        if not self.is_language_supported(language_code):
            logger.warning(f"Language {language_code} is not supported")
            return False
        
        language_dir = self.base_path / language_code
        if not language_dir.exists():
            logger.warning(f"Language directory not found: {language_dir}")
            return False
        
        messages = {}
        
        # Load all JSON files in the language directory
        for file_path in language_dir.glob("*.json"):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    file_messages = json.load(f)
                    namespace = file_path.stem
                    messages[namespace] = file_messages
                    logger.debug(f"Loaded {len(file_messages)} messages from {file_path}")
            except Exception as e:
                logger.error(f"Error loading language file {file_path}: {e}")
                continue
        
        if messages:
            self.messages[language_code] = messages
            logger.info(f"Successfully loaded {len(messages)} namespaces for language {language_code}")
            return True
        else:
            logger.error(f"No valid message files found for language {language_code}")
            return False
    
    def set_language(self, language_code: str) -> bool:
        """Set the current active language."""
        if self.is_language_supported(language_code):
            if language_code not in self.messages:
                if not self.load_language(language_code):
                    return False
            
            self.current_language = language_code
            logger.info(f"Language changed to: {language_code}")
            return True
        else:
            logger.warning(f"Cannot set unsupported language: {language_code}")
            return False
    
    def get_message(self, key: str, language: Optional[str] = None, 
                   namespace: str = "common", **kwargs) -> str:
        """
        Get a localized message with optional variable substitution.
        
        Args:
            key: Message key (e.g., 'welcome_message')
            language: Language code (uses current if None)
            namespace: Message namespace (default: 'common')
            **kwargs: Variables for message formatting
        
        Returns:
            Localized message string with variables substituted
        """
        lang = language or self.current_language
        
        # Try to get message in requested language
        message = self._get_message_from_lang(key, lang, namespace)
        
        # Fallback to default language if not found
        if message is None and lang != self.default_language:
            message = self._get_message_from_lang(key, self.default_language, namespace)
        
        # Final fallback to key itself
        if message is None:
            logger.warning(f"Message not found: {namespace}.{key} for language {lang}")
            message = f"[{namespace}.{key}]"
        
        # Substitute variables
        return self._format_message(message, **kwargs)
    
    def _get_message_from_lang(self, key: str, language: str, namespace: str) -> Optional[str]:
        """Get message from specific language and namespace."""
        if language not in self.messages:
            return None
        
        lang_messages = self.messages[language]
        if namespace not in lang_messages:
            return None
        
        namespace_messages = lang_messages[namespace]
        
        # Support nested keys with dot notation
        keys = key.split('.')
        current = namespace_messages
        
        for k in keys:
            if isinstance(current, dict) and k in current:
                current = current[k]
            else:
                return None
        
        return current if isinstance(current, str) else None
    
    def _format_message(self, message: str, **kwargs) -> str:
        """Format message with variable substitution."""
        if not kwargs:
            return message
        
        try:
            # Simple variable substitution: {variable_name}
            for key, value in kwargs.items():
                message = message.replace(f"{{{key}}}", str(value))
            
            return message
        except Exception as e:
            logger.error(f"Error formatting message: {e}")
            return message
    
    def get_plural_message(self, key: str, count: int, language: Optional[str] = None,
                          namespace: str = "common", **kwargs) -> str:
        """
        Get a pluralized message based on count.
        
        Supports different pluralization rules for different languages.
        Message keys should follow pattern: key_zero, key_one, key_other
        """
        lang = language or self.current_language
        config = self.languages.get(lang)
        
        if not config:
            return self.get_message(key, language, namespace, count=count, **kwargs)
        
        # Determine plural form based on language rules
        plural_form = self._get_plural_form(count, config.plural_rules)
        plural_key = f"{key}_{plural_form}"
        
        # Try to get pluralized message
        message = self._get_message_from_lang(plural_key, lang, namespace)
        
        if message is None:
            # Fallback to base key
            message = self.get_message(key, language, namespace, count=count, **kwargs)
        else:
            # Format with count and other variables
            message = self._format_message(message, count=count, **kwargs)
        
        return message
    
    def _get_plural_form(self, count: int, rules: str) -> str:
        """Determine plural form based on count and language rules."""
        if rules == "simple":
            return "one" if count == 1 else "other"
        elif rules == "romance":
            if count == 0:
                return "zero"
            elif count == 1:
                return "one"
            else:
                return "other"
        elif rules == "slavic":
            if count == 0:
                return "zero"
            elif count == 1:
                return "one"
            elif 2 <= count <= 4:
                return "few"
            else:
                return "other"
        elif rules == "arabic":
            if count == 0:
                return "zero"
            elif count == 1:
                return "one"
            elif count == 2:
                return "two"
            elif 3 <= count <= 10:
                return "few"
            else:
                return "other"
        else:
            return "one" if count == 1 else "other"
    
    def format_date(self, date: datetime, language: Optional[str] = None) -> str:
        """Format date according to language conventions."""
        lang = language or self.current_language
        config = self.languages.get(lang)
        
        if config:
            return date.strftime(config.date_format)
        else:
            return date.strftime("%Y-%m-%d")
    
    def format_time(self, time: datetime, language: Optional[str] = None) -> str:
        """Format time according to language conventions."""
        lang = language or self.current_language
        config = self.languages.get(lang)
        
        if config:
            return time.strftime(config.time_format)
        else:
            return time.strftime("%H:%M:%S")
    
    def format_number(self, number: Union[int, float], language: Optional[str] = None) -> str:
        """Format number according to language conventions."""
        lang = language or self.current_language
        config = self.languages.get(lang)
        
        if not config:
            return str(number)
        
        # Basic number formatting
        decimal_sep = config.number_format.get("decimal_separator", ".")
        thousands_sep = config.number_format.get("thousands_separator", ",")
        
        if isinstance(number, float):
            # Format float with 2 decimal places
            formatted = f"{number:,.2f}"
        else:
            # Format integer
            formatted = f"{number:,}"
        
        # Replace separators according to locale
        if decimal_sep != ".":
            formatted = formatted.replace(".", decimal_sep)
        if thousands_sep != ",":
            formatted = formatted.replace(",", thousands_sep)
        
        return formatted
    
    def format_currency(self, amount: Union[int, float], language: Optional[str] = None) -> str:
        """Format currency according to language conventions."""
        lang = language or self.current_language
        config = self.languages.get(lang)
        
        if not config:
            return f"${amount}"
        
        formatted_number = self.format_number(amount, language)
        currency_symbol = config.number_format.get("currency_symbol", "$")
        currency_position = config.number_format.get("currency_position", "before")
        
        if currency_position == "before":
            return f"{currency_symbol}{formatted_number}"
        else:
            return f"{formatted_number} {currency_symbol}"
    
    def create_language_pack(self, language_code: str, force: bool = False) -> Path:
        """
        Create directory structure and template files for a new language.
        """
        if not force and self.is_language_supported(language_code):
            raise ValueError(f"Language {language_code} already exists")
        
        language_dir = self.base_path / language_code
        language_dir.mkdir(parents=True, exist_ok=True)
        
        # Create common message templates
        templates = {
            "common.json": {
                "app_name": "RAG System",
                "welcome": "Welcome",
                "loading": "Loading...",
                "error": "Error",
                "success": "Success",
                "cancel": "Cancel",
                "save": "Save",
                "delete": "Delete",
                "edit": "Edit",
                "search": "Search",
                "upload": "Upload",
                "download": "Download"
            },
            "documents.json": {
                "document": "Document",
                "documents": "Documents",
                "upload_document": "Upload Document",
                "delete_document": "Delete Document",
                "document_uploaded": "Document uploaded successfully",
                "document_deleted": "Document deleted",
                "no_documents": "No documents found",
                "processing": "Processing document...",
                "processed": "Document processed",
                "failed": "Processing failed"
            },
            "chat.json": {
                "chat": "Chat",
                "message": "Message",
                "send_message": "Send Message",
                "thinking": "Thinking...",
                "no_response": "No response available",
                "conversation": "Conversation",
                "new_conversation": "New Conversation",
                "clear_conversation": "Clear Conversation"
            },
            "errors.json": {
                "network_error": "Network connection error",
                "server_error": "Server error occurred",
                "validation_error": "Validation error",
                "not_found": "Not found",
                "unauthorized": "Unauthorized access",
                "forbidden": "Access forbidden",
                "timeout": "Request timeout",
                "unknown_error": "Unknown error occurred"
            }
        }
        
        for filename, content in templates.items():
            file_path = language_dir / filename
            if not file_path.exists() or force:
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(content, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Language pack created for {language_code} at {language_dir}")
        return language_dir
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get internationalization statistics."""
        stats = {
            "supported_languages": len(self.languages),
            "loaded_languages": len(self.messages),
            "current_language": self.current_language,
            "default_language": self.default_language,
            "message_counts": {}
        }
        
        for lang_code, lang_messages in self.messages.items():
            total_messages = 0
            for namespace, messages in lang_messages.items():
                total_messages += len(messages) if isinstance(messages, dict) else 1
            stats["message_counts"][lang_code] = total_messages
        
        return stats

# Global instance
_i18n_manager = None

def get_i18n_manager() -> I18nManager:
    """Get the global i18n manager instance."""
    global _i18n_manager
    if _i18n_manager is None:
        _i18n_manager = I18nManager()
    return _i18n_manager

def _(key: str, **kwargs) -> str:
    """Shorthand function for getting localized messages."""
    return get_i18n_manager().get_message(key, **kwargs)

def _p(key: str, count: int, **kwargs) -> str:
    """Shorthand function for getting pluralized messages."""
    return get_i18n_manager().get_plural_message(key, count, **kwargs)

def set_language(language_code: str) -> bool:
    """Set the current language globally."""
    return get_i18n_manager().set_language(language_code)

def get_current_language() -> str:
    """Get the current language code."""
    return get_i18n_manager().current_language

if __name__ == "__main__":
    # Demo usage
    i18n = I18nManager()
    print("Supported languages:", [lang.code for lang in i18n.get_supported_languages()])
    print("Statistics:", i18n.get_statistics())