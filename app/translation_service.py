"""
Authored by: Harry Lewis (louie)
Date: 2025-01-08

Translation Service for RAG System
Provides offline translation capabilities while maintaining data privacy
"""

import logging
import os
import re
from typing import Dict, List, Optional, Any, Tuple, Union
from dataclasses import dataclass, asdict
from datetime import datetime
from functools import lru_cache
import hashlib
import json
from pathlib import Path
import asyncio
import threading
from concurrent.futures import ThreadPoolExecutor

# Import our components
from language_detection import get_language_detector, LanguageDetectionResult
from i18n_manager import get_i18n_manager

logger = logging.getLogger(__name__)

@dataclass
class TranslationRequest:
    """Request structure for translation operations."""
    text: str
    source_language: Optional[str] = None  # Auto-detect if None
    target_language: str = "en"
    context: Optional[str] = None  # Additional context for better translation
    preserve_formatting: bool = True
    translation_type: str = "general"  # general, technical, formal, casual
    priority: int = 1  # 1=low, 2=medium, 3=high
    cache_result: bool = True

@dataclass
class TranslationResult:
    """Result structure for translation operations."""
    original_text: str
    translated_text: str
    source_language: str
    target_language: str
    confidence: float
    translation_method: str
    processing_time: float
    cached: bool = False
    alternatives: List[str] = None
    warnings: List[str] = None

@dataclass
class TranslationJob:
    """Background translation job."""
    job_id: str
    request: TranslationRequest
    status: str  # pending, processing, completed, failed
    result: Optional[TranslationResult] = None
    error_message: Optional[str] = None
    created_at: datetime = None
    completed_at: Optional[datetime] = None
    progress: float = 0.0

class LocalTranslationEngine:
    """
    Local translation engine using lightweight offline methods.
    
    This implementation focuses on maintaining privacy while providing
    basic translation capabilities using dictionary-based and rule-based methods.
    For production use, consider integrating with offline models like
    Helsinki-NLP MarianMT models or similar.
    """
    
    def __init__(self):
        self.translation_cache = {}
        self.dictionaries = {}
        self.translation_rules = {}
        self.supported_pairs = set()
        self._initialize_translation_data()
        
        logger.info("Local translation engine initialized")
    
    def _initialize_translation_data(self):
        """Initialize translation dictionaries and rules."""
        # Basic translation dictionaries for common words/phrases
        # In production, load from comprehensive translation files
        self.dictionaries = {
            ("en", "es"): {
                "hello": "hola", "goodbye": "adiós", "thank you": "gracias",
                "yes": "sí", "no": "no", "please": "por favor",
                "document": "documento", "search": "buscar", "upload": "subir",
                "download": "descargar", "delete": "eliminar", "save": "guardar",
                "error": "error", "success": "éxito", "loading": "cargando",
                "artificial intelligence": "inteligencia artificial",
                "machine learning": "aprendizaje automático",
                "data science": "ciencia de datos"
            },
            ("en", "fr"): {
                "hello": "bonjour", "goodbye": "au revoir", "thank you": "merci",
                "yes": "oui", "no": "non", "please": "s'il vous plaît",
                "document": "document", "search": "rechercher", "upload": "télécharger",
                "download": "télécharger", "delete": "supprimer", "save": "sauvegarder",
                "error": "erreur", "success": "succès", "loading": "chargement",
                "artificial intelligence": "intelligence artificielle",
                "machine learning": "apprentissage automatique",
                "data science": "science des données"
            },
            ("en", "de"): {
                "hello": "hallo", "goodbye": "auf wiedersehen", "thank you": "danke",
                "yes": "ja", "no": "nein", "please": "bitte",
                "document": "dokument", "search": "suchen", "upload": "hochladen",
                "download": "herunterladen", "delete": "löschen", "save": "speichern",
                "error": "fehler", "success": "erfolg", "loading": "laden",
                "artificial intelligence": "künstliche intelligenz",
                "machine learning": "maschinelles lernen",
                "data science": "datenwissenschaft"
            },
            ("en", "it"): {
                "hello": "ciao", "goodbye": "arrivederci", "thank you": "grazie",
                "yes": "sì", "no": "no", "please": "per favore",
                "document": "documento", "search": "cerca", "upload": "carica",
                "download": "scarica", "delete": "elimina", "save": "salva",
                "error": "errore", "success": "successo", "loading": "caricamento",
                "artificial intelligence": "intelligenza artificiale",
                "machine learning": "apprendimento automatico",
                "data science": "scienza dei dati"
            },
            ("en", "pt"): {
                "hello": "olá", "goodbye": "tchau", "thank you": "obrigado",
                "yes": "sim", "no": "não", "please": "por favor",
                "document": "documento", "search": "buscar", "upload": "carregar",
                "download": "baixar", "delete": "excluir", "save": "salvar",
                "error": "erro", "success": "sucesso", "loading": "carregando",
                "artificial intelligence": "inteligência artificial",
                "machine learning": "aprendizado de máquina",
                "data science": "ciência de dados"
            }
        }
        
        # Add reverse dictionaries
        reverse_dicts = {}
        for (src, tgt), dictionary in self.dictionaries.items():
            reverse_key = (tgt, src)
            reverse_dicts[reverse_key] = {v: k for k, v in dictionary.items()}
        
        self.dictionaries.update(reverse_dicts)
        
        # Track supported language pairs
        self.supported_pairs = set(self.dictionaries.keys())
        
        # Basic translation rules for common patterns
        self.translation_rules = {
            ("en", "es"): [
                (r"\b(\w+)ing\b", r"\1ando"),  # -ing to -ando (simplified)
                (r"\b(\w+)ed\b", r"\1ado"),    # -ed to -ado (simplified)
            ],
            ("en", "fr"): [
                (r"\b(\w+)ing\b", r"\1ant"),   # -ing to -ant (simplified)
                (r"\b(\w+)ed\b", r"\1é"),      # -ed to -é (simplified)
            ]
        }
    
    def is_translation_supported(self, source_lang: str, target_lang: str) -> bool:
        """Check if translation between two languages is supported."""
        return (source_lang, target_lang) in self.supported_pairs
    
    def get_supported_language_pairs(self) -> List[Tuple[str, str]]:
        """Get list of supported translation language pairs."""
        return list(self.supported_pairs)
    
    def translate_text(self, text: str, source_lang: str, target_lang: str,
                      context: Optional[str] = None) -> str:
        """
        Translate text using local dictionary and rules.
        
        Note: This is a basic implementation. For production use,
        integrate with proper offline translation models.
        """
        if source_lang == target_lang:
            return text
        
        if not self.is_translation_supported(source_lang, target_lang):
            logger.warning(f"Translation not supported: {source_lang} -> {target_lang}")
            return text
        
        # Get dictionary for this language pair
        dictionary = self.dictionaries.get((source_lang, target_lang), {})
        
        # Simple word-by-word translation with phrase matching
        translated_text = text.lower()
        
        # First, try to match longer phrases
        phrases = sorted(dictionary.keys(), key=len, reverse=True)
        for phrase in phrases:
            if phrase in translated_text:
                translated_text = translated_text.replace(phrase, dictionary[phrase])
        
        # Apply translation rules if available
        rules = self.translation_rules.get((source_lang, target_lang), [])
        for pattern, replacement in rules:
            translated_text = re.sub(pattern, replacement, translated_text)
        
        # Preserve original capitalization patterns
        result = self._preserve_capitalization(text, translated_text)
        
        return result
    
    def _preserve_capitalization(self, original: str, translated: str) -> str:
        """Preserve capitalization patterns from original text."""
        if not original or not translated:
            return translated
        
        # Simple capitalization preservation
        if original[0].isupper():
            translated = translated[0].upper() + translated[1:] if len(translated) > 1 else translated.upper()
        
        if original.isupper():
            translated = translated.upper()
        elif original.islower():
            translated = translated.lower()
        
        return translated

class TranslationService:
    """
    Comprehensive translation service with caching and offline capabilities.
    
    Features:
    - Offline translation (privacy-preserving)
    - Translation caching for performance
    - Batch translation support
    - Background translation jobs
    - Translation quality assessment
    - Context-aware translation
    """
    
    def __init__(self, cache_dir: Optional[str] = None):
        self.cache_dir = Path(cache_dir) if cache_dir else Path(__file__).parent / "translation_cache"
        self.cache_dir.mkdir(exist_ok=True)
        
        self.language_detector = get_language_detector()
        self.i18n_manager = get_i18n_manager()
        self.translation_engine = LocalTranslationEngine()
        
        # Translation cache
        self.memory_cache = {}
        self.cache_file = self.cache_dir / "translation_cache.json"
        self._load_cache()
        
        # Background job management
        self.background_jobs = {}
        self.job_executor = ThreadPoolExecutor(max_workers=2)
        
        # Configuration
        self.max_cache_size = 10000
        self.cache_expiry_days = 30
        self.default_confidence_threshold = 0.7
        
        logger.info("Translation service initialized")
    
    def _load_cache(self):
        """Load translation cache from disk."""
        try:
            if self.cache_file.exists():
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    cache_data = json.load(f)
                    self.memory_cache = cache_data.get("translations", {})
                logger.info(f"Loaded {len(self.memory_cache)} cached translations")
        except Exception as e:
            logger.error(f"Error loading translation cache: {e}")
            self.memory_cache = {}
    
    def _save_cache(self):
        """Save translation cache to disk."""
        try:
            cache_data = {
                "translations": self.memory_cache,
                "last_updated": datetime.now().isoformat()
            }
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Error saving translation cache: {e}")
    
    def _get_cache_key(self, text: str, source_lang: str, target_lang: str) -> str:
        """Generate cache key for translation."""
        content = f"{text}|{source_lang}|{target_lang}"
        return hashlib.md5(content.encode('utf-8')).hexdigest()
    
    async def translate(self, request: TranslationRequest) -> TranslationResult:
        """
        Translate text with comprehensive language processing.
        
        Args:
            request: TranslationRequest with text and parameters
            
        Returns:
            TranslationResult with translation and metadata
        """
        start_time = datetime.now()
        
        # Auto-detect source language if not provided
        if not request.source_language:
            detection = self.language_detector.detect_language(request.text)
            source_lang = detection.language
            detection_confidence = detection.confidence
        else:
            source_lang = request.source_language
            detection_confidence = 1.0
        
        # Check if translation is needed
        if source_lang == request.target_language:
            processing_time = (datetime.now() - start_time).total_seconds()
            return TranslationResult(
                original_text=request.text,
                translated_text=request.text,
                source_language=source_lang,
                target_language=request.target_language,
                confidence=1.0,
                translation_method="no_translation_needed",
                processing_time=processing_time,
                cached=False
            )
        
        # Check cache first
        cache_key = self._get_cache_key(request.text, source_lang, request.target_language)
        if request.cache_result and cache_key in self.memory_cache:
            cached_result = self.memory_cache[cache_key]
            processing_time = (datetime.now() - start_time).total_seconds()
            
            return TranslationResult(
                original_text=request.text,
                translated_text=cached_result["translated_text"],
                source_language=source_lang,
                target_language=request.target_language,
                confidence=cached_result["confidence"],
                translation_method=cached_result["method"],
                processing_time=processing_time,
                cached=True
            )
        
        # Perform translation
        try:
            if self.translation_engine.is_translation_supported(source_lang, request.target_language):
                translated_text = self.translation_engine.translate_text(
                    request.text, source_lang, request.target_language, request.context
                )
                translation_method = "local_dictionary"
                confidence = detection_confidence * 0.8  # Adjust for translation quality
            else:
                # Fallback: return original with warning
                translated_text = request.text
                translation_method = "unsupported_fallback"
                confidence = 0.0
                logger.warning(f"Translation not supported: {source_lang} -> {request.target_language}")
        
        except Exception as e:
            logger.error(f"Translation error: {e}")
            translated_text = request.text
            translation_method = "error_fallback"
            confidence = 0.0
        
        processing_time = (datetime.now() - start_time).total_seconds()
        
        # Create result
        result = TranslationResult(
            original_text=request.text,
            translated_text=translated_text,
            source_language=source_lang,
            target_language=request.target_language,
            confidence=confidence,
            translation_method=translation_method,
            processing_time=processing_time,
            cached=False
        )
        
        # Cache the result
        if request.cache_result and confidence > 0.5:
            self.memory_cache[cache_key] = {
                "translated_text": translated_text,
                "confidence": confidence,
                "method": translation_method,
                "timestamp": datetime.now().isoformat()
            }
            
            # Manage cache size
            if len(self.memory_cache) > self.max_cache_size:
                self._cleanup_cache()
        
        return result
    
    async def translate_batch(self, requests: List[TranslationRequest]) -> List[TranslationResult]:
        """Translate multiple texts efficiently."""
        results = []
        
        # Group requests by language pair for efficiency
        language_groups = {}
        for i, request in enumerate(requests):
            # Auto-detect source language if needed
            source_lang = request.source_language
            if not source_lang:
                detection = self.language_detector.detect_language(request.text)
                source_lang = detection.language
                request.source_language = source_lang
            
            key = (source_lang, request.target_language)
            if key not in language_groups:
                language_groups[key] = []
            language_groups[key].append((i, request))
        
        # Process each language group
        result_array = [None] * len(requests)
        
        for (src_lang, tgt_lang), group in language_groups.items():
            for index, request in group:
                result = await self.translate(request)
                result_array[index] = result
        
        return result_array
    
    def start_background_translation(self, request: TranslationRequest) -> str:
        """Start a background translation job."""
        job_id = hashlib.md5(f"{request.text}_{datetime.now().isoformat()}".encode()).hexdigest()[:12]
        
        job = TranslationJob(
            job_id=job_id,
            request=request,
            status="pending",
            created_at=datetime.now()
        )
        
        self.background_jobs[job_id] = job
        
        # Submit to thread pool
        future = self.job_executor.submit(self._process_background_job, job_id)
        
        logger.info(f"Started background translation job: {job_id}")
        return job_id
    
    def _process_background_job(self, job_id: str):
        """Process a background translation job."""
        job = self.background_jobs.get(job_id)
        if not job:
            return
        
        try:
            job.status = "processing"
            job.progress = 0.5
            
            # Run translation in sync context
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(self.translate(job.request))
            loop.close()
            
            job.result = result
            job.status = "completed"
            job.progress = 1.0
            job.completed_at = datetime.now()
            
        except Exception as e:
            job.status = "failed"
            job.error_message = str(e)
            job.completed_at = datetime.now()
            logger.error(f"Background translation job {job_id} failed: {e}")
    
    def get_job_status(self, job_id: str) -> Optional[TranslationJob]:
        """Get status of a background translation job."""
        return self.background_jobs.get(job_id)
    
    def get_translation_capabilities(self) -> Dict[str, Any]:
        """Get information about translation capabilities."""
        supported_pairs = self.translation_engine.get_supported_language_pairs()
        
        # Group by source language
        capabilities = {}
        for src, tgt in supported_pairs:
            if src not in capabilities:
                capabilities[src] = []
            capabilities[src].append(tgt)
        
        return {
            "supported_language_pairs": supported_pairs,
            "supported_languages_by_source": capabilities,
            "total_language_pairs": len(supported_pairs),
            "cache_size": len(self.memory_cache),
            "background_jobs_active": len([j for j in self.background_jobs.values() if j.status in ["pending", "processing"]]),
            "translation_methods": ["local_dictionary", "rule_based"]
        }
    
    def _cleanup_cache(self):
        """Clean up old cache entries."""
        try:
            # Remove oldest entries to maintain cache size
            sorted_entries = sorted(
                self.memory_cache.items(),
                key=lambda x: x[1].get("timestamp", "1970-01-01")
            )
            
            # Keep only the most recent entries
            entries_to_keep = sorted_entries[-int(self.max_cache_size * 0.8):]
            self.memory_cache = dict(entries_to_keep)
            
            # Save updated cache
            self._save_cache()
            
            logger.info(f"Cleaned cache, now contains {len(self.memory_cache)} entries")
            
        except Exception as e:
            logger.error(f"Error cleaning cache: {e}")
    
    def clear_cache(self):
        """Clear all cached translations."""
        self.memory_cache.clear()
        try:
            if self.cache_file.exists():
                self.cache_file.unlink()
        except Exception as e:
            logger.error(f"Error clearing cache file: {e}")
        
        logger.info("Translation cache cleared")
    
    def get_cache_statistics(self) -> Dict[str, Any]:
        """Get cache usage statistics."""
        return {
            "cache_size": len(self.memory_cache),
            "max_cache_size": self.max_cache_size,
            "cache_hit_rate": "unknown",  # Would need to track hits vs misses
            "cache_file_exists": self.cache_file.exists(),
            "cache_file_size": self.cache_file.stat().st_size if self.cache_file.exists() else 0
        }
    
    def __del__(self):
        """Cleanup when service is destroyed."""
        try:
            self._save_cache()
            self.job_executor.shutdown(wait=False)
        except:
            pass

# Global instance
_translation_service = None

def get_translation_service() -> TranslationService:
    """Get the global translation service instance."""
    global _translation_service
    if _translation_service is None:
        _translation_service = TranslationService()
    return _translation_service

async def translate_text(text: str, target_language: str, 
                        source_language: Optional[str] = None,
                        context: Optional[str] = None) -> TranslationResult:
    """Shorthand function for text translation."""
    service = get_translation_service()
    request = TranslationRequest(
        text=text,
        source_language=source_language,
        target_language=target_language,
        context=context
    )
    return await service.translate(request)

if __name__ == "__main__":
    # Demo usage
    import asyncio
    
    async def demo():
        service = TranslationService()
        
        # Test translations
        test_cases = [
            ("Hello, how are you?", "es"),
            ("Thank you for the document", "fr"),
            ("Artificial intelligence is amazing", "de"),
            ("Please upload the file", "it"),
            ("Good morning", "pt")
        ]
        
        for text, target_lang in test_cases:
            request = TranslationRequest(text=text, target_language=target_lang)
            result = await service.translate(request)
            
            print(f"Original ({result.source_language}): {result.original_text}")
            print(f"Translated ({result.target_language}): {result.translated_text}")
            print(f"Confidence: {result.confidence:.3f}, Method: {result.translation_method}")
            print("---")
        
        # Show capabilities
        print("\nTranslation Capabilities:")
        capabilities = service.get_translation_capabilities()
        for src_lang, target_langs in capabilities["supported_languages_by_source"].items():
            print(f"{src_lang} -> {', '.join(target_langs)}")
    
    asyncio.run(demo())