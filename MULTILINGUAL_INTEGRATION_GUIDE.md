# Multilingual RAG System Integration Guide

*Authored by: Harry Lewis (louie)*  
*Date: 2025-01-08*

## Overview

This guide provides comprehensive instructions for integrating and using the multilingual capabilities of the RAG system. The implementation includes automatic language detection, translation services, internationalization support, and language-aware document processing.

## Architecture Overview

```
┌─────────────────────┐    ┌─────────────────────┐    ┌─────────────────────┐
│   Language          │    │   Translation       │    │   I18n Manager      │
│   Detection         │    │   Service           │    │                     │
│   - Auto-detect     │    │   - Offline trans   │    │   - UI localization │
│   - Confidence      │    │   - Caching         │    │   - Message mgmt    │
│   - Script ID       │    │   - Quality scoring │    │   - Pluralization   │
└─────────────────────┘    └─────────────────────┘    └─────────────────────┘
           │                          │                          │
           └──────────────────────────┼──────────────────────────┘
                                      │
                    ┌─────────────────────┐
                    │  Multilingual RAG   │
                    │  - Language-aware   │
                    │  - Cross-lang search│
                    │  - Smart embeddings │
                    │  - Mixed lang detect│
                    └─────────────────────┘
                              │
                    ┌─────────────────────┐
                    │  Multilingual UI    │
                    │  - Localized text   │
                    │  - RTL support      │
                    │  - Cultural format  │
                    │  - Dynamic switching│
                    └─────────────────────┘
```

## Components Overview

### 1. I18n Manager (`i18n_manager.py`)
- **Purpose**: Core internationalization framework
- **Features**: Message loading, pluralization, locale formatting
- **Supported Languages**: 19 languages including major world languages
- **Key Functions**:
  - `get_message()`: Retrieve localized text
  - `get_plural_message()`: Handle pluralization
  - `format_date()`, `format_time()`: Locale-specific formatting

### 2. Language Detection (`language_detection.py`)
- **Purpose**: Automatic language identification
- **Methods**: Character n-grams, common words, script patterns
- **Features**: Confidence scoring, mixed language detection, text quality assessment
- **Supported**: 19+ languages with script detection

### 3. Translation Service (`translation_service.py`)
- **Purpose**: Offline translation capabilities
- **Features**: Dictionary-based translation, caching, background jobs
- **Privacy**: Completely offline, no external API calls
- **Extensible**: Ready for integration with advanced models

### 4. Multilingual RAG (`multilingual_rag.py`)
- **Purpose**: Language-aware document processing and querying
- **Features**: Language-specific embeddings, cross-language search, multilingual responses
- **Integration**: Seamless integration with existing RAG system

### 5. Multilingual UI (`multilingual_ui.py`)
- **Purpose**: UI localization and multilingual interface support
- **Features**: Dynamic language switching, RTL support, cultural formatting

## Installation and Setup

### 1. Install Dependencies

```bash
# Navigate to the app directory
cd app

# Install new multilingual dependencies
pip install -r requirements.txt

# The following packages are now included:
# - langdetect==1.0.9
# - babel==2.13.1
# - regex==2023.10.3
# - unicodedata2==15.1.0
```

### 2. Initialize Localization Resources

```python
from app.i18n_manager import get_i18n_manager

# Initialize and create language packs
i18n = get_i18n_manager()

# Create additional language packs if needed
i18n.create_language_pack("pt")  # Portuguese
i18n.create_language_pack("ru")  # Russian
```

### 3. Test Installation

```bash
# Run multilingual tests
python test_multilingual_support.py

# Or use pytest
pytest test_multilingual_support.py -v
```

## Integration with Existing RAG System

### 1. Update Main Application

Add multilingual imports to your `main.py`:

```python
# Add to existing imports
from multilingual_rag import get_multilingual_rag_system, MultilingualRAGResponse
from multilingual_ui import get_multilingual_ui_helper, t, tp
from language_detection import get_language_detector
from translation_service import get_translation_service

# Initialize multilingual components in startup
@app.on_event("startup")
async def startup_event():
    # ... existing startup code ...
    
    # Initialize multilingual components
    multilingual_rag = get_multilingual_rag_system()
    ui_helper = get_multilingual_ui_helper()
    language_detector = get_language_detector()
    translation_service = get_translation_service()
    
    logger.info("Multilingual services initialized")
```

### 2. Add Multilingual API Endpoints

```python
# Add to main.py

@app.post("/api/v1/multilingual/query", response_model=MultilingualRAGResponse)
async def multilingual_query_endpoint(
    query: str,
    target_language: Optional[str] = None,
    max_chunks: Optional[int] = None,
    enable_cross_language: bool = True
):
    """Enhanced multilingual query endpoint."""
    try:
        multilingual_rag = get_multilingual_rag_system()
        response = await multilingual_rag.multilingual_query(
            query=query,
            target_language=target_language,
            max_chunks=max_chunks,
            enable_cross_language=enable_cross_language
        )
        return response
    except Exception as e:
        app_error = handle_error(e)
        logger.error(f"Multilingual query error: {app_error.to_dict()}")
        raise HTTPException(status_code=500, detail=app_error.user_message)

@app.get("/api/v1/multilingual/languages")
async def get_supported_languages():
    """Get supported languages for the system."""
    try:
        multilingual_rag = get_multilingual_rag_system()
        ui_helper = get_multilingual_ui_helper()
        
        return {
            "rag_languages": multilingual_rag.get_supported_languages(),
            "ui_languages": [lang.code for lang in ui_helper.get_available_ui_languages()],
            "translation_capabilities": get_translation_service().get_translation_capabilities()
        }
    except Exception as e:
        app_error = handle_error(e)
        raise HTTPException(status_code=500, detail=app_error.user_message)

@app.post("/api/v1/multilingual/translate")
async def translate_text_endpoint(
    text: str,
    target_language: str,
    source_language: Optional[str] = None
):
    """Translate text endpoint."""
    try:
        from translation_service import TranslationRequest
        
        translation_service = get_translation_service()
        request = TranslationRequest(
            text=text,
            source_language=source_language,
            target_language=target_language
        )
        
        result = await translation_service.translate(request)
        return {
            "original_text": result.original_text,
            "translated_text": result.translated_text,
            "source_language": result.source_language,
            "target_language": result.target_language,
            "confidence": result.confidence,
            "method": result.translation_method
        }
    except Exception as e:
        app_error = handle_error(e)
        raise HTTPException(status_code=500, detail=app_error.user_message)

@app.post("/api/v1/multilingual/detect-language")
async def detect_language_endpoint(text: str):
    """Detect language of text."""
    try:
        detector = get_language_detector()
        result = detector.detect_language(text)
        
        return {
            "language": result.language,
            "confidence": result.confidence,
            "alternatives": result.alternatives,
            "script": result.script,
            "mixed_languages": result.mixed_languages,
            "text_quality": result.text_quality
        }
    except Exception as e:
        app_error = handle_error(e)
        raise HTTPException(status_code=500, detail=app_error.user_message)
```

### 3. Update Document Processing

Modify document upload to include language detection:

```python
# Update in main.py document upload endpoint

@app.post("/api/v1/documents/upload")
async def upload_single_file_v1(file: UploadFile = File(...)):
    """Upload with automatic language detection."""
    try:
        # ... existing upload code ...
        
        # Add language detection
        multilingual_rag = get_multilingual_rag_system()
        document = {
            "title": file.filename,
            "content": content_str,  # extracted content
            "doc_id": doc_id,
            # ... other metadata ...
        }
        
        # Process with multilingual analysis
        multilingual_doc = await multilingual_rag.process_multilingual_document(document)
        
        # Add language metadata to response
        return {
            "message": f"File {file.filename} processed",
            "doc_id": multilingual_doc.doc_id,
            "detected_language": multilingual_doc.detected_language,
            "language_confidence": multilingual_doc.language_confidence,
            "processing_notes": multilingual_doc.processing_notes,
            "success": True
        }
        
    except Exception as e:
        # ... error handling ...
```

## Frontend Integration

### 1. Language Selector Component

```javascript
// Example React component for language selection
import React, { useState, useEffect } from 'react';

const LanguageSelector = ({ onLanguageChange }) => {
  const [languages, setLanguages] = useState([]);
  const [currentLanguage, setCurrentLanguage] = useState('en');

  useEffect(() => {
    // Fetch available languages
    fetch('/api/v1/multilingual/languages')
      .then(response => response.json())
      .then(data => setLanguages(data.ui_languages));
  }, []);

  const handleLanguageChange = (langCode) => {
    setCurrentLanguage(langCode);
    onLanguageChange(langCode);
    
    // Update UI language
    fetch('/api/v1/ui/set-language', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ language: langCode })
    });
  };

  return (
    <select 
      value={currentLanguage} 
      onChange={(e) => handleLanguageChange(e.target.value)}
      className="language-selector"
    >
      {languages.map(lang => (
        <option key={lang} value={lang}>
          {/* Display language name */}
          {lang.toUpperCase()}
        </option>
      ))}
    </select>
  );
};
```

### 2. Multilingual Chat Interface

```javascript
// Enhanced chat with multilingual support
const MultilingualChat = () => {
  const [query, setQuery] = useState('');
  const [targetLanguage, setTargetLanguage] = useState('en');
  const [response, setResponse] = useState(null);

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    try {
      const response = await fetch('/api/v1/multilingual/query', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          query: query,
          target_language: targetLanguage,
          max_chunks: 5,
          enable_cross_language: true
        })
      });
      
      const result = await response.json();
      setResponse(result);
    } catch (error) {
      console.error('Query failed:', error);
    }
  };

  return (
    <div className="multilingual-chat">
      <form onSubmit={handleSubmit}>
        <div className="query-input">
          <textarea
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Ask a question in any language..."
            className="query-textarea"
          />
        </div>
        
        <div className="language-controls">
          <label>
            Response Language:
            <select 
              value={targetLanguage}
              onChange={(e) => setTargetLanguage(e.target.value)}
            >
              <option value="en">English</option>
              <option value="es">Español</option>
              <option value="fr">Français</option>
              {/* Add more languages */}
            </select>
          </label>
        </div>
        
        <button type="submit">Send Query</button>
      </form>
      
      {response && (
        <div className="response">
          <div className="answer">{response.answer}</div>
          <div className="metadata">
            <span>Query Language: {response.query_language}</span>
            <span>Answer Language: {response.answer_language}</span>
            <span>Confidence: {response.confidence_score.toFixed(3)}</span>
            {response.language_mixing_detected && (
              <span className="warning">Mixed languages detected</span>
            )}
          </div>
        </div>
      )}
    </div>
  );
};
```

## Usage Examples

### 1. Basic Language Detection

```python
from app.language_detection import get_language_detector

detector = get_language_detector()

# Detect language of text
result = detector.detect_language("Bonjour, comment allez-vous?")
print(f"Language: {result.language}")  # fr
print(f"Confidence: {result.confidence}")  # 0.95
print(f"Alternatives: {result.alternatives}")  # [('en', 0.2), ('es', 0.1)]
```

### 2. Translation

```python
from app.translation_service import get_translation_service, TranslationRequest
import asyncio

async def translate_example():
    service = get_translation_service()
    
    request = TranslationRequest(
        text="Hello, how are you?",
        source_language="en",
        target_language="es"
    )
    
    result = await service.translate(request)
    print(f"Original: {result.original_text}")
    print(f"Translated: {result.translated_text}")
    print(f"Confidence: {result.confidence}")

asyncio.run(translate_example())
```

### 3. Multilingual RAG Query

```python
from app.multilingual_rag import get_multilingual_rag_system
import asyncio

async def multilingual_query_example():
    rag = get_multilingual_rag_system()
    
    # Query in Spanish, respond in English
    response = await rag.multilingual_query(
        query="¿Qué documentos tienes sobre inteligencia artificial?",
        target_language="en",
        max_chunks=3
    )
    
    print(f"Query Language: {response.query_language}")  # es
    print(f"Answer Language: {response.answer_language}")  # en
    print(f"Answer: {response.answer}")
    print(f"Sources: {len(response.sources)}")

asyncio.run(multilingual_query_example())
```

### 4. UI Localization

```python
from app.multilingual_ui import get_multilingual_ui_helper

ui = get_multilingual_ui_helper()

# Set UI language
ui.set_ui_language("es")

# Get localized text
welcome = ui.t("welcome")  # "Bienvenido"
doc_count = ui.tp("document_count", 5, "documents", count=5)  # "5 documentos"

# Format dates and numbers
from datetime import datetime
date_str = ui.format_date_for_ui(datetime.now())  # Spanish format
number_str = ui.format_number_for_ui(1234.56)  # Spanish number format
```

## Configuration

### 1. Language Settings

```python
# Configure supported languages
from app.i18n_manager import get_i18n_manager

i18n = get_i18n_manager()

# Enable/disable languages
config = i18n.get_language_config("fr")
config.enabled = True  # Enable French

# Set default language
i18n.default_language = "en"
```

### 2. Translation Settings

```python
from app.translation_service import get_translation_service

service = get_translation_service()

# Configure caching
service.max_cache_size = 5000
service.cache_expiry_days = 60

# Configure background jobs
service.job_executor._max_workers = 4
```

### 3. RAG Settings

```python
from app.multilingual_rag import get_multilingual_rag_system

rag = get_multilingual_rag_system()

# Configure search behavior
rag.enable_cross_language_search = True
rag.confidence_threshold = 0.5

# Configure language-specific strategies
rag.language_search_strategies["zh"] = {
    "chunk_size": 250,
    "overlap": 25
}
```

## Performance Considerations

### 1. Caching Strategy

- **Translation Cache**: Automatically caches translation results
- **Language Detection Cache**: LRU cache for frequently detected texts
- **Embedding Cache**: Language-specific embedding caching
- **UI Message Cache**: Localized message caching

### 2. Memory Usage

- **Language Models**: ~50MB per language for embeddings
- **Translation Dictionaries**: ~5MB per language pair
- **UI Messages**: ~1MB per language pack
- **Detection Models**: ~10MB for character profiles

### 3. Performance Optimization

```python
# Batch operations for better performance
detector = get_language_detector()
results = detector.detect_languages_batch(texts)

# Use background translation for non-urgent tasks
service = get_translation_service()
job_id = service.start_background_translation(request)

# Pre-load frequently used languages
ui = get_multilingual_ui_helper()
for lang in ["en", "es", "fr"]:
    ui.i18n_manager.load_language(lang)
```

## Troubleshooting

### Common Issues

1. **Language Not Detected Correctly**
   - Increase minimum text length
   - Check text quality score
   - Verify language is in supported list

2. **Translation Quality Poor**
   - Current implementation is dictionary-based
   - Consider integrating advanced models
   - Add more dictionary entries

3. **UI Text Not Localized**
   - Check if language pack exists
   - Verify message keys are correct
   - Ensure language is loaded

4. **Performance Issues**
   - Enable caching
   - Use batch operations
   - Pre-load common languages

### Debug Mode

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# Enable debug logging for multilingual components
logging.getLogger("app.language_detection").setLevel(logging.DEBUG)
logging.getLogger("app.translation_service").setLevel(logging.DEBUG)
logging.getLogger("app.multilingual_rag").setLevel(logging.DEBUG)
```

## Testing

### Run Tests

```bash
# Run all multilingual tests
python test_multilingual_support.py

# Run specific test classes
pytest test_multilingual_support.py::TestI18nManager -v
pytest test_multilingual_support.py::TestLanguageDetection -v
pytest test_multilingual_support.py::TestTranslationService -v
pytest test_multilingual_support.py::TestMultilingualRAG -v
pytest test_multilingual_support.py::TestMultilingualUI -v
```

### Test Coverage

The test suite covers:
- Language detection accuracy
- Translation functionality
- UI localization
- RAG integration
- Error handling
- Performance characteristics

## Future Extensions

### 1. Advanced Translation Models

```python
# Integration point for advanced models
class AdvancedTranslationEngine:
    def __init__(self):
        # Load Helsinki-NLP MarianMT models
        # Load Facebook M2M-100 models
        # Load Google T5 multilingual models
        pass
    
    def translate_with_model(self, text, src_lang, tgt_lang):
        # Advanced neural translation
        pass
```

### 2. Voice Interface Support

```python
# Speech-to-text multilingual support
class MultilingualSpeechInterface:
    def detect_speech_language(self, audio):
        # Detect language from audio
        pass
    
    def transcribe_multilingual(self, audio, language):
        # Transcribe with language-specific models
        pass
```

### 3. Advanced Language Models

```python
# Integration with large multilingual models
class MultilingualLLMInterface:
    def __init__(self):
        # Load mBERT, XLM-R, mT5 models
        pass
    
    def generate_multilingual_response(self, query, context, target_lang):
        # Generate responses with advanced models
        pass
```

## Contributing

To contribute to the multilingual functionality:

1. **Adding New Languages**:
   - Add language configuration to `i18n_manager.py`
   - Create message files in `locales/{lang}/`
   - Add character profiles to `language_detection.py`
   - Add translation dictionaries to `translation_service.py`

2. **Improving Detection**:
   - Enhance character profiles
   - Add more common words
   - Improve script detection patterns

3. **Better Translation**:
   - Add more dictionary entries
   - Implement rule-based improvements
   - Integrate with advanced models

4. **UI Enhancements**:
   - Add more UI languages
   - Improve cultural formatting
   - Add region-specific variants

## Security Considerations

- **Data Privacy**: All processing is offline, no external API calls
- **Input Validation**: All text inputs are validated and sanitized
- **Resource Limits**: Configurable limits prevent resource exhaustion
- **Error Handling**: Comprehensive error handling prevents information leakage
- **Access Control**: Language preferences are user-specific

## License and Attribution

This multilingual implementation is part of the RAG system and follows the same licensing terms. The language detection algorithms are custom implementations designed for privacy and offline operation.

---

For technical support or questions about the multilingual functionality, please refer to the test suite and inline documentation in the source code.