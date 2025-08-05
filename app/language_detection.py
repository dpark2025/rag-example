"""
Authored by: Harry Lewis (louie)
Date: 2025-01-08

Language Detection Service for RAG System
Provides automatic language identification for documents and queries
"""

import logging
import re
from typing import Dict, List, Optional, Tuple, Union
from dataclasses import dataclass
from collections import Counter
import unicodedata
import string
from functools import lru_cache

logger = logging.getLogger(__name__)

@dataclass
class LanguageDetectionResult:
    """Result of language detection analysis."""
    language: str  # Primary detected language code
    confidence: float  # Confidence score (0.0 to 1.0)
    alternatives: List[Tuple[str, float]]  # Alternative languages with scores
    script: Optional[str] = None  # Script type (latin, cyrillic, arabic, etc.)
    mixed_languages: bool = False  # Whether multiple languages detected
    text_quality: float = 1.0  # Text quality score for detection reliability

@dataclass 
class LanguageStats:
    """Statistics for a specific language in text analysis."""
    language: str
    word_count: int
    character_count: int
    unique_words: int
    common_words_matched: int
    script_confidence: float
    pattern_matches: int

class LanguageDetector:
    """
    Advanced language detection system with multiple detection methods.
    
    Features:
    - Character n-gram analysis
    - Common word detection
    - Script identification
    - Pattern-based detection
    - Confidence scoring
    - Mixed language detection
    - Text quality assessment
    """
    
    def __init__(self):
        self.character_profiles = self._build_character_profiles()
        self.common_words = self._build_common_words()
        self.script_patterns = self._build_script_patterns()
        self.language_patterns = self._build_language_patterns()
        self.min_text_length = 10
        self.confidence_threshold = 0.3
        
        logger.info("Language detector initialized with support for 19 languages")
    
    def _build_character_profiles(self) -> Dict[str, Dict[str, float]]:
        """Build character frequency profiles for different languages."""
        # Character frequency profiles for major languages
        # These are simplified profiles - in production, use more comprehensive data
        profiles = {
            "en": {  # English
                "e": 0.127, "t": 0.091, "a": 0.082, "o": 0.075, "i": 0.070,
                "n": 0.067, "s": 0.063, "h": 0.061, "r": 0.060, "d": 0.043,
                "l": 0.040, "c": 0.028, "u": 0.028, "m": 0.024, "w": 0.023,
                "f": 0.022, "g": 0.020, "y": 0.020, "p": 0.019, "b": 0.013
            },
            "es": {  # Spanish
                "e": 0.137, "a": 0.125, "o": 0.087, "s": 0.080, "n": 0.071,
                "r": 0.069, "i": 0.063, "t": 0.046, "l": 0.050, "d": 0.058,
                "u": 0.039, "c": 0.047, "m": 0.032, "p": 0.025, "b": 0.014,
                "g": 0.010, "v": 0.009, "y": 0.009, "q": 0.009, "h": 0.007
            },
            "fr": {  # French
                "e": 0.171, "s": 0.081, "a": 0.764, "i": 0.073, "t": 0.072,
                "n": 0.070, "r": 0.066, "u": 0.062, "l": 0.054, "o": 0.054,
                "d": 0.036, "c": 0.030, "m": 0.027, "p": 0.025, "é": 0.019,
                "v": 0.016, "q": 0.013, "f": 0.011, "b": 0.009, "g": 0.009
            },
            "de": {  # German
                "e": 0.174, "n": 0.098, "i": 0.075, "s": 0.072, "r": 0.070,
                "a": 0.065, "t": 0.061, "d": 0.051, "h": 0.476, "u": 0.435,
                "l": 0.037, "c": 0.031, "g": 0.030, "m": 0.025, "o": 0.025,
                "b": 0.020, "w": 0.018, "f": 0.017, "k": 0.012, "z": 0.011
            },
            "it": {  # Italian
                "e": 0.118, "a": 0.117, "i": 0.101, "o": 0.098, "n": 0.069,
                "t": 0.056, "r": 0.064, "s": 0.050, "l": 0.065, "c": 0.045,
                "d": 0.037, "u": 0.030, "p": 0.031, "m": 0.025, "v": 0.021,
                "g": 0.016, "f": 0.011, "b": 0.009, "q": 0.005, "h": 0.015
            },
            "pt": {  # Portuguese
                "a": 0.146, "e": 0.120, "o": 0.103, "s": 0.081, "r": 0.065,
                "i": 0.062, "n": 0.050, "d": 0.050, "m": 0.047, "u": 0.046,
                "t": 0.047, "c": 0.039, "l": 0.028, "p": 0.025, "v": 0.016,
                "g": 0.013, "h": 0.013, "q": 0.012, "b": 0.010, "f": 0.010
            },
            "ru": {  # Russian (Cyrillic)
                "о": 0.109, "е": 0.085, "а": 0.062, "и": 0.074, "н": 0.067,
                "т": 0.062, "с": 0.055, "р": 0.047, "в": 0.045, "л": 0.044,
                "к": 0.035, "м": 0.032, "д": 0.030, "п": 0.028, "у": 0.026,
                "я": 0.020, "ы": 0.019, "ь": 0.017, "г": 0.017, "з": 0.016
            },
            "zh": {  # Chinese (simplified characters most common)
                "的": 0.043, "了": 0.024, "在": 0.022, "是": 0.022, "我": 0.021,
                "有": 0.020, "和": 0.019, "就": 0.017, "不": 0.017, "人": 0.016,
                "都": 0.014, "一": 0.014, "个": 0.013, "也": 0.013, "上": 0.012,
                "他": 0.012, "为": 0.011, "来": 0.011, "会": 0.011, "要": 0.010
            },
            "ja": {  # Japanese (Hiragana/Katakana)
                "の": 0.055, "に": 0.045, "は": 0.040, "を": 0.035, "と": 0.030,
                "が": 0.025, "で": 0.025, "た": 0.022, "し": 0.020, "て": 0.020,
                "り": 0.018, "れ": 0.018, "る": 0.017, "ん": 0.015, "か": 0.015,
                "ー": 0.012, "ル": 0.010, "ト": 0.010, "ス": 0.009, "ン": 0.009
            },
            "ko": {  # Korean (Hangul)
                "이": 0.045, "의": 0.040, "을": 0.035, "는": 0.030, "에": 0.025,
                "가": 0.022, "고": 0.020, "다": 0.018, "한": 0.016, "로": 0.015,
                "서": 0.014, "리": 0.013, "하": 0.012, "지": 0.011, "기": 0.010,
                "어": 0.010, "으": 0.009, "인": 0.009, "수": 0.008, "도": 0.008
            },
            "ar": {  # Arabic
                "ا": 0.127, "ل": 0.097, "ي": 0.091, "م": 0.074, "و": 0.073,
                "ن": 0.067, "ر": 0.061, "ت": 0.055, "ب": 0.047, "ع": 0.043,
                "د": 0.035, "س": 0.034, "ف": 0.032, "ه": 0.030, "ك": 0.025,
                "ج": 0.020, "ق": 0.018, "ط": 0.015, "ز": 0.012, "ص": 0.010
            },
            "hi": {  # Hindi (Devanagari)
                "्": 0.085, "े": 0.070, "र": 0.065, "क": 0.060, "न": 0.055,
                "त": 0.050, "स": 0.045, "ि": 0.040, "ा": 0.038, "ल": 0.035,
                "म": 0.032, "ह": 0.030, "प": 0.028, "द": 0.025, "य": 0.022,
                "व": 0.020, "ग": 0.018, "ज": 0.015, "ब": 0.012, "च": 0.010
            },
            "nl": {  # Dutch
                "e": 0.189, "n": 0.100, "a": 0.074, "t": 0.079, "i": 0.065,
                "r": 0.641, "o": 0.061, "d": 0.056, "s": 0.037, "l": 0.035,
                "g": 0.034, "v": 0.025, "h": 0.024, "k": 0.022, "m": 0.022,
                "u": 0.019, "b": 0.015, "p": 0.015, "w": 0.015, "j": 0.015
            },
            "sv": {  # Swedish
                "a": 0.101, "e": 0.101, "n": 0.089, "r": 0.083, "t": 0.069,
                "s": 0.066, "l": 0.053, "i": 0.051, "o": 0.044, "d": 0.045,
                "ä": 0.020, "m": 0.035, "k": 0.032, "g": 0.028, "v": 0.024,
                "h": 0.021, "f": 0.020, "u": 0.018, "p": 0.018, "ö": 0.013
            },
            "da": {  # Danish
                "e": 0.167, "r": 0.089, "n": 0.073, "t": 0.069, "a": 0.061,
                "i": 0.057, "s": 0.058, "l": 0.050, "o": 0.044, "d": 0.042,
                "g": 0.403, "m": 0.032, "k": 0.334, "f": 0.024, "v": 0.024,
                "u": 0.021, "b": 0.020, "h": 0.016, "å": 0.012, "p": 0.017
            },
            "no": {  # Norwegian
                "e": 0.146, "r": 0.089, "n": 0.076, "t": 0.069, "a": 0.063,
                "i": 0.053, "s": 0.058, "l": 0.052, "o": 0.051, "d": 0.044,
                "g": 0.041, "k": 0.035, "m": 0.032, "f": 0.018, "v": 0.024,
                "u": 0.020, "h": 0.018, "p": 0.017, "b": 0.014, "å": 0.009
            },
            "fi": {  # Finnish
                "a": 0.122, "i": 0.108, "n": 0.087, "t": 0.087, "e": 0.079,
                "s": 0.078, "l": 0.056, "o": 0.051, "u": 0.045, "k": 0.049,
                "ä": 0.031, "r": 0.024, "v": 0.022, "j": 0.020, "m": 0.031,
                "h": 0.018, "y": 0.017, "p": 0.019, "d": 0.011, "ö": 0.004
            },
            "pl": {  # Polish
                "a": 0.891, "i": 0.081, "o": 0.860, "e": 0.078, "z": 0.064,
                "n": 0.052, "r": 0.046, "w": 0.046, "s": 0.043, "c": 0.040,
                "t": 0.039, "k": 0.035, "y": 0.038, "d": 0.032, "p": 0.031,
                "m": 0.029, "u": 0.025, "l": 0.021, "j": 0.023, "ł": 0.018
            },
            "tr": {  # Turkish
                "a": 0.119, "e": 0.089, "i": 0.084, "n": 0.069, "r": 0.068,
                "l": 0.058, "ı": 0.051, "k": 0.047, "d": 0.047, "t": 0.043,
                "s": 0.030, "m": 0.037, "u": 0.034, "o": 0.028, "b": 0.028,
                "y": 0.033, "ü": 0.018, "ç": 0.011, "ğ": 0.011, "ş": 0.015
            }
        }
        return profiles
    
    def _build_common_words(self) -> Dict[str, List[str]]:
        """Build lists of common words for each language."""
        return {
            "en": ["the", "be", "to", "of", "and", "a", "in", "that", "have", "i", "it", "for", "not", "on", "with", "he", "as", "you", "do", "at"],
            "es": ["el", "de", "que", "y", "a", "en", "un", "es", "se", "no", "te", "lo", "le", "da", "su", "por", "son", "con", "para", "al"],
            "fr": ["le", "de", "et", "à", "un", "il", "être", "et", "en", "avoir", "que", "pour", "dans", "ce", "son", "une", "sur", "avec", "ne", "se"],
            "de": ["der", "die", "und", "in", "den", "von", "zu", "das", "mit", "sich", "des", "auf", "für", "ist", "im", "dem", "nicht", "ein", "eine", "als"],
            "it": ["il", "di", "che", "e", "la", "per", "un", "in", "con", "del", "da", "a", "al", "le", "si", "dei", "sul", "una", "su", "alla"],
            "pt": ["o", "de", "a", "e", "do", "da", "em", "um", "para", "é", "com", "não", "uma", "os", "no", "se", "na", "por", "mais", "as"],
            "ru": ["в", "и", "не", "на", "я", "быть", "тот", "этот", "он", "весь", "к", "а", "мочь", "его", "свой", "что", "её", "так", "ещё", "её"],
            "zh": ["的", "了", "在", "是", "我", "有", "和", "就", "不", "人", "都", "一", "个", "也", "上", "他", "为", "来", "会", "要"],
            "ja": ["の", "に", "は", "を", "と", "が", "で", "た", "し", "て", "り", "れ", "る", "ん", "か", "だ", "ある", "する", "この", "その"],
            "ko": ["이", "의", "을", "는", "에", "가", "고", "다", "한", "로", "서", "리", "하", "지", "기", "어", "으", "인", "수", "도"],
            "ar": ["في", "من", "إلى", "على", "أن", "هذا", "كان", "قد", "التي", "أو", "كل", "بعد", "لم", "عند", "غير", "بين", "سوف", "حيث", "أكثر", "جدا"],
            "hi": ["के", "में", "की", "और", "को", "है", "से", "एक", "पर", "था", "यह", "भी", "जो", "ने", "तो", "हो", "इस", "लिए", "कि", "या"],
            "nl": ["de", "van", "het", "een", "in", "te", "dat", "op", "voor", "met", "als", "zijn", "er", "maar", "om", "door", "over", "ze", "uit", "aan"],
            "sv": ["och", "i", "att", "det", "som", "en", "på", "är", "för", "av", "med", "han", "den", "till", "har", "inte", "sin", "vara", "ett", "om"],
            "da": ["og", "i", "af", "til", "en", "det", "at", "på", "med", "for", "er", "har", "den", "ikke", "de", "et", "var", "som", "fra", "ved"],
            "no": ["og", "i", "det", "av", "en", "til", "å", "være", "på", "med", "for", "som", "har", "de", "er", "at", "den", "ikke", "et", "seg"],
            "fi": ["ja", "olla", "ei", "se", "hän", "että", "tämä", "kun", "niin", "kuin", "vaan", "jos", "voi", "tai", "mikä", "sen", "kaikki", "hänen", "tulee", "saada"],
            "pl": ["i", "w", "na", "z", "to", "się", "nie", "do", "że", "o", "a", "od", "dla", "po", "ze", "za", "co", "te", "ale", "być"],
            "tr": ["ve", "bir", "bu", "da", "ile", "o", "için", "de", "var", "daha", "kadar", "olan", "gibi", "çok", "ya", "her", "şey", "mi", "ben", "sen"]
        }
    
    def _build_script_patterns(self) -> Dict[str, str]:
        """Build regex patterns for different scripts."""
        return {
            "latin": r"[a-zA-ZÀ-ÿĀ-žА-я]",
            "cyrillic": r"[А-я]",
            "arabic": r"[\u0600-\u06FF]",
            "chinese": r"[\u4e00-\u9fff]",
            "japanese": r"[\u3040-\u309f\u30a0-\u30ff\u4e00-\u9fff]",
            "korean": r"[\uac00-\ud7af]",
            "devanagari": r"[\u0900-\u097f]",
            "thai": r"[\u0e00-\u0e7f]",
            "hebrew": r"[\u0590-\u05ff]"
        }
    
    def _build_language_patterns(self) -> Dict[str, List[str]]:
        """Build specific patterns for language identification."""
        return {
            "en": [r"\b(the|and|that|have|for|not|with|you|this|but|his|from|they)\b"],
            "es": [r"\b(que|con|por|para|una|este|esta|como|más|pero|todo|bien|puede)\b", r"ñ", r"¿", r"¡"],
            "fr": [r"\b(que|dans|pour|avoir|tout|faire|son|mettre|autre|pouvoir)\b", r"ç", r"[àâäéèêë]"],
            "de": [r"\b(und|der|die|das|den|dem|des|ein|eine|einen|einem|eines|sich|auch|nach|werden|können)\b", r"[äöüß]"],
            "it": [r"\b(che|con|per|una|suo|come|dalla|della|sono|stato|quanto|molto|dove|cosa)\b", r"[àèéìîòù]"],
            "pt": [r"\b(que|não|uma|para|todo|bem|ser|estar|ter|fazer|ver|dar|saber|poder)\b", r"[ãçõáàâéêíóôú]"],
            "ru": [r"\b(что|это|как|так|если|где|когда|почему|который|какой|должен|можно)\b"],
            "nl": [r"\b(het|een|van|in|op|voor|met|als|zijn|er|maar|om|door|over|ze|uit|aan)\b", r"ij", r"[ëéèáàóò]"],
            "sv": [r"\b(och|att|det|som|på|är|för|av|med|han|den|till|har|inte|sin|vara|ett|om)\b", r"[åäö]"],
            "da": [r"\b(og|af|til|en|det|at|på|med|for|er|har|den|ikke|de|et|var|som|fra|ved)\b", r"[æøå]"], 
            "no": [r"\b(og|det|av|en|til|være|på|med|for|som|har|de|er|at|den|ikke|et|seg)\b", r"[æøå]"],
            "fi": [r"\b(ja|olla|ei|se|hän|että|tämä|kun|niin|kuin|vaan|jos|voi|tai|mikä)\b", r"[äöy]"],
            "pl": [r"\b(że|się|nie|do|na|za|jak|ale|czy|już|tylko|bardzo|gdzie|kiedy)\b", r"[ąćęłńóśźż]"],
            "tr": [r"\b(ve|bir|bu|da|ile|için|daha|kadar|olan|gibi|çok|her|şey|ben|sen)\b", r"[çğıöşü]"]
        }
    
    def detect_language(self, text: str, min_confidence: Optional[float] = None) -> LanguageDetectionResult:
        """
        Detect the language of given text using multiple methods.
        
        Args:
            text: Input text to analyze
            min_confidence: Minimum confidence threshold (uses default if None)
        
        Returns:
            LanguageDetectionResult with detection details
        """
        if not text or len(text.strip()) < self.min_text_length:
            return LanguageDetectionResult(
                language="unknown",
                confidence=0.0,
                alternatives=[],
                text_quality=0.0
            )
        
        # Clean and normalize text
        cleaned_text = self._clean_text(text)
        text_quality = self._assess_text_quality(cleaned_text)
        
        # Multiple detection methods
        script_results = self._detect_script(cleaned_text)
        ngram_results = self._detect_by_ngrams(cleaned_text)
        word_results = self._detect_by_words(cleaned_text)
        pattern_results = self._detect_by_patterns(cleaned_text)
        
        # Combine results with weighted scoring
        combined_scores = self._combine_detection_results(
            script_results, ngram_results, word_results, pattern_results
        )
        
        # Get top languages
        sorted_languages = sorted(combined_scores.items(), key=lambda x: x[1], reverse=True)
        
        if not sorted_languages:
            return LanguageDetectionResult(
                language="unknown",
                confidence=0.0,
                alternatives=[],
                text_quality=text_quality
            )
        
        primary_lang, primary_score = sorted_languages[0]
        alternatives = [(lang, score) for lang, score in sorted_languages[1:6]]  # Top 5 alternatives
        
        # Check if confidence meets threshold
        confidence_threshold = min_confidence or self.confidence_threshold
        if primary_score < confidence_threshold:
            primary_lang = "unknown"
            primary_score = 0.0
        
        # Detect mixed languages
        mixed_languages = len([score for _, score in sorted_languages[:3] if score > 0.2]) > 1
        
        return LanguageDetectionResult(
            language=primary_lang,
            confidence=primary_score,
            alternatives=alternatives,
            script=script_results.get("dominant_script"),
            mixed_languages=mixed_languages,
            text_quality=text_quality
        )
    
    def _clean_text(self, text: str) -> str:
        """Clean and normalize text for analysis."""
        # Remove URLs, emails, and common non-linguistic content
        text = re.sub(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', '', text)
        text = re.sub(r'\S+@\S+', '', text)
        text = re.sub(r'\d+', ' ', text)  # Replace numbers with spaces
        text = re.sub(r'[^\w\s]', ' ', text, flags=re.UNICODE)  # Keep only word characters and spaces
        text = re.sub(r'\s+', ' ', text)  # Normalize whitespace
        return text.strip().lower()
    
    def _assess_text_quality(self, text: str) -> float:
        """Assess text quality for detection reliability."""
        if not text:
            return 0.0
        
        length_score = min(len(text) / 100, 1.0)  # Longer text is better
        word_count = len(text.split())
        word_score = min(word_count / 20, 1.0)  # More words is better
        
        # Check for repetitive content
        words = text.split()
        unique_words = len(set(words))
        diversity_score = unique_words / max(len(words), 1) if words else 0
        
        return (length_score + word_score + diversity_score) / 3
    
    def _detect_script(self, text: str) -> Dict[str, Any]:
        """Detect script types in the text."""
        script_counts = {}
        total_chars = 0
        
        for char in text:
            if char.isalpha():
                total_chars += 1
                for script, pattern in self.script_patterns.items():
                    if re.match(pattern, char):
                        script_counts[script] = script_counts.get(script, 0) + 1
                        break
        
        if total_chars == 0:
            return {"dominant_script": None, "script_scores": {}}
        
        # Calculate script percentages
        script_scores = {script: count / total_chars for script, count in script_counts.items()}
        dominant_script = max(script_scores.items(), key=lambda x: x[1])[0] if script_scores else None
        
        return {
            "dominant_script": dominant_script,
            "script_scores": script_scores
        }
    
    def _detect_by_ngrams(self, text: str) -> Dict[str, float]:
        """Detect language using character n-gram analysis."""
        if len(text) < 3:
            return {}
        
        # Generate character trigrams
        trigrams = [text[i:i+3] for i in range(len(text) - 2)]
        trigram_freq = Counter(trigrams)
        total_trigrams = len(trigrams)
        
        scores = {}
        
        for lang, profile in self.character_profiles.items():
            score = 0.0
            for trigram, count in trigram_freq.items():
                trigram_freq_norm = count / total_trigrams
                
                # Simple scoring based on character frequency
                for char in trigram:
                    if char in profile:
                        score += profile[char] * trigram_freq_norm
            
            scores[lang] = score / max(len(trigrams), 1)
        
        return scores
    
    def _detect_by_words(self, text: str) -> Dict[str, float]:
        """Detect language using common word analysis."""
        words = text.split()
        if not words:
            return {}
        
        scores = {}
        total_words = len(words)
        
        for lang, common_words in self.common_words.items():
            matches = sum(1 for word in words if word in common_words)
            scores[lang] = matches / total_words
        
        return scores
    
    def _detect_by_patterns(self, text: str) -> Dict[str, float]:
        """Detect language using specific patterns."""
        scores = {}
        
        for lang, patterns in self.language_patterns.items():
            score = 0.0
            for pattern in patterns:
                matches = len(re.findall(pattern, text, re.IGNORECASE))
                score += matches
            
            # Normalize by text length
            scores[lang] = score / max(len(text.split()), 1)
        
        return scores
    
    def _combine_detection_results(self, script_results: Dict, ngram_results: Dict,
                                 word_results: Dict, pattern_results: Dict) -> Dict[str, float]:
        """Combine results from different detection methods."""
        all_languages = set()
        all_languages.update(ngram_results.keys())
        all_languages.update(word_results.keys())
        all_languages.update(pattern_results.keys())
        
        combined_scores = {}
        
        for lang in all_languages:
            # Weighted combination of different methods
            ngram_score = ngram_results.get(lang, 0.0)
            word_score = word_results.get(lang, 0.0)
            pattern_score = pattern_results.get(lang, 0.0)
            
            # Weight: n-grams 40%, words 40%, patterns 20%
            combined_score = (ngram_score * 0.4 + word_score * 0.4 + pattern_score * 0.2)
            
            # Boost score if script matches language expectations
            script_boost = self._get_script_boost(lang, script_results.get("dominant_script"))
            combined_score *= script_boost
            
            combined_scores[lang] = combined_score
        
        return combined_scores
    
    def _get_script_boost(self, language: str, dominant_script: Optional[str]) -> float:
        """Get score boost based on script compatibility."""
        if not dominant_script:
            return 1.0
        
        # Map languages to expected scripts
        script_mapping = {
            "en": "latin", "es": "latin", "fr": "latin", "de": "latin", "it": "latin",
            "pt": "latin", "nl": "latin", "sv": "latin", "da": "latin", "no": "latin",
            "fi": "latin", "pl": "latin", "tr": "latin",
            "ru": "cyrillic",
            "ar": "arabic",
            "zh": "chinese",
            "ja": "japanese",
            "ko": "korean",
            "hi": "devanagari"
        }
        
        expected_script = script_mapping.get(language)
        if expected_script == dominant_script:
            return 1.2  # 20% boost for matching script
        elif expected_script and dominant_script and expected_script != dominant_script:
            return 0.8  # 20% penalty for mismatched script
        else:
            return 1.0  # No change if uncertain
    
    @lru_cache(maxsize=1000)
    def detect_language_cached(self, text: str) -> LanguageDetectionResult:
        """Cached version of language detection for frequently used texts."""
        return self.detect_language(text)
    
    def detect_languages_batch(self, texts: List[str]) -> List[LanguageDetectionResult]:
        """Detect languages for multiple texts efficiently."""
        return [self.detect_language(text) for text in texts]
    
    def get_detection_statistics(self) -> Dict[str, Any]:
        """Get statistics about the language detector."""
        return {
            "supported_languages": len(self.character_profiles),
            "supported_scripts": len(self.script_patterns),
            "min_text_length": self.min_text_length,
            "confidence_threshold": self.confidence_threshold,
            "cache_size": self.detect_language_cached.cache_info().currsize if hasattr(self.detect_language_cached, 'cache_info') else 0
        }

# Global instance
_language_detector = None

def get_language_detector() -> LanguageDetector:
    """Get the global language detector instance."""
    global _language_detector
    if _language_detector is None:
        _language_detector = LanguageDetector()
    return _language_detector

def detect_language(text: str, min_confidence: Optional[float] = None) -> LanguageDetectionResult:
    """Shorthand function for language detection."""
    return get_language_detector().detect_language(text, min_confidence)

if __name__ == "__main__":
    # Demo usage
    detector = LanguageDetector()
    
    test_texts = [
        "This is a sample English text for testing language detection.",
        "Esto es un texto de ejemplo en español para probar la detección de idiomas.",
        "Ceci est un texte d'exemple en français pour tester la détection de langue.",
        "Dies ist ein Beispieltext auf Deutsch zum Testen der Spracherkennung.",
        "Questo è un testo di esempio in italiano per testare il rilevamento della lingua.",
        "这是一个中文示例文本，用于测试语言检测。",
        "これは言語検出をテストするための日本語のサンプルテキストです。",
        "이것은 언어 감지를 테스트하기 위한 한국어 샘플 텍스트입니다."
    ]
    
    for text in test_texts:
        result = detector.detect_language(text)
        print(f"Text: {text[:50]}...")
        print(f"Detected: {result.language} (confidence: {result.confidence:.3f})")
        print(f"Alternatives: {result.alternatives[:3]}")
        print("---")