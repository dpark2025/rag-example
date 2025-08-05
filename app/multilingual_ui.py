"""
Authored by: Harry Lewis (louie)
Date: 2025-01-08

Multilingual UI Components and Helpers
Provides UI components and utilities for multilingual interfaces
"""

import logging
from typing import Dict, List, Optional, Any, Tuple, Union
from dataclasses import dataclass
from datetime import datetime
from functools import wraps
import json

# Import our multilingual components
from i18n_manager import get_i18n_manager, I18nManager
from language_detection import get_language_detector
from translation_service import get_translation_service, TranslationRequest

logger = logging.getLogger(__name__)

@dataclass
class UILanguageConfig:
    """Configuration for UI language settings."""
    code: str
    name: str
    display_name: str
    flag_emoji: str
    rtl: bool = False
    enabled: bool = True

class MultilingualUIHelper:
    """
    Helper class for multilingual UI components and utilities.
    
    Provides:
    - Language selection utilities
    - Localized formatting functions
    - UI text retrieval with fallbacks
    - Dynamic language switching
    - Cultural formatting adaptations
    """
    
    def __init__(self):
        self.i18n_manager = get_i18n_manager()
        self.translation_service = get_translation_service()
        self.current_ui_language = self.i18n_manager.current_language
        
        # UI-specific language configurations
        self.ui_languages = {
            "en": UILanguageConfig("en", "English", "English", "🇺🇸", False, True),
            "es": UILanguageConfig("es", "Español", "Spanish", "🇪🇸", False, True),
            "fr": UILanguageConfig("fr", "Français", "French", "🇫🇷", False, True),
            "de": UILanguageConfig("de", "Deutsch", "German", "🇩🇪", False, True),
            "it": UILanguageConfig("it", "Italiano", "Italian", "🇮🇹", False, True),
            "pt": UILanguageConfig("pt", "Português", "Portuguese", "🇵🇹", False, True),
            "ru": UILanguageConfig("ru", "Русский", "Russian", "🇷🇺", False, True),
            "zh": UILanguageConfig("zh", "中文", "Chinese", "🇨🇳", False, True),
            "ja": UILanguageConfig("ja", "日本語", "Japanese", "🇯🇵", False, True),
            "ko": UILanguageConfig("ko", "한국어", "Korean", "🇰🇷", False, True),
            "ar": UILanguageConfig("ar", "العربية", "Arabic", "🇸🇦", True, True),
            "hi": UILanguageConfig("hi", "हिन्दी", "Hindi", "🇮🇳", False, True),
            "nl": UILanguageConfig("nl", "Nederlands", "Dutch", "🇳🇱", False, True),
            "sv": UILanguageConfig("sv", "Svenska", "Swedish", "🇸🇪", False, True),
            "da": UILanguageConfig("da", "Dansk", "Danish", "🇩🇰", False, True),
            "no": UILanguageConfig("no", "Norsk", "Norwegian", "🇳🇴", False, True),
            "fi": UILanguageConfig("fi", "Suomi", "Finnish", "🇫🇮", False, True),
            "pl": UILanguageConfig("pl", "Polski", "Polish", "🇵🇱", False, True),
            "tr": UILanguageConfig("tr", "Türkçe", "Turkish", "🇹🇷", False, True)
        }
        
        logger.info("Multilingual UI helper initialized")
    
    def get_available_ui_languages(self) -> List[UILanguageConfig]:
        """Get list of available UI languages."""
        return [config for config in self.ui_languages.values() if config.enabled]
    
    def get_ui_language_config(self, language_code: str) -> Optional[UILanguageConfig]:
        """Get UI configuration for a specific language."""
        return self.ui_languages.get(language_code)
    
    def set_ui_language(self, language_code: str) -> bool:
        """Set the current UI language."""
        if language_code in self.ui_languages and self.ui_languages[language_code].enabled:
            success = self.i18n_manager.set_language(language_code)
            if success:
                self.current_ui_language = language_code
                logger.info(f"UI language changed to: {language_code}")
                return True
        return False
    
    def t(self, key: str, namespace: str = "common", **kwargs) -> str:
        """
        Get localized text for UI.
        Shorthand for translation with current UI language.
        """
        return self.i18n_manager.get_message(
            key, 
            language=self.current_ui_language, 
            namespace=namespace, 
            **kwargs
        )
    
    def tp(self, key: str, count: int, namespace: str = "common", **kwargs) -> str:
        """
        Get pluralized localized text for UI.
        """
        return self.i18n_manager.get_plural_message(
            key, 
            count, 
            language=self.current_ui_language, 
            namespace=namespace, 
            **kwargs
        )
    
    def format_date_for_ui(self, date: datetime) -> str:
        """Format date according to current UI language conventions."""
        return self.i18n_manager.format_date(date, self.current_ui_language)
    
    def format_time_for_ui(self, time: datetime) -> str:
        """Format time according to current UI language conventions."""
        return self.i18n_manager.format_time(time, self.current_ui_language)
    
    def format_number_for_ui(self, number: Union[int, float]) -> str:
        """Format number according to current UI language conventions."""
        return self.i18n_manager.format_number(number, self.current_ui_language)
    
    def format_currency_for_ui(self, amount: Union[int, float]) -> str:
        """Format currency according to current UI language conventions."""
        return self.i18n_manager.format_currency(amount, self.current_ui_language)
    
    def format_file_size(self, size_bytes: int) -> str:
        """Format file size with localized units."""
        if size_bytes < 1024:
            return f"{size_bytes} {self.t('bytes', 'common')}"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:.1f} {self.t('kb', 'common')}"
        elif size_bytes < 1024 * 1024 * 1024:
            return f"{size_bytes / (1024 * 1024):.1f} {self.t('mb', 'common')}"
        else:
            return f"{size_bytes / (1024 * 1024 * 1024):.1f} {self.t('gb', 'common')}"
    
    def get_language_display_name(self, language_code: str, in_language: Optional[str] = None) -> str:
        """Get display name for a language."""
        target_lang = in_language or self.current_ui_language
        config = self.ui_languages.get(language_code)
        
        if not config:
            return language_code.upper()
        
        # Return native name if displaying in the same language
        if target_lang == language_code:
            return config.name
        else:
            return config.display_name
    
    def is_rtl_language(self, language_code: Optional[str] = None) -> bool:
        """Check if a language is right-to-left."""
        lang = language_code or self.current_ui_language
        config = self.ui_languages.get(lang)
        return config.rtl if config else False
    
    def get_text_direction(self, language_code: Optional[str] = None) -> str:
        """Get CSS text direction for a language."""
        return "rtl" if self.is_rtl_language(language_code) else "ltr"
    
    def create_language_selector_data(self) -> List[Dict[str, Any]]:
        """Create data structure for language selector UI component."""
        languages = []
        
        for config in self.get_available_ui_languages():
            languages.append({
                "code": config.code,
                "name": config.name,
                "display_name": config.display_name,
                "flag": config.flag_emoji,
                "rtl": config.rtl,
                "current": config.code == self.current_ui_language
            })
        
        # Sort by display name
        languages.sort(key=lambda x: x["display_name"])
        return languages
    
    def get_localized_error_message(self, error_key: str, **kwargs) -> str:
        """Get localized error message."""
        return self.t(error_key, namespace="errors", **kwargs)
    
    def get_localized_success_message(self, message_key: str, **kwargs) -> str:
        """Get localized success message."""
        return self.t(message_key, namespace="common", **kwargs)
    
    def create_breadcrumb_data(self, breadcrumbs: List[Tuple[str, str]]) -> List[Dict[str, str]]:
        """Create localized breadcrumb data."""
        result = []
        for i, (key, url) in enumerate(breadcrumbs):
            result.append({
                "text": self.t(key, namespace="common"),
                "url": url,
                "active": i == len(breadcrumbs) - 1
            })
        return result
    
    def get_localized_status_text(self, status: str, namespace: str = "common") -> str:
        """Get localized status text with appropriate styling info."""
        status_lower = status.lower()
        return self.t(status_lower, namespace=namespace)
    
    def format_relative_time(self, datetime_obj: datetime) -> str:
        """Format relative time (e.g., '2 hours ago') in current language."""
        now = datetime.now()
        diff = now - datetime_obj
        
        if diff.days > 0:
            if diff.days == 1:
                return self.t("yesterday", namespace="common")
            elif diff.days < 7:
                return self.tp("days_ago", diff.days, namespace="common", count=diff.days)
            elif diff.days < 30:
                weeks = diff.days // 7
                return self.tp("weeks_ago", weeks, namespace="common", count=weeks)
            else:
                months = diff.days // 30
                return self.tp("months_ago", months, namespace="common", count=months)
        elif diff.seconds > 3600:
            hours = diff.seconds // 3600
            return self.tp("hours_ago", hours, namespace="common", count=hours)
        elif diff.seconds > 60:
            minutes = diff.seconds // 60
            return self.tp("minutes_ago", minutes, namespace="common", count=minutes)
        else:
            return self.t("just_now", namespace="common")
    
    def create_validation_messages(self, field_errors: Dict[str, List[str]]) -> Dict[str, List[str]]:
        """Create localized validation error messages."""
        localized_errors = {}
        
        for field, errors in field_errors.items():
            localized_errors[field] = []
            for error in errors:
                # Try to get localized version of error message
                localized_error = self.t(error, namespace="errors")
                localized_errors[field].append(localized_error)
        
        return localized_errors
    
    async def translate_ui_text(self, text: str, target_language: str) -> str:
        """Translate UI text to another language."""
        try:
            request = TranslationRequest(
                text=text,
                source_language=self.current_ui_language,
                target_language=target_language
            )
            result = await self.translation_service.translate(request)
            return result.translated_text
        except Exception as e:
            logger.error(f"UI text translation failed: {e}")
            return text
    
    def get_ui_statistics(self) -> Dict[str, Any]:
        """Get UI multilingual statistics."""
        return {
            "current_language": self.current_ui_language,
            "available_languages": len(self.get_available_ui_languages()),
            "rtl_support": any(config.rtl for config in self.ui_languages.values()),
            "supported_namespaces": ["common", "documents", "chat", "errors"],
            "i18n_statistics": self.i18n_manager.get_statistics()
        }

class MultilingualFormHelper:
    """Helper for multilingual form handling."""
    
    def __init__(self, ui_helper: MultilingualUIHelper):
        self.ui_helper = ui_helper
    
    def get_form_labels(self, form_type: str) -> Dict[str, str]:
        """Get localized form labels."""
        labels = {}
        
        if form_type == "document_upload":
            labels = {
                "file": self.ui_helper.t("file", "documents"),
                "title": self.ui_helper.t("title", "common"),
                "description": self.ui_helper.t("description", "common"),
                "language": self.ui_helper.t("language", "common"),
                "auto_detect": self.ui_helper.t("auto_detect", "documents")
            }
        elif form_type == "language_settings":
            labels = {
                "ui_language": self.ui_helper.t("ui_language", "common"),
                "preferred_language": self.ui_helper.t("prefer_language", "chat"),
                "auto_translate": self.ui_helper.t("auto_translate", "chat"),
                "cross_language_search": self.ui_helper.t("cross_language_search", "chat")
            }
        
        return labels
    
    def get_form_placeholders(self, form_type: str) -> Dict[str, str]:
        """Get localized form placeholders."""
        placeholders = {}
        
        if form_type == "chat":
            placeholders = {
                "message": self.ui_helper.t("type_message", "chat"),
                "search": self.ui_helper.t("search_documents", "documents")
            }
        
        return placeholders
    
    def get_validation_rules(self, form_type: str) -> Dict[str, Dict[str, Any]]:
        """Get localized validation rules and messages."""
        rules = {}
        
        if form_type == "document_upload":
            rules = {
                "file": {
                    "required": True,
                    "message": self.ui_helper.t("file_required", "errors")
                },
                "title": {
                    "required": False,
                    "max_length": 255,
                    "message": self.ui_helper.t("title_too_long", "errors")
                }
            }
        
        return rules

# Global instance
_multilingual_ui_helper = None

def get_multilingual_ui_helper() -> MultilingualUIHelper:
    """Get the global multilingual UI helper instance."""
    global _multilingual_ui_helper
    if _multilingual_ui_helper is None:
        _multilingual_ui_helper = MultilingualUIHelper()
    return _multilingual_ui_helper

# Decorator for automatic UI text localization
def localized_ui(func):
    """Decorator to automatically provide UI helper to functions."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        ui_helper = get_multilingual_ui_helper()
        return func(*args, ui_helper=ui_helper, **kwargs)
    return wrapper

# Utility functions for UI components
def t(key: str, namespace: str = "common", **kwargs) -> str:
    """Global shorthand for UI text translation."""
    return get_multilingual_ui_helper().t(key, namespace, **kwargs)

def tp(key: str, count: int, namespace: str = "common", **kwargs) -> str:
    """Global shorthand for UI text pluralization."""
    return get_multilingual_ui_helper().tp(key, count, namespace, **kwargs)

def format_ui_date(date: datetime) -> str:
    """Global shorthand for UI date formatting."""
    return get_multilingual_ui_helper().format_date_for_ui(date)

def format_ui_time(time: datetime) -> str:
    """Global shorthand for UI time formatting."""
    return get_multilingual_ui_helper().format_time_for_ui(time)

def format_ui_number(number: Union[int, float]) -> str:
    """Global shorthand for UI number formatting."""
    return get_multilingual_ui_helper().format_number_for_ui(number)

def get_text_direction() -> str:
    """Get CSS text direction for current UI language."""
    return get_multilingual_ui_helper().get_text_direction()

if __name__ == "__main__":
    # Demo usage
    ui_helper = MultilingualUIHelper()
    
    print("Available Languages:")
    for lang in ui_helper.create_language_selector_data():
        print(f"  {lang['flag']} {lang['display_name']} ({lang['code']})")
    
    print(f"\nCurrent Language: {ui_helper.current_ui_language}")
    print(f"Welcome Message: {ui_helper.t('welcome')}")
    print(f"Document Count: {ui_helper.tp('document_count', 5, 'documents', count=5)}")
    print(f"Text Direction: {ui_helper.get_text_direction()}")
    
    # Change language and test
    ui_helper.set_ui_language("es")
    print(f"\nAfter changing to Spanish:")
    print(f"Welcome Message: {ui_helper.t('welcome')}")
    print(f"Document Count: {ui_helper.tp('document_count', 5, 'documents', count=5)}")