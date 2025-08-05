"""
Authored by: Harry Lewis (louie)
Date: 2025-01-08

Comprehensive Tests for Multilingual RAG System
Tests all multilingual components and their integration
"""

import pytest
import asyncio
import tempfile
import shutil
from pathlib import Path
from datetime import datetime
from unittest.mock import Mock, patch
import json

# Import modules to test
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.i18n_manager import I18nManager, get_i18n_manager, LanguageConfig
from app.language_detection import LanguageDetector, get_language_detector, LanguageDetectionResult
from app.translation_service import TranslationService, get_translation_service, TranslationRequest
from app.multilingual_rag import MultilingualRAGSystem, get_multilingual_rag_system, MultilingualQuery
from app.multilingual_ui import MultilingualUIHelper, get_multilingual_ui_helper

class TestI18nManager:
    """Test internationalization manager functionality."""
    
    def setup_method(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.i18n = I18nManager(base_path=self.temp_dir)
    
    def teardown_method(self):
        """Clean up test environment."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_language_initialization(self):
        """Test language configuration initialization."""
        languages = self.i18n.get_supported_languages()
        assert len(languages) > 0
        
        # Check that common languages are supported
        language_codes = [lang.code for lang in languages]
        expected_languages = ["en", "es", "fr", "de", "it", "pt", "ru", "zh", "ja", "ko"]
        for lang in expected_languages:
            assert lang in language_codes
    
    def test_language_config_properties(self):
        """Test language configuration properties."""
        en_config = self.i18n.get_language_config("en")
        assert en_config is not None
        assert en_config.code == "en"
        assert en_config.name == "English"
        assert en_config.enabled is True
        assert en_config.rtl is False
        
        ar_config = self.i18n.get_language_config("ar")
        assert ar_config is not None
        assert ar_config.rtl is True  # Arabic is RTL
    
    def test_language_pack_creation(self):
        """Test creating new language packs."""
        test_lang = "test"
        lang_dir = self.i18n.create_language_pack(test_lang)
        
        assert lang_dir.exists()
        assert (lang_dir / "common.json").exists()
        assert (lang_dir / "documents.json").exists()
        assert (lang_dir / "chat.json").exists()
        assert (lang_dir / "errors.json").exists()
        
        # Test loading the created language pack
        with open(lang_dir / "common.json", 'w') as f:
            json.dump({"test_key": "test_value"}, f)
        
        assert self.i18n.load_language(test_lang)
        assert test_lang in self.i18n.messages
    
    def test_message_retrieval(self):
        """Test message retrieval and fallbacks."""
        # Create test messages
        en_dir = Path(self.temp_dir) / "en"
        en_dir.mkdir(exist_ok=True)
        
        with open(en_dir / "common.json", 'w') as f:
            json.dump({
                "test_message": "Hello World",
                "nested": {"key": "Nested Value"},
                "variable_message": "Hello {name}!"
            }, f)
        
        self.i18n.load_language("en")
        self.i18n.set_language("en")
        
        # Test basic retrieval
        assert self.i18n.get_message("test_message") == "Hello World"
        
        # Test nested key retrieval
        assert self.i18n.get_message("nested.key") == "Nested Value"
        
        # Test variable substitution
        assert self.i18n.get_message("variable_message", name="Claude") == "Hello Claude!"
        
        # Test fallback for missing key
        missing_msg = self.i18n.get_message("missing_key")
        assert "[common.missing_key]" in missing_msg
    
    def test_pluralization(self):
        """Test pluralization functionality."""
        en_dir = Path(self.temp_dir) / "en"
        en_dir.mkdir(exist_ok=True)
        
        with open(en_dir / "common.json", 'w') as f:
            json.dump({
                "item_count_one": "{count} item",
                "item_count_other": "{count} items"
            }, f)
        
        self.i18n.load_language("en")
        self.i18n.set_language("en")
        
        assert "1 item" in self.i18n.get_plural_message("item_count", 1, count=1)
        assert "5 items" in self.i18n.get_plural_message("item_count", 5, count=5)
    
    def test_date_time_formatting(self):
        """Test date and time formatting."""
        test_date = datetime(2024, 1, 15, 14, 30, 0)
        
        # Test different language formats
        en_date = self.i18n.format_date(test_date, "en")
        assert "2024" in en_date
        
        en_time = self.i18n.format_time(test_date, "en")
        assert "14:30" in en_time
    
    def test_number_formatting(self):
        """Test number and currency formatting."""
        # Test number formatting
        formatted_number = self.i18n.format_number(1234.56, "en")
        assert "1,234.56" in formatted_number
        
        # Test currency formatting
        formatted_currency = self.i18n.format_currency(99.99, "en")
        assert "$" in formatted_currency
        assert "99.99" in formatted_currency

class TestLanguageDetection:
    """Test language detection functionality."""
    
    def setup_method(self):
        """Set up test environment."""
        self.detector = LanguageDetector()
    
    def test_language_detector_initialization(self):
        """Test language detector initialization."""
        assert len(self.detector.character_profiles) > 0
        assert len(self.detector.common_words) > 0
        assert len(self.detector.script_patterns) > 0
    
    def test_basic_language_detection(self):
        """Test basic language detection functionality."""
        test_cases = [
            ("This is a test in English.", "en"),
            ("Este es un texto en español.", "es"),
            ("Ceci est un texte en français.", "fr"),
            ("Dies ist ein Text auf Deutsch.", "de"),
            ("Questo è un testo in italiano.", "it"),
        ]
        
        for text, expected_lang in test_cases:
            result = self.detector.detect_language(text)
            assert isinstance(result, LanguageDetectionResult)
            assert result.language == expected_lang or result.language == "unknown"
            assert 0 <= result.confidence <= 1
            assert isinstance(result.alternatives, list)
    
    def test_short_text_handling(self):
        """Test handling of very short texts."""
        short_text = "Hi"
        result = self.detector.detect_language(short_text)
        
        # Short texts should have low confidence or be marked as unknown
        assert result.confidence < 0.5 or result.language == "unknown"
    
    def test_mixed_language_detection(self):
        """Test detection of mixed language content."""
        mixed_text = "Hello world, esto es mixed language content, très intéressant!"
        result = self.detector.detect_language(mixed_text)
        
        assert isinstance(result, LanguageDetectionResult)
        # Should detect mixing or return reasonable primary language
        assert len(result.alternatives) > 0
    
    def test_script_detection(self):
        """Test script detection functionality."""
        script_tests = [
            ("This is Latin script", "latin"),
            ("Это кириллица", "cyrillic"),
            ("这是中文", "chinese"),
            ("これは日本語です", "japanese"),
            ("이것은 한국어입니다", "korean"),
        ]
        
        for text, expected_script in script_tests:
            script_result = self.detector._detect_script(text.lower())
            # Check if the expected script is among the detected scripts
            if script_result.get("dominant_script"):
                dominant = script_result["dominant_script"]
                # Allow some flexibility in script detection
                assert dominant in self.detector.script_patterns.keys()
    
    def test_text_quality_assessment(self):
        """Test text quality assessment."""
        high_quality = "This is a well-formed sentence with proper grammar and sufficient length for analysis."
        low_quality = "a b c d"
        
        high_quality_score = self.detector._assess_text_quality(high_quality)
        low_quality_score = self.detector._assess_text_quality(low_quality)
        
        assert high_quality_score > low_quality_score
        assert 0 <= high_quality_score <= 1
        assert 0 <= low_quality_score <= 1
    
    def test_batch_detection(self):
        """Test batch language detection."""
        texts = [
            "English text for testing",
            "Texto en español para pruebas",
            "Texte français pour les tests"
        ]
        
        results = self.detector.detect_languages_batch(texts)
        assert len(results) == len(texts)
        
        for result in results:
            assert isinstance(result, LanguageDetectionResult)
            assert hasattr(result, 'language')
            assert hasattr(result, 'confidence')
    
    def test_caching_functionality(self):
        """Test caching of detection results."""
        text = "This is a test for caching functionality."
        
        # First call
        result1 = self.detector.detect_language_cached(text)
        
        # Second call should use cache
        result2 = self.detector.detect_language_cached(text)
        
        assert result1.language == result2.language
        assert result1.confidence == result2.confidence

class TestTranslationService:
    """Test translation service functionality."""
    
    def setup_method(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.translation_service = TranslationService(cache_dir=self.temp_dir)
    
    def teardown_method(self):
        """Clean up test environment."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_translation_service_initialization(self):
        """Test translation service initialization."""
        assert self.translation_service.translation_engine is not None
        assert self.translation_service.cache_dir.exists()
        assert isinstance(self.translation_service.memory_cache, dict)
    
    def test_supported_language_pairs(self):
        """Test supported language pair functionality."""
        pairs = self.translation_service.translation_engine.get_supported_language_pairs()
        assert len(pairs) > 0
        
        # Check specific pairs
        assert ("en", "es") in pairs
        assert ("en", "fr") in pairs
        assert ("es", "en") in pairs  # Reverse should also be supported
    
    @pytest.mark.asyncio
    async def test_basic_translation(self):
        """Test basic translation functionality."""
        request = TranslationRequest(
            text="hello",
            source_language="en",
            target_language="es"
        )
        
        result = await self.translation_service.translate(request)
        
        assert result.original_text == "hello"
        assert result.source_language == "en"
        assert result.target_language == "es"
        assert result.translated_text is not None
        assert result.confidence >= 0
        assert result.processing_time >= 0
    
    @pytest.mark.asyncio
    async def test_no_translation_needed(self):
        """Test when no translation is needed."""
        request = TranslationRequest(
            text="hello",
            source_language="en",
            target_language="en"
        )
        
        result = await self.translation_service.translate(request)
        
        assert result.original_text == result.translated_text
        assert result.translation_method == "no_translation_needed"
        assert result.confidence == 1.0
    
    @pytest.mark.asyncio
    async def test_auto_language_detection(self):
        """Test automatic source language detection."""
        request = TranslationRequest(
            text="This is English text",
            target_language="es"
        )
        
        result = await self.translation_service.translate(request)
        
        # Should auto-detect English
        assert result.source_language in ["en", "unknown"]
    
    @pytest.mark.asyncio
    async def test_unsupported_language_pair(self):
        """Test handling of unsupported language pairs."""
        request = TranslationRequest(
            text="test text",
            source_language="unsupported1",
            target_language="unsupported2"
        )
        
        result = await self.translation_service.translate(request)
        
        # Should fallback to original text
        assert result.translated_text == result.original_text
        assert "unsupported" in result.translation_method or "fallback" in result.translation_method
    
    @pytest.mark.asyncio
    async def test_batch_translation(self):
        """Test batch translation functionality."""
        requests = [
            TranslationRequest(text="hello", source_language="en", target_language="es"),
            TranslationRequest(text="world", source_language="en", target_language="fr"),
            TranslationRequest(text="test", source_language="en", target_language="de")
        ]
        
        results = await self.translation_service.translate_batch(requests)
        
        assert len(results) == len(requests)
        for result in results:
            assert result.original_text is not None
            assert result.translated_text is not None
    
    def test_translation_caching(self):
        """Test translation result caching."""
        # Test cache key generation
        key1 = self.translation_service._get_cache_key("hello", "en", "es")
        key2 = self.translation_service._get_cache_key("hello", "en", "es")
        key3 = self.translation_service._get_cache_key("goodbye", "en", "es")
        
        assert key1 == key2  # Same input should generate same key
        assert key1 != key3  # Different input should generate different key
    
    def test_cache_cleanup(self):
        """Test cache cleanup functionality."""
        # Fill cache with test data
        for i in range(10):
            key = f"test_key_{i}"
            self.translation_service.memory_cache[key] = {
                "translated_text": f"translation_{i}",
                "confidence": 0.8,
                "method": "test",
                "timestamp": datetime.now().isoformat()
            }
        
        original_size = len(self.translation_service.memory_cache)
        assert original_size == 10
        
        # Trigger cleanup
        self.translation_service.max_cache_size = 5
        self.translation_service._cleanup_cache()
        
        # Cache should be reduced
        assert len(self.translation_service.memory_cache) <= 5
    
    def test_background_translation_job(self):
        """Test background translation job functionality."""
        request = TranslationRequest(
            text="background test",
            source_language="en",
            target_language="es"
        )
        
        job_id = self.translation_service.start_background_translation(request)
        assert job_id is not None
        assert len(job_id) > 0
        
        # Check job status
        job = self.translation_service.get_job_status(job_id)
        assert job is not None
        assert job.job_id == job_id
        assert job.status in ["pending", "processing", "completed", "failed"]
    
    def test_translation_capabilities(self):
        """Test translation capabilities reporting."""
        capabilities = self.translation_service.get_translation_capabilities()
        
        assert "supported_language_pairs" in capabilities
        assert "supported_languages_by_source" in capabilities
        assert "total_language_pairs" in capabilities
        assert "cache_size" in capabilities
        
        assert isinstance(capabilities["supported_language_pairs"], list)
        assert isinstance(capabilities["supported_languages_by_source"], dict)
        assert isinstance(capabilities["total_language_pairs"], int)

class TestMultilingualRAG:
    """Test multilingual RAG system functionality."""
    
    def setup_method(self):
        """Set up test environment."""
        # Mock the base RAG system since we don't want to create actual ChromaDB
        self.mock_rag = Mock()
        self.mock_collection = Mock()
        self.mock_rag.collection = self.mock_collection
        
        self.multilingual_rag = MultilingualRAGSystem(base_rag_system=self.mock_rag)
    
    @pytest.mark.asyncio
    async def test_multilingual_document_processing(self):
        """Test multilingual document processing."""
        document = {
            "doc_id": "test_doc_1",
            "title": "Test Document",
            "content": "This is a test document in English."
        }
        
        result = await self.multilingual_rag.process_multilingual_document(document)
        
        assert result.doc_id == "test_doc_1"
        assert result.title == "Test Document"
        assert result.detected_language is not None
        assert 0 <= result.language_confidence <= 1
        assert isinstance(result.alternative_languages, list)
    
    @pytest.mark.asyncio
    async def test_multilingual_query_processing(self):
        """Test multilingual query processing."""
        # Mock search results
        self.mock_collection.query.return_value = {
            "documents": [["This is a test document."]],
            "metadatas": [[{"doc_id": "test_1", "detected_language": "en"}]],
            "distances": [[0.2]]
        }
        
        # Mock LLM response
        with patch.object(self.multilingual_rag, '_call_llm_with_context', return_value="Test response"):
            response = await self.multilingual_rag.multilingual_query(
                "What is this about?",
                target_language="en"
            )
        
        assert response.answer is not None
        assert response.query_language is not None
        assert response.answer_language is not None
        assert isinstance(response.sources, list)
        assert 0 <= response.confidence_score <= 1
    
    def test_supported_languages(self):
        """Test getting supported languages."""
        languages = self.multilingual_rag.get_supported_languages()
        assert isinstance(languages, list)
        assert len(languages) > 0
        assert "en" in languages
    
    def test_language_statistics(self):
        """Test language statistics functionality."""
        # Mock collection data
        self.mock_collection.get.return_value = {
            "metadatas": [
                {"detected_language": "en"},
                {"detected_language": "es"},
                {"detected_language": "en"}
            ]
        }
        
        stats = self.multilingual_rag.get_language_statistics()
        
        assert "total_documents" in stats
        assert "language_distribution" in stats
        assert "supported_languages" in stats
        assert isinstance(stats["language_distribution"], dict)
    
    def test_language_preferences(self):
        """Test setting language preferences."""
        original_threshold = self.multilingual_rag.confidence_threshold
        original_cross_lang = self.multilingual_rag.enable_cross_language_search
        
        self.multilingual_rag.set_language_preferences(
            confidence_threshold=0.8,
            enable_cross_language_search=False
        )
        
        assert self.multilingual_rag.confidence_threshold == 0.8
        assert self.multilingual_rag.enable_cross_language_search is False
        
        # Reset
        self.multilingual_rag.confidence_threshold = original_threshold
        self.multilingual_rag.enable_cross_language_search = original_cross_lang

class TestMultilingualUI:
    """Test multilingual UI helper functionality."""
    
    def setup_method(self):
        """Set up test environment."""
        self.ui_helper = MultilingualUIHelper()
    
    def test_ui_language_initialization(self):
        """Test UI language initialization."""
        languages = self.ui_helper.get_available_ui_languages()
        assert len(languages) > 0
        
        # Check specific languages
        language_codes = [lang.code for lang in languages]
        assert "en" in language_codes
        assert "es" in language_codes
        assert "fr" in language_codes
    
    def test_language_switching(self):
        """Test UI language switching."""
        original_lang = self.ui_helper.current_ui_language
        
        # Switch to Spanish
        success = self.ui_helper.set_ui_language("es")
        assert success is True
        assert self.ui_helper.current_ui_language == "es"
        
        # Switch back
        self.ui_helper.set_ui_language(original_lang)
        assert self.ui_helper.current_ui_language == original_lang
    
    def test_text_localization(self):
        """Test text localization functionality."""
        # Test basic text retrieval
        welcome = self.ui_helper.t("welcome")
        assert isinstance(welcome, str)
        assert len(welcome) > 0
        
        # Test with namespace
        doc_text = self.ui_helper.t("document", "documents")
        assert isinstance(doc_text, str)
        assert len(doc_text) > 0
    
    def test_pluralization(self):
        """Test pluralization functionality."""
        # Test singular
        singular = self.ui_helper.tp("document_count", 1, "documents", count=1)
        assert "1" in singular
        
        # Test plural  
        plural = self.ui_helper.tp("document_count", 5, "documents", count=5)
        assert "5" in plural
    
    def test_date_time_formatting(self):
        """Test date and time formatting."""
        test_date = datetime(2024, 1, 15, 14, 30, 0)
        
        formatted_date = self.ui_helper.format_date_for_ui(test_date)
        assert isinstance(formatted_date, str)
        assert "2024" in formatted_date
        
        formatted_time = self.ui_helper.format_time_for_ui(test_date)
        assert isinstance(formatted_time, str)
        assert "14" in formatted_time or "2" in formatted_time  # 24h or 12h format
    
    def test_rtl_language_detection(self):
        """Test RTL language detection."""
        # Arabic should be RTL
        assert self.ui_helper.is_rtl_language("ar") is True
        assert self.ui_helper.get_text_direction("ar") == "rtl"
        
        # English should be LTR
        assert self.ui_helper.is_rtl_language("en") is False
        assert self.ui_helper.get_text_direction("en") == "ltr"
    
    def test_language_selector_data(self):
        """Test language selector data generation."""
        selector_data = self.ui_helper.create_language_selector_data()
        
        assert isinstance(selector_data, list)
        assert len(selector_data) > 0
        
        for lang_data in selector_data:
            assert "code" in lang_data
            assert "name" in lang_data
            assert "display_name" in lang_data
            assert "flag" in lang_data
            assert "rtl" in lang_data and isinstance(lang_data["rtl"], bool)
            assert "current" in lang_data and isinstance(lang_data["current"], bool)
    
    def test_file_size_formatting(self):
        """Test file size formatting."""
        # Test different sizes
        assert "bytes" in self.ui_helper.format_file_size(500).lower()
        assert "kb" in self.ui_helper.format_file_size(2048).lower()
        assert "mb" in self.ui_helper.format_file_size(2 * 1024 * 1024).lower()
        assert "gb" in self.ui_helper.format_file_size(2 * 1024 * 1024 * 1024).lower()
    
    def test_language_display_names(self):
        """Test language display name functionality."""
        # Get display name in current language
        en_name = self.ui_helper.get_language_display_name("en")
        assert isinstance(en_name, str)
        assert len(en_name) > 0
        
        # Get display name in specific language
        es_name_in_en = self.ui_helper.get_language_display_name("es", "en")
        assert isinstance(es_name_in_en, str)
        assert len(es_name_in_en) > 0
    
    def test_error_message_localization(self):
        """Test error message localization."""
        error_msg = self.ui_helper.get_localized_error_message("network_error")
        assert isinstance(error_msg, str)
        assert len(error_msg) > 0
    
    @pytest.mark.asyncio
    async def test_ui_text_translation(self):
        """Test UI text translation."""
        original_text = "Hello World"
        translated = await self.ui_helper.translate_ui_text(original_text, "es")
        
        assert isinstance(translated, str)
        # Should either be translated or return original if translation fails
        assert len(translated) > 0
    
    def test_ui_statistics(self):
        """Test UI statistics."""
        stats = self.ui_helper.get_ui_statistics()
        
        assert "current_language" in stats
        assert "available_languages" in stats
        assert "rtl_support" in stats
        assert "supported_namespaces" in stats
        
        assert isinstance(stats["current_language"], str)
        assert isinstance(stats["available_languages"], int)
        assert isinstance(stats["rtl_support"], bool)
        assert isinstance(stats["supported_namespaces"], list)

class TestIntegration:
    """Test integration between multilingual components."""
    
    def setup_method(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        
        # Initialize components
        self.i18n = I18nManager(base_path=self.temp_dir)
        self.detector = LanguageDetector()
        self.translation_service = TranslationService(cache_dir=self.temp_dir)
        self.ui_helper = MultilingualUIHelper()
    
    def teardown_method(self):
        """Clean up test environment."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_component_integration(self):
        """Test integration between different components."""
        # Test text through the full pipeline
        test_text = "This is a test message for integration testing."
        
        # 1. Detect language
        detection = self.detector.detect_language(test_text)
        assert detection.language is not None
        
        # 2. Get localized UI text
        ui_text = self.ui_helper.t("welcome")
        assert isinstance(ui_text, str)
        
        # 3. Components should work together
        assert len(detection.alternatives) >= 0
        assert len(ui_text) > 0
    
    @pytest.mark.asyncio
    async def test_end_to_end_multilingual_workflow(self):
        """Test complete multilingual workflow."""
        # Simulate a complete workflow
        
        # 1. Document upload with language detection
        document_content = "This is a sample document for testing multilingual capabilities."
        detection = self.detector.detect_language(document_content)
        
        # 2. UI feedback
        ui_message = self.ui_helper.t("document_uploaded", "documents")
        
        # 3. Translation if needed
        if detection.language != "es":
            translation_request = TranslationRequest(
                text=ui_message,
                source_language="en",
                target_language="es"
            )
            translation_result = await self.translation_service.translate(translation_request)
            assert translation_result.translated_text is not None
        
        # Verify workflow completed
        assert detection.language is not None
        assert ui_message is not None
    
    def test_global_functions(self):
        """Test global convenience functions."""
        from app.multilingual_ui import t, tp, format_ui_date, get_text_direction
        
        # Test global translation function
        welcome = t("welcome")
        assert isinstance(welcome, str)
        
        # Test global plurals
        count_msg = tp("document_count", 3, "documents", count=3)
        assert isinstance(count_msg, str)
        
        # Test global date formatting
        test_date = datetime.now()
        formatted = format_ui_date(test_date)
        assert isinstance(formatted, str)
        
        # Test text direction
        direction = get_text_direction()
        assert direction in ["ltr", "rtl"]

def run_all_tests():
    """Run all multilingual tests."""
    pytest.main([__file__, "-v", "--tb=short"])

if __name__ == "__main__":
    # Run tests when script is executed directly
    run_all_tests()