"""
Layer 2: Clustering/Deduplication - Group Similar Headlines
Memphis Civic Market - July 28, 2025

This module clusters similar headlines to avoid duplicate contracts.
Only one contract per cluster per day is generated.
"""

import hashlib
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set, Tuple
from dataclasses import dataclass
from collections import defaultdict
import re

@dataclass
class HeadlineCluster:
    """A cluster of similar headlines"""
    cluster_id: str
    primary_headline: str
    similar_headlines: List[str]
    topic_signature: str
    entity_signature: str
    last_contract_date: Optional[datetime]
    total_headlines: int

@dataclass
class ClusteringResult:
    """Result of clustering operation"""
    cluster_id: str
    is_primary: bool  # True if this headline should generate a contract
    similar_count: int
    reason: str
    processing_time_ms: float

class Layer2Clustering:
    """
    Clusters similar headlines to prevent duplicate contracts.
    Uses topic signatures and entity matching for grouping.
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Active clusters (in-memory for now, could be database-backed)
        self.active_clusters: Dict[str, HeadlineCluster] = {}
        
        # Contract generation tracking (one per cluster per day)
        self.daily_contract_tracking: Dict[str, datetime] = {}
        
        # Stop words for topic signature generation
        self.stop_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
            'of', 'with', 'by', 'from', 'up', 'about', 'into', 'through', 'during',
            'before', 'after', 'above', 'below', 'between', 'among', 'will', 'would',
            'could', 'should', 'may', 'might', 'can', 'must', 'shall', 'is', 'are',
            'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'do', 'does',
            'did', 'this', 'that', 'these', 'those', 'memphis', 'shelby', 'county'
        }
        
        # Key civic entities for entity signature
        self.civic_entities = {
            'council', 'commission', 'mayor', 'school', 'board', 'mata', 'mlgw',
            'police', 'fire', 'planning', 'zoning', 'housing', 'budget', 'vote',
            'election', 'development', 'transportation', 'water', 'sewer', 'park'
        }
    
    def generate_topic_signature(self, headline: str) -> str:
        """
        Generate a topic signature for clustering.
        Extracts key topic words while ignoring stop words.
        """
        # Normalize text
        text = headline.lower()
        text = re.sub(r'[^\w\s]', ' ', text)  # Remove punctuation
        words = text.split()
        
        # Filter stop words and extract meaningful terms
        topic_words = []
        for word in words:
            if len(word) > 2 and word not in self.stop_words:
                topic_words.append(word)
        
        # Sort and join to create consistent signature
        topic_words.sort()
        return '_'.join(topic_words[:5])  # Limit to top 5 words
    
    def generate_entity_signature(self, headline: str, entity_tags: List[str] = None) -> str:
        """
        Generate an entity signature based on civic entities mentioned.
        """
        text = headline.lower()
        
        # Extract civic entities from headline
        found_entities = set()
        for entity in self.civic_entities:
            if entity in text:
                found_entities.add(entity)
        
        # Add entity tags if provided
        if entity_tags:
            for tag in entity_tags:
                tag_lower = tag.lower()
                if tag_lower in self.civic_entities:
                    found_entities.add(tag_lower)
        
        # Sort and join to create consistent signature
        entity_list = sorted(list(found_entities))
        return '_'.join(entity_list) if entity_list else 'general_civic'
    
    def calculate_similarity_score(self, headline1: str, headline2: str) -> float:
        """
        Calculate similarity score between two headlines.
        Returns 0.0-1.0 where 1.0 is identical.
        """
        # Generate signatures for both headlines
        topic1 = self.generate_topic_signature(headline1)
        topic2 = self.generate_topic_signature(headline2)
        entity1 = self.generate_entity_signature(headline1)
        entity2 = self.generate_entity_signature(headline2)
        
        # Calculate topic similarity
        topic_words1 = set(topic1.split('_'))
        topic_words2 = set(topic2.split('_'))
        
        if not topic_words1 or not topic_words2:
            topic_similarity = 0.0
        else:
            intersection = len(topic_words1.intersection(topic_words2))
            union = len(topic_words1.union(topic_words2))
            topic_similarity = intersection / union if union > 0 else 0.0
        
        # Calculate entity similarity
        entity_words1 = set(entity1.split('_'))
        entity_words2 = set(entity2.split('_'))
        
        if not entity_words1 or not entity_words2:
            entity_similarity = 0.0
        else:
            intersection = len(entity_words1.intersection(entity_words2))
            union = len(entity_words1.union(entity_words2))
            entity_similarity = intersection / union if union > 0 else 0.0
        
        # Weighted average (topic 60%, entity 40%)
        overall_similarity = (topic_similarity * 0.6) + (entity_similarity * 0.4)
        return overall_similarity
    
    def find_or_create_cluster(self, headline: str, entity_tags: List[str] = None) -> ClusteringResult:
        """
        Find existing cluster for headline or create new one.
        
        Args:
            headline: The headline to cluster
            entity_tags: Optional entity tags from Layer 1 classification
            
        Returns:
            ClusteringResult with clustering decision
        """
        start_time = datetime.now()
        
        # Generate signatures for this headline
        topic_signature = self.generate_topic_signature(headline)
        entity_signature = self.generate_entity_signature(headline, entity_tags)
        
        # Look for existing similar clusters
        best_cluster_id = None
        best_similarity = 0.0
        similarity_threshold = 0.7  # 70% similarity required for clustering
        
        for cluster_id, cluster in self.active_clusters.items():
            similarity = self.calculate_similarity_score(headline, cluster.primary_headline)
            
            if similarity > similarity_threshold and similarity > best_similarity:
                best_cluster_id = cluster_id
                best_similarity = similarity
        
        # Determine if this headline should generate a contract
        is_primary = False
        cluster_id = None
        reason = ""
        
        if best_cluster_id:
            # Add to existing cluster
            cluster_id = best_cluster_id
            cluster = self.active_clusters[cluster_id]
            cluster.similar_headlines.append(headline)
            cluster.total_headlines += 1
            
            # Check if we can generate a contract (one per cluster per day)
            today = datetime.now().date()
            last_contract_date = cluster.last_contract_date
            
            if not last_contract_date or last_contract_date.date() < today:
                is_primary = True
                cluster.last_contract_date = datetime.now()
                reason = f"Primary headline for cluster (last contract: {last_contract_date.date() if last_contract_date else 'never'})"
            else:
                reason = f"Similar to existing cluster, contract already generated today"
            
        else:
            # Create new cluster
            cluster_id = hashlib.md5(f"{topic_signature}_{entity_signature}_{datetime.now().isoformat()}".encode()).hexdigest()[:12]
            
            new_cluster = HeadlineCluster(
                cluster_id=cluster_id,
                primary_headline=headline,
                similar_headlines=[],
                topic_signature=topic_signature,
                entity_signature=entity_signature,
                last_contract_date=datetime.now(),
                total_headlines=1
            )
            
            self.active_clusters[cluster_id] = new_cluster
            is_primary = True
            reason = "New cluster created, generating contract"
        
        # Calculate processing time
        end_time = datetime.now()
        processing_time_ms = (end_time - start_time).total_seconds() * 1000
        
        # Log result
        similar_count = len(self.active_clusters[cluster_id].similar_headlines) if cluster_id else 0
        self.logger.info(f"Layer 2 Clustering: {'PRIMARY' if is_primary else 'SIMILAR'} - {headline[:100]}... - Cluster: {cluster_id}")
        
        return ClusteringResult(
            cluster_id=cluster_id,
            is_primary=is_primary,
            similar_count=similar_count,
            reason=reason,
            processing_time_ms=processing_time_ms
        )
    
    def cleanup_old_clusters(self, days_to_keep: int = 7):
        """
        Clean up clusters older than specified days to prevent memory bloat.
        """
        cutoff_date = datetime.now() - timedelta(days=days_to_keep)
        
        clusters_to_remove = []
        for cluster_id, cluster in self.active_clusters.items():
            if cluster.last_contract_date and cluster.last_contract_date < cutoff_date:
                clusters_to_remove.append(cluster_id)
        
        for cluster_id in clusters_to_remove:
            del self.active_clusters[cluster_id]
        
        if clusters_to_remove:
            self.logger.info(f"Cleaned up {len(clusters_to_remove)} old clusters")
    
    def get_cluster_stats(self) -> Dict:
        """Get statistics about current clustering state."""
        total_clusters = len(self.active_clusters)
        total_headlines = sum(cluster.total_headlines for cluster in self.active_clusters.values())
        
        return {
            'total_clusters': total_clusters,
            'total_headlines': total_headlines,
            'avg_headlines_per_cluster': total_headlines / total_clusters if total_clusters > 0 else 0
        }
