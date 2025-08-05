"""
Authored by: AI/ML Engineer (jackson)
Date: 2025-08-05

Intelligent Tagging System

ML-based automatic tagging and categorization system for documents.
Provides semantic tags, hierarchical classification, and confidence scoring.
"""

import os
import json
import time
import logging
from typing import List, Dict, Optional, Set, Tuple, Any
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from collections import defaultdict, Counter
import re
import math
import asyncio
from functools import lru_cache

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.naive_bayes import MultinomialNB
from sklearn.linear_model import LogisticRegression
from sentence_transformers import SentenceTransformer, util

from rag_backend import get_rag_system
from document_manager import DocumentManager
from document_analytics import get_analytics_engine
from performance_cache import get_document_cache
from error_handlers import handle_error, ApplicationError, ErrorCategory, ErrorSeverity

logger = logging.getLogger(__name__)

@dataclass
class Tag:
    """Individual tag with metadata."""
    name: str
    category: str
    confidence: float
    source: str  # 'ml_auto', 'rule_based', 'user_manual'
    context: str
    related_terms: List[str]
    created_at: datetime

@dataclass
class TagSuggestion:
    """Tag suggestion with reasoning."""
    tag: str
    confidence: float
    reasoning: str
    similar_tags: List[str]
    auto_apply: bool

@dataclass 
class DocumentTags:
    """Complete tagging information for a document."""
    doc_id: str
    tags: List[Tag]
    suggested_tags: List[TagSuggestion]
    hierarchy: Dict[str, List[str]]  # category -> tags
    semantic_clusters: List[str]
    generated_at: datetime
    model_version: str

class TagTaxonomy:
    """Hierarchical tag taxonomy and relationship management."""
    
    def __init__(self):
        self.taxonomy = self._build_base_taxonomy()
        self.synonyms = self._build_synonym_map()
        self.exclusions = self._build_exclusion_rules()

    def _build_base_taxonomy(self) -> Dict[str, Dict[str, List[str]]]:
        """Build hierarchical tag taxonomy."""
        return {
            'content_type': {
                'technical': ['api', 'code', 'programming', 'software', 'development', 'system'],
                'business': ['strategy', 'marketing', 'sales', 'finance', 'operations', 'management'],
                'research': ['study', 'analysis', 'experiment', 'methodology', 'findings', 'data'],
                'educational': ['tutorial', 'guide', 'course', 'training', 'learning', 'instruction'],
                'legal': ['contract', 'policy', 'compliance', 'regulation', 'terms', 'agreement']
            },
            'domain': {
                'technology': ['ai', 'ml', 'blockchain', 'cloud', 'mobile', 'web', 'security', 'data'],
                'healthcare': ['medical', 'clinical', 'patient', 'treatment', 'diagnosis', 'pharmaceutical'],
                'finance': ['banking', 'investment', 'insurance', 'trading', 'cryptocurrency', 'fintech'],
                'education': ['academic', 'university', 'school', 'curriculum', 'assessment', 'pedagogy'],
                'manufacturing': ['production', 'supply_chain', 'quality', 'automation', 'logistics']
            },
            'purpose': {
                'documentation': ['manual', 'specification', 'readme', 'wiki', 'help', 'faq'],
                'analysis': ['report', 'insights', 'metrics', 'dashboard', 'visualization', 'statistics'],
                'planning': ['roadmap', 'strategy', 'proposal', 'requirements', 'design', 'architecture'],
                'communication': ['email', 'memo', 'announcement', 'newsletter', 'presentation', 'meeting']
            },
            'format': {
                'structured': ['table', 'list', 'form', 'template', 'schema', 'format'],
                'narrative': ['story', 'case_study', 'article', 'blog', 'essay', 'description'],
                'procedural': ['steps', 'process', 'workflow', 'checklist', 'procedure', 'protocol']
            }
        }

    def _build_synonym_map(self) -> Dict[str, Set[str]]:
        """Build synonym mapping for tag normalization."""
        return {
            'api': {'api', 'interface', 'endpoint', 'service'},
            'ml': {'ml', 'machine_learning', 'ai', 'artificial_intelligence'},
            'security': {'security', 'cybersecurity', 'infosec', 'protection'},
            'database': {'database', 'db', 'data_storage', 'persistence'},
            'frontend': {'frontend', 'ui', 'user_interface', 'client_side'},
            'backend': {'backend', 'server_side', 'api', 'service_layer'},
            'mobile': {'mobile', 'ios', 'android', 'app', 'smartphone'},
            'web': {'web', 'website', 'browser', 'html', 'css', 'javascript'},
            'data': {'data', 'dataset', 'information', 'analytics'},
            'testing': {'testing', 'qa', 'quality_assurance', 'validation'},
            'deployment': {'deployment', 'release', 'production', 'publishing'},
            'monitoring': {'monitoring', 'observability', 'logging', 'metrics'}
        }

    def _build_exclusion_rules(self) -> List[Tuple[str, str]]:
        """Build tag exclusion rules (mutually exclusive tags)."""
        return [
            ('frontend', 'backend'),
            ('manual', 'automated'),
            ('internal', 'external'),
            ('development', 'production'),
            ('draft', 'final')
        ]

    def normalize_tag(self, tag: str) -> str:
        """Normalize a tag using synonym mapping."""
        tag_lower = tag.lower().replace(' ', '_')
        
        for canonical, synonyms in self.synonyms.items():
            if tag_lower in synonyms:
                return canonical
        
        return tag_lower

    def get_tag_hierarchy(self, tag: str) -> Optional[Tuple[str, str]]:
        """Get the hierarchy (category, subcategory) for a tag."""
        normalized_tag = self.normalize_tag(tag)
        
        for category, subcategories in self.taxonomy.items():
            for subcategory, tags in subcategories.items():
                if normalized_tag in tags:
                    return (category, subcategory)
        
        return None

    def suggest_related_tags(self, tag: str, max_suggestions: int = 5) -> List[str]:
        """Suggest related tags based on hierarchy."""
        hierarchy = self.get_tag_hierarchy(tag)
        if not hierarchy:
            return []
        
        category, subcategory = hierarchy
        related_tags = self.taxonomy[category][subcategory].copy()
        
        # Remove the original tag
        normalized_tag = self.normalize_tag(tag)
        if normalized_tag in related_tags:
            related_tags.remove(normalized_tag)
        
        return related_tags[:max_suggestions]

    def validate_tag_combination(self, tags: List[str]) -> List[str]:
        """Validate tag combination and resolve conflicts."""
        normalized_tags = [self.normalize_tag(tag) for tag in tags]
        valid_tags = []
        
        for tag in normalized_tags:
            # Check for exclusions
            conflicted = False
            for existing_tag in valid_tags:
                for tag1, tag2 in self.exclusions:
                    if (tag == tag1 and existing_tag == tag2) or (tag == tag2 and existing_tag == tag1):
                        conflicted = True
                        break
                if conflicted:
                    break
            
            if not conflicted:
                valid_tags.append(tag)
        
        return valid_tags

class SemanticTagger:
    """Semantic tagging using embeddings and clustering."""
    
    def __init__(self):
        self.encoder = SentenceTransformer('all-MiniLM-L6-v2')
        self.tag_embeddings = {}
        self.cluster_cache = {}
        self._build_tag_embeddings()

    def _build_tag_embeddings(self):
        """Pre-compute embeddings for common tags."""
        common_tags = [
            'api', 'frontend', 'backend', 'database', 'security', 'testing',
            'documentation', 'tutorial', 'guide', 'analysis', 'report',
            'machine_learning', 'artificial_intelligence', 'data_science',
            'web_development', 'mobile_development', 'cloud_computing',
            'business_strategy', 'marketing', 'sales', 'finance',
            'project_management', 'requirements', 'design', 'architecture'
        ]
        
        try:
            embeddings = self.encoder.encode(common_tags)
            for tag, embedding in zip(common_tags, embeddings):
                self.tag_embeddings[tag] = embedding
            
            logger.info(f"Built embeddings for {len(common_tags)} common tags")
            
        except Exception as e:
            logger.error(f"Error building tag embeddings: {e}")

    def generate_semantic_tags(self, content: str, title: str = "", 
                             max_tags: int = 10, min_confidence: float = 0.3) -> List[TagSuggestion]:
        """Generate semantic tags using content similarity."""
        try:
            if not content:
                return []
            
            # Create content embedding
            text_for_embedding = f"{title} {content[:1000]}"  # First 1000 chars + title
            content_embedding = self.encoder.encode([text_for_embedding])[0]
            
            # Calculate similarities with pre-computed tag embeddings
            suggestions = []
            
            for tag, tag_embedding in self.tag_embeddings.items():
                similarity = util.cos_sim(content_embedding, tag_embedding).item()
                
                if similarity >= min_confidence:
                    # Generate reasoning
                    reasoning = self._generate_semantic_reasoning(tag, similarity, content)
                    
                    # Find similar tags
                    similar_tags = self._find_similar_tags(tag, similarity_threshold=0.7)
                    
                    suggestion = TagSuggestion(
                        tag=tag,
                        confidence=similarity,
                        reasoning=reasoning,
                        similar_tags=similar_tags,
                        auto_apply=similarity > 0.6  # Auto-apply high confidence tags
                    )
                    suggestions.append(suggestion)
            
            # Sort by confidence and return top suggestions
            suggestions.sort(key=lambda x: x.confidence, reverse=True)
            return suggestions[:max_tags]
            
        except Exception as e:
            logger.error(f"Semantic tagging error: {e}")
            return []

    def _generate_semantic_reasoning(self, tag: str, similarity: float, content: str) -> str:
        """Generate reasoning for semantic tag suggestion."""
        confidence_level = "high" if similarity > 0.6 else "moderate" if similarity > 0.4 else "low"
        
        # Look for explicit mentions
        if tag.replace('_', ' ') in content.lower():
            return f"{confidence_level.capitalize()} confidence - explicit mention of '{tag}' found in content"
        
        # Look for related terms
        related_terms = self._extract_related_terms(tag, content)
        if related_terms:
            terms_text = ", ".join(related_terms[:3])
            return f"{confidence_level.capitalize()} confidence - semantic similarity based on: {terms_text}"
        
        return f"{confidence_level.capitalize()} confidence - semantic similarity to content"

    def _extract_related_terms(self, tag: str, content: str) -> List[str]:
        """Extract terms related to the tag from content."""
        # Simple keyword extraction based on tag
        tag_keywords = {
            'api': ['endpoint', 'rest', 'http', 'json', 'request', 'response'],
            'frontend': ['ui', 'interface', 'react', 'vue', 'angular', 'html', 'css'],
            'backend': ['server', 'database', 'service', 'logic', 'processing'],
            'database': ['sql', 'query', 'table', 'data', 'storage', 'record'],
            'security': ['auth', 'authentication', 'encryption', 'password', 'secure'],
            'testing': ['test', 'unit', 'integration', 'qa', 'validation', 'verify'],
            'machine_learning': ['model', 'algorithm', 'training', 'prediction', 'dataset']
        }
        
        keywords = tag_keywords.get(tag, [])
        found_terms = []
        
        content_lower = content.lower()
        for keyword in keywords:
            if keyword in content_lower:
                found_terms.append(keyword)
        
        return found_terms

    def _find_similar_tags(self, tag: str, similarity_threshold: float = 0.7) -> List[str]:
        """Find tags similar to the given tag."""
        if tag not in self.tag_embeddings:
            return []
        
        tag_embedding = self.tag_embeddings[tag]
        similar_tags = []
        
        for other_tag, other_embedding in self.tag_embeddings.items():
            if other_tag != tag:
                similarity = util.cos_sim(tag_embedding, other_embedding).item()
                if similarity >= similarity_threshold:
                    similar_tags.append(other_tag)
        
        return similar_tags[:5]

    def cluster_content_tags(self, documents: List[Dict], num_clusters: int = 5) -> Dict[int, List[str]]:
        """Cluster documents and generate cluster-based tags."""
        try:
            if len(documents) < 2:
                return {}
            
            # Create embeddings for all documents
            texts = []
            doc_ids = []
            
            for doc in documents:
                text = f"{doc.get('title', '')} {doc.get('content', '')[:500]}"
                texts.append(text)
                doc_ids.append(doc.get('doc_id', ''))
            
            embeddings = self.encoder.encode(texts)
            
            # Perform clustering
            actual_clusters = min(num_clusters, len(documents) // 2)
            if actual_clusters < 2:
                return {}
            
            kmeans = KMeans(n_clusters=actual_clusters, random_state=42, n_init=10)
            cluster_labels = kmeans.fit_predict(embeddings)
            
            # Generate tags for each cluster
            cluster_tags = {}
            for cluster_id in range(actual_clusters):
                cluster_docs = [texts[i] for i, label in enumerate(cluster_labels) if label == cluster_id]
                cluster_keywords = self._extract_cluster_keywords(cluster_docs)
                cluster_tags[cluster_id] = cluster_keywords
            
            return cluster_tags
            
        except Exception as e:
            logger.error(f"Content clustering error: {e}")
            return {}

    def _extract_cluster_keywords(self, texts: List[str], max_keywords: int = 5) -> List[str]:
        """Extract representative keywords for a cluster."""
        try:
            if not texts:
                return []
            
            # Use TF-IDF to find distinctive terms
            vectorizer = TfidfVectorizer(
                max_features=50,
                stop_words='english',
                ngram_range=(1, 2)
            )
            
            tfidf_matrix = vectorizer.fit_transform(texts)
            feature_names = vectorizer.get_feature_names_out()
            
            # Get average TF-IDF scores
            mean_scores = np.mean(tfidf_matrix.toarray(), axis=0)
            
            # Get top keywords
            top_indices = mean_scores.argsort()[-max_keywords:][::-1]
            keywords = [feature_names[i] for i in top_indices]
            
            return keywords
            
        except Exception as e:
            logger.warning(f"Cluster keyword extraction error: {e}")
            return []

class RuleBasedTagger:
    """Rule-based tagging using patterns and heuristics."""
    
    def __init__(self):
        self.rules = self._build_tagging_rules()

    def _build_tagging_rules(self) -> List[Dict[str, Any]]:
        """Build rule-based tagging patterns."""
        return [
            {
                'tag': 'api_documentation',
                'patterns': [r'\b(api|endpoint|rest|http)\b', r'\b(get|post|put|delete)\b'],
                'keywords': ['api', 'endpoint', 'rest', 'http', 'json', 'request', 'response'],
                'min_matches': 2,
                'confidence': 0.8
            },
            {
                'tag': 'database_design',
                'patterns': [r'\b(table|schema|database|sql)\b', r'\b(primary key|foreign key)\b'],
                'keywords': ['database', 'table', 'schema', 'sql', 'query', 'index'],
                'min_matches': 2,
                'confidence': 0.9
            },
            {
                'tag': 'security_guide',
                'patterns': [r'\b(security|auth|encryption|password)\b', r'\b(vulnerability|threat)\b'],
                'keywords': ['security', 'authentication', 'encryption', 'password', 'vulnerability'],
                'min_matches': 2,
                'confidence': 0.8
            },
            {
                'tag': 'tutorial',
                'patterns': [r'\b(tutorial|guide|how to|step)\b', r'^\s*\d+\.', r'^\s*step\s+\d+'],
                'keywords': ['tutorial', 'guide', 'how', 'step', 'instruction', 'example'],
                'min_matches': 1,
                'confidence': 0.7
            },
            {
                'tag': 'troubleshooting',
                'patterns': [r'\b(error|problem|issue|fix|solve)\b', r'\b(troubleshoot|debug)\b'],
                'keywords': ['error', 'problem', 'issue', 'fix', 'solve', 'troubleshoot', 'debug'],
                'min_matches': 2,
                'confidence': 0.8
            },
            {
                'tag': 'configuration',
                'patterns': [r'\b(config|configuration|setup|install)\b', r'\.(json|yaml|xml|ini)\b'],
                'keywords': ['config', 'configuration', 'setup', 'install', 'settings'],
                'min_matches': 1,
                'confidence': 0.7
            },
            {
                'tag': 'requirements',
                'patterns': [r'\b(requirements|specification|spec)\b', r'\b(shall|must|should)\b'],
                'keywords': ['requirements', 'specification', 'must', 'should', 'shall'],
                'min_matches': 2,
                'confidence': 0.8
            },
            {
                'tag': 'testing',
                'patterns': [r'\b(test|testing|qa|quality)\b', r'\b(unit test|integration test)\b'],
                'keywords': ['test', 'testing', 'qa', 'quality', 'validation', 'verify'],
                'min_matches': 2,
                'confidence': 0.8
            }
        ]

    def apply_rules(self, content: str, title: str = "") -> List[TagSuggestion]:
        """Apply rule-based tagging to content."""
        suggestions = []
        text = f"{title} {content}".lower()
        
        for rule in self.rules:
            matches = 0
            matched_elements = []
            
            # Check patterns
            for pattern in rule['patterns']:
                if re.search(pattern, text, re.IGNORECASE | re.MULTILINE):
                    matches += 1
                    matched_elements.append(f"pattern: {pattern}")
            
            # Check keywords
            keyword_matches = sum(1 for keyword in rule['keywords'] if keyword in text)
            if keyword_matches >= rule.get('keyword_threshold', 1):
                matches += 1
                matched_elements.append(f"keywords: {keyword_matches} matches")
            
            # If sufficient matches, suggest tag
            if matches >= rule['min_matches']:
                reasoning = f"Rule-based match - {'; '.join(matched_elements)}"
                
                suggestion = TagSuggestion(
                    tag=rule['tag'],
                    confidence=rule['confidence'],
                    reasoning=reasoning,
                    similar_tags=[],
                    auto_apply=rule['confidence'] > 0.8
                )
                suggestions.append(suggestion)
        
        return suggestions

class IntelligentTaggingSystem:
    """Main intelligent tagging system combining multiple approaches."""
    
    def __init__(self):
        self.rag_system = get_rag_system()
        self.doc_manager = DocumentManager()
        self.analytics_engine = get_analytics_engine()
        self.cache = get_document_cache()
        
        # Initialize components
        self.taxonomy = TagTaxonomy()
        self.semantic_tagger = SemanticTagger()
        self.rule_tagger = RuleBasedTagger()
        
        # ML models for tag prediction
        self.ml_models = {}
        self.vectorizer = None
        self.model_trained = False
        
        # Tag statistics
        self.tag_stats = defaultdict(int)
        self.tag_cooccurrence = defaultdict(lambda: defaultdict(int))

    async def tag_document(self, doc_id: str, force_refresh: bool = False) -> Optional[DocumentTags]:
        """Generate comprehensive tags for a document."""
        try:
            # Check cache
            cache_key = f"doc_tags_{doc_id}"
            if not force_refresh:
                cached_result = self.cache.get(cache_key)
                if cached_result:
                    return DocumentTags(**cached_result)
            
            # Get document data
            doc_metadata = self.doc_manager.get_document(doc_id)
            if not doc_metadata:
                return None
            
            # Get document content
            results = self.rag_system.collection.get(
                where={"doc_id": doc_id},
                include=["documents"]
            )
            
            if not results or not results['documents']:
                return None
            
            content = ' '.join(results['documents'])
            
            # Generate tags using multiple approaches
            all_suggestions = []
            
            # 1. Semantic tagging
            semantic_suggestions = self.semantic_tagger.generate_semantic_tags(
                content, doc_metadata.title, max_tags=15
            )
            all_suggestions.extend(semantic_suggestions)
            
            # 2. Rule-based tagging
            rule_suggestions = self.rule_tagger.apply_rules(content, doc_metadata.title)
            all_suggestions.extend(rule_suggestions)
            
            # 3. ML-based tagging (if model is trained)
            if self.model_trained:
                ml_suggestions = await self._ml_tag_prediction(content, doc_metadata.title)
                all_suggestions.extend(ml_suggestions)
            
            # 4. Content analysis based tags
            analytics_tags = await self._generate_analytics_tags(doc_id, content)
            all_suggestions.extend(analytics_tags)
            
            # Consolidate and rank suggestions
            consolidated_suggestions = self._consolidate_suggestions(all_suggestions)
            
            # Apply taxonomy validation
            validated_tags = self._apply_taxonomy_validation(consolidated_suggestions)
            
            # Generate final tags and hierarchy
            final_tags = self._create_final_tags(validated_tags)
            hierarchy = self._build_tag_hierarchy(final_tags)
            
            # Find semantic clusters
            semantic_clusters = await self._find_semantic_clusters(doc_id, content)
            
            # Create document tags object
            doc_tags = DocumentTags(
                doc_id=doc_id,
                tags=final_tags,
                suggested_tags=consolidated_suggestions,
                hierarchy=hierarchy,
                semantic_clusters=semantic_clusters,
                generated_at=datetime.now(),
                model_version="1.0"
            )
            
            # Update statistics
            self._update_tag_statistics(final_tags)
            
            # Cache result
            self.cache.put(cache_key, asdict(doc_tags), ttl=3600)  # 1 hour TTL
            
            return doc_tags
            
        except Exception as e:
            logger.error(f"Document tagging error for {doc_id}: {e}")
            return None

    def _consolidate_suggestions(self, suggestions: List[TagSuggestion]) -> List[TagSuggestion]:
        """Consolidate duplicate tag suggestions from different sources."""
        tag_groups = defaultdict(list)
        
        # Group suggestions by normalized tag name
        for suggestion in suggestions:
            normalized_tag = self.taxonomy.normalize_tag(suggestion.tag)
            tag_groups[normalized_tag].append(suggestion)
        
        consolidated = []
        
        for normalized_tag, group in tag_groups.items():
            if not group:
                continue
            
            # Combine confidences and reasoning
            max_confidence = max(s.confidence for s in group)
            combined_reasoning = "; ".join(set(s.reasoning for s in group))
            
            # Collect all similar tags
            all_similar = []
            for s in group:
                all_similar.extend(s.similar_tags)
            unique_similar = list(set(all_similar))
            
            # Auto-apply if any source recommends it
            auto_apply = any(s.auto_apply for s in group)
            
            consolidated_suggestion = TagSuggestion(
                tag=normalized_tag,
                confidence=max_confidence,
                reasoning=combined_reasoning,
                similar_tags=unique_similar,
                auto_apply=auto_apply
            )
            consolidated.append(consolidated_suggestion)
        
        # Sort by confidence
        consolidated.sort(key=lambda x: x.confidence, reverse=True)
        return consolidated

    def _apply_taxonomy_validation(self, suggestions: List[TagSuggestion]) -> List[TagSuggestion]:
        """Apply taxonomy validation and conflict resolution."""
        validated = []
        selected_tags = []
        
        for suggestion in suggestions:
            # Check for conflicts with already selected tags
            valid_combination = self.taxonomy.validate_tag_combination(
                selected_tags + [suggestion.tag]
            )
            
            if suggestion.tag in valid_combination:
                validated.append(suggestion)
                selected_tags.append(suggestion.tag)
        
        return validated

    def _create_final_tags(self, suggestions: List[TagSuggestion], 
                          min_confidence: float = 0.3, max_tags: int = 15) -> List[Tag]:
        """Create final tag objects from suggestions."""
        final_tags = []
        
        for suggestion in suggestions:
            if suggestion.confidence >= min_confidence and len(final_tags) < max_tags:
                # Determine source
                if 'semantic' in suggestion.reasoning.lower():
                    source = 'ml_semantic'
                elif 'rule' in suggestion.reasoning.lower():
                    source = 'rule_based'
                else:
                    source = 'ml_auto'
                
                # Get hierarchy info
                hierarchy = self.taxonomy.get_tag_hierarchy(suggestion.tag)
                category = hierarchy[0] if hierarchy else 'general'
                
                # Get related terms
                related_terms = self.taxonomy.suggest_related_tags(suggestion.tag)
                
                tag = Tag(
                    name=suggestion.tag,
                    category=category,
                    confidence=suggestion.confidence,
                    source=source,
                    context=suggestion.reasoning,
                    related_terms=related_terms,
                    created_at=datetime.now()
                )
                final_tags.append(tag)
        
        return final_tags

    def _build_tag_hierarchy(self, tags: List[Tag]) -> Dict[str, List[str]]:
        """Build hierarchical organization of tags."""
        hierarchy = defaultdict(list)
        
        for tag in tags:
            hierarchy[tag.category].append(tag.name)
        
        return dict(hierarchy)

    async def _generate_analytics_tags(self, doc_id: str, content: str) -> List[TagSuggestion]:
        """Generate tags based on document analytics."""
        try:
            # Get document analytics
            doc_insight = await self.analytics_engine.analyze_document(doc_id)
            if not doc_insight:
                return []
            
            suggestions = []
            
            # Tags based on complexity
            if doc_insight.complexity_score > 0.7:
                suggestions.append(TagSuggestion(
                    tag='complex_content',
                    confidence=0.8,
                    reasoning=f'High complexity score: {doc_insight.complexity_score:.2f}',
                    similar_tags=['advanced', 'detailed'],
                    auto_apply=True
                ))
            elif doc_insight.complexity_score < 0.3:
                suggestions.append(TagSuggestion(
                    tag='simple_content',
                    confidence=0.7,
                    reasoning=f'Low complexity score: {doc_insight.complexity_score:.2f}',
                    similar_tags=['basic', 'introductory'],
                    auto_apply=True
                ))
            
            # Tags based on readability
            if doc_insight.readability_score > 0.8:
                suggestions.append(TagSuggestion(
                    tag='easy_to_read',
                    confidence=0.7,
                    reasoning=f'High readability score: {doc_insight.readability_score:.2f}',
                    similar_tags=['accessible', 'clear'],
                    auto_apply=False
                ))
            
            # Tags based on sentiment
            if doc_insight.sentiment_score > 0.3:
                suggestions.append(TagSuggestion(
                    tag='positive_content',
                    confidence=0.6,
                    reasoning=f'Positive sentiment: {doc_insight.sentiment_score:.2f}',
                    similar_tags=['optimistic', 'encouraging'],
                    auto_apply=False
                ))
            elif doc_insight.sentiment_score < -0.3:
                suggestions.append(TagSuggestion(
                    tag='critical_content',
                    confidence=0.6,
                    reasoning=f'Negative sentiment: {doc_insight.sentiment_score:.2f}',
                    similar_tags=['problem_focused', 'issues'],
                    auto_apply=False
                ))
            
            # Tags based on key topics
            for topic in doc_insight.key_topics[:3]:
                if topic:
                    suggestions.append(TagSuggestion(
                        tag=topic.replace(' ', '_'),
                        confidence=0.5,
                        reasoning=f'Key topic identified: {topic}',
                        similar_tags=[],
                        auto_apply=False
                    ))
            
            return suggestions
            
        except Exception as e:
            logger.warning(f"Analytics tagging error: {e}")
            return []

    async def _find_semantic_clusters(self, doc_id: str, content: str) -> List[str]:
        """Find semantic clusters for the document."""
        try:
            # Get related documents
            related_docs = await self._get_related_documents(doc_id, max_related=10)
            
            if len(related_docs) < 2:
                return []
            
            # Include current document
            all_docs = [{'doc_id': doc_id, 'content': content}] + related_docs
            
            # Cluster documents
            clusters = self.semantic_tagger.cluster_content_tags(all_docs, num_clusters=3)
            
            # Find which cluster contains the current document
            for cluster_id, keywords in clusters.items():
                # Simple heuristic: if content contains cluster keywords
                content_lower = content.lower()
                if any(keyword.lower() in content_lower for keyword in keywords):
                    return keywords
            
            return []
            
        except Exception as e:
            logger.warning(f"Semantic clustering error: {e}")
            return []

    async def _get_related_documents(self, doc_id: str, max_related: int = 10) -> List[Dict]:
        """Get related documents for clustering."""
        try:
            # Get document content for similarity search
            results = self.rag_system.collection.get(
                where={"doc_id": doc_id},
                include=["documents"]
            )
            
            if not results or not results['documents']:
                return []
            
            content = ' '.join(results['documents'])
            query = content[:500]  # Use first part as query
            
            # Find similar documents
            similar_docs = self.rag_system.adaptive_retrieval(query, max_chunks=max_related * 2)
            
            # Group by document and exclude current doc
            doc_contents = {}
            for doc in similar_docs:
                related_id = doc.get('doc_id')
                if related_id and related_id != doc_id:
                    if related_id not in doc_contents:
                        doc_contents[related_id] = []
                    doc_contents[related_id].append(doc.get('content', ''))
            
            # Create document objects
            related_docs = []
            for related_id, contents in doc_contents.items():
                related_docs.append({
                    'doc_id': related_id,
                    'content': ' '.join(contents)
                })
                
                if len(related_docs) >= max_related:
                    break
            
            return related_docs
            
        except Exception as e:
            logger.warning(f"Error getting related documents: {e}")
            return []

    async def _ml_tag_prediction(self, content: str, title: str) -> List[TagSuggestion]:
        """Predict tags using trained ML models (placeholder for future enhancement)."""
        # This is a placeholder for ML-based tag prediction
        # In a full implementation, this would use trained models
        return []

    def _update_tag_statistics(self, tags: List[Tag]):
        """Update tag usage statistics."""
        tag_names = [tag.name for tag in tags]
        
        # Update individual tag counts
        for tag_name in tag_names:
            self.tag_stats[tag_name] += 1
        
        # Update co-occurrence statistics
        for i, tag1 in enumerate(tag_names):
            for tag2 in tag_names[i+1:]:
                self.tag_cooccurrence[tag1][tag2] += 1
                self.tag_cooccurrence[tag2][tag1] += 1

    async def get_tag_suggestions_for_query(self, query: str) -> List[str]:
        """Get tag suggestions for a search query."""
        try:
            # Use semantic similarity to suggest relevant tags
            suggestions = self.semantic_tagger.generate_semantic_tags(
                query, max_tags=10, min_confidence=0.2
            )
            
            # Extract tag names
            tag_names = [s.tag for s in suggestions]
            
            # Add popular tags that might be relevant
            popular_tags = sorted(self.tag_stats.items(), key=lambda x: x[1], reverse=True)[:20]
            for tag, count in popular_tags:
                if tag not in tag_names and any(word in query.lower() for word in tag.split('_')):
                    tag_names.append(tag)
            
            return tag_names[:10]
            
        except Exception as e:
            logger.error(f"Tag suggestion error: {e}")
            return []

    async def get_popular_tags(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Get most popular tags across the collection."""
        try:
            popular = []
            for tag, count in sorted(self.tag_stats.items(), key=lambda x: x[1], reverse=True)[:limit]:
                # Get tag hierarchy
                hierarchy = self.taxonomy.get_tag_hierarchy(tag)
                category = hierarchy[0] if hierarchy else 'general'
                
                popular.append({
                    'tag': tag,
                    'count': count,
                    'category': category,
                    'related_tags': self.taxonomy.suggest_related_tags(tag, max_suggestions=3)
                })
            
            return popular
            
        except Exception as e:
            logger.error(f"Popular tags error: {e}")
            return []

    async def get_tag_trends(self, time_period: str = 'month') -> List[Dict[str, Any]]:
        """Get trending tags over a time period."""
        # This would require storing tag creation timestamps
        # For now, return most popular tags as trends
        return await self.get_popular_tags(limit=10)

# Global instance
_tagging_system_instance = None

def get_tagging_system() -> IntelligentTaggingSystem:
    """Get global tagging system instance."""
    global _tagging_system_instance
    if _tagging_system_instance is None:
        _tagging_system_instance = IntelligentTaggingSystem()
    return _tagging_system_instance