import re
import json
import os
import uuid
from typing import Dict, List, Any, Optional, Tuple, Set

class Entity:
    def __init__(self, entity_id: str, entity_type: str, name: str, properties: Dict[str, Any] = None, confidence: float = 1.0):
        self.id = entity_id
        self.type = entity_type
        self.name = name
        self.properties = properties or {}
        self.confidence = confidence
    
    def to_dict(self):
        return {
            "id": self.id,
            "type": self.type,
            "name": self.name,
            "properties": self.properties,
            "confidence": self.confidence
        }
    
    @classmethod
    def from_dict(cls, data):
        return cls(
            entity_id=data["id"],
            entity_type=data["type"],
            name=data["name"],
            properties=data.get("properties", {}),
            confidence=data.get("confidence", 1.0)
        )

class Relationship:
    def __init__(self, rel_id: str, rel_type: str, source: str, target: str, properties: Dict[str, Any] = None, confidence: float = 1.0):
        self.id = rel_id
        self.type = rel_type
        self.source = source
        self.target = target
        self.properties = properties or {}
        self.confidence = confidence
    
    def to_dict(self):
        return {
            "id": self.id,
            "type": self.type,
            "source": self.source,
            "target": self.target,
            "properties": self.properties,
            "confidence": self.confidence
        }
    
    @classmethod
    def from_dict(cls, data):
        return cls(
            rel_id=data["id"],
            rel_type=data["type"],
            source=data["source"],
            target=data["target"],
            properties=data.get("properties", {}),
            confidence=data.get("confidence", 1.0)
        )

class TextChunk:
    def __init__(self, chunk_id: str, text: str, metadata: Dict[str, Any] = None, similarity: float = 0.0):
        self.id = chunk_id
        self.text = text
        self.metadata = metadata or {}
        self.similarity = similarity
    
    def to_dict(self):
        return {
            "id": self.id,
            "text": self.text,
            "metadata": self.metadata,
            "similarity": self.similarity
        }
    
    @classmethod
    def from_dict(cls, data):
        return cls(
            chunk_id=data["id"],
            text=data["text"],
            metadata=data.get("metadata", {}),
            similarity=data.get("similarity", 0.0)
        )

class KnowledgeGraph:
    def __init__(self):
        self.entities = []
        self.relationships = []
        self.text_chunks = []
        self.entity_map = {}  # For quick lookup by ID
    
    def add_entity(self, entity_type: str, name: str, properties: Dict[str, Any] = None, confidence: float = 1.0) -> str:
        entity_id = f"entity-{str(uuid.uuid4())[:8]}"
        entity = Entity(entity_id, entity_type, name, properties, confidence)
        self.entities.append(entity)
        self.entity_map[entity_id] = entity
        return entity_id
    
    def add_relationship(self, rel_type: str, source: str, target: str, properties: Dict[str, Any] = None, confidence: float = 1.0) -> str:
        rel_id = f"rel-{str(uuid.uuid4())[:8]}"
        relationship = Relationship(rel_id, rel_type, source, target, properties, confidence)
        self.relationships.append(relationship)
        return rel_id
    
    def add_text_chunk(self, text: str, metadata: Dict[str, Any] = None) -> str:
        chunk_id = f"chunk-{str(uuid.uuid4())[:8]}"
        chunk = TextChunk(chunk_id, text, metadata)
        self.text_chunks.append(chunk)
        return chunk_id
    
    def get_entity(self, entity_id: str) -> Optional[Entity]:
        return self.entity_map.get(entity_id)
    
    def get_entities_by_type(self, entity_type: str) -> List[Entity]:
        return [e for e in self.entities if e.type == entity_type]
    
    def get_relationships_for_entity(self, entity_id: str) -> List[Relationship]:
        return [r for r in self.relationships if r.source == entity_id or r.target == entity_id]
    
    def clear(self):
        """Clear all data from the knowledge graph"""
        self.entities = []
        self.relationships = []
        self.text_chunks = []
        self.entity_map = {}
    
    def save(self, filename: str):
        """Save the knowledge graph to a file"""
        data = {
            "entities": [e.to_dict() for e in self.entities],
            "relationships": [r.to_dict() for r in self.relationships],
            "text_chunks": [c.to_dict() for c in self.text_chunks]
        }
        
        os.makedirs(os.path.dirname(os.path.abspath(filename)), exist_ok=True)
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2)
    
    def load(self, filename: str) -> bool:
        """Load the knowledge graph from a file"""
        if not os.path.exists(filename):
            return False
            
        with open(filename, 'r') as f:
            data = json.load(f)
        
        self.clear()
        self.entities = [Entity.from_dict(e) for e in data.get("entities", [])]
        self.relationships = [Relationship.from_dict(r) for r in data.get("relationships", [])]
        self.text_chunks = [TextChunk.from_dict(c) for c in data.get("text_chunks", [])]
        
        # Rebuild entity map
        self.entity_map = {e.id: e for e in self.entities}
        
        return True
    
    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about the knowledge graph"""
        entity_types = {}
        for entity in self.entities:
            entity_types[entity.type] = entity_types.get(entity.type, 0) + 1
        
        relationship_types = {}
        for rel in self.relationships:
            relationship_types[rel.type] = relationship_types.get(rel.type, 0) + 1
        
        return {
            "entity_count": len(self.entities),
            "relationship_count": len(self.relationships),
            "text_chunk_count": len(self.text_chunks),
            "entity_types": entity_types,
            "relationship_types": relationship_types
        }

