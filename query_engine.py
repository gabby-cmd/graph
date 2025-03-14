from typing import Dict, List, Any, Tuple, Optional
from knowledge_graph import KnowledgeGraph, Entity, Relationship, TextChunk

class QueryEngine:
    def __init__(self, knowledge_graph: KnowledgeGraph):
        self.kg = knowledge_graph
    
    def query(self, query_text: str) -> Dict[str, Any]:
        """Query the knowledge graph for relevant information"""
        # Find relevant entities
        relevant_entities = self._find_relevant_entities(query_text)
        
        # Find relevant relationships
        relevant_relationships = self._find_relevant_relationships(relevant_entities)
        
        # Find relevant text chunks
        relevant_chunks = self._find_relevant_text_chunks(query_text)
        
        # Generate answer
        answer = self._generate_answer(query_text, relevant_entities, relevant_relationships, relevant_chunks)
        
        return {
            "answer": answer,
            "entities": [e.to_dict() for e in relevant_entities],
            "relationships": [r.to_dict() for r in relevant_relationships],
            "chunks": [c.to_dict() for c in relevant_chunks]
        }
    
    def _find_relevant_entities(self, query_text: str) -> List[Entity]:
        """Find entities relevant to the query"""
        relevant_entities = []
        keywords = [kw.lower() for kw in query_text.split() if len(kw) > 3]
        
        for entity in self.kg.entities:
            # Check entity name
            if any(keyword in entity.name.lower() for keyword in keywords):
                relevant_entities.append(entity)
                continue
            
            # Check entity properties
            for prop_value in entity.properties.values():
                if isinstance(prop_value, str) and any(keyword in prop_value.lower() for keyword in keywords):
                    relevant_entities.append(entity)
                    break
        
        return relevant_entities
    
    def _find_relevant_relationships(self, relevant_entities: List[Entity]) -> List[Relationship]:
        """Find relationships involving the relevant entities"""
        entity_ids = {entity.id for entity in relevant_entities}
        return [rel for rel in self.kg.relationships if rel.source in entity_ids or rel.target in entity_ids]
    
    def _find_relevant_text_chunks(self, query_text: str) -> List[TextChunk]:
        """Find text chunks relevant to the query"""
        keywords = [kw.lower() for kw in query_text.split() if len(kw) > 3]
        
        scored_chunks = []
        for chunk in self.kg.text_chunks:
            # Simple relevance scoring based on keyword matches
            text_lower = chunk.text.lower()
            matches = sum(1 for keyword in keywords if keyword in text_lower)
            if matches > 0:
                similarity = matches / len(keywords)
                chunk.similarity = similarity
                scored_chunks.append(chunk)
        
        # Sort by relevance
        scored_chunks.sort(key=lambda x: x.similarity, reverse=True)
        
        # Return top chunks
        return scored_chunks[:5]
    
    def _generate_answer(self, query: str, entities: List[Entity], relationships: List[Relationship], chunks: List[TextChunk]) -> str:
        """Generate an answer based on the query and relevant information"""
        query_lower = query.lower()
        
        # Check for specific banking policy questions
        if "credit score" in query_lower:
            for entity in entities:
                if entity.type == "Threshold" and "700" in entity.name:
                    return "According to the Bank Loan Approval Policy, customers must have a minimum credit score of 700 to qualify for a loan."
            return "Based on the bank's loan policies, a minimum credit score is required for loan approval, but I couldn't find the exact threshold in the provided information."
        
        if "data deletion" in query_lower or "deletion request" in query_lower:
            for entity in entities:
                if entity.type == "TimePeriod" and "30 day" in entity.name.lower():
                    return "According to the Bank Customer Data Protection Policy, customer requests for data deletion must be processed within 30 days."
            return "The Bank Customer Data Protection Policy requires timely processing of data deletion requests, but I couldn't find the exact timeframe in the provided information."
        
        if "transaction" in query_lower and ("verification" in query_lower or "verify" in query_lower):
            for entity in entities:
                if entity.type == "Threshold" and "$10,000" in entity.name:
                    return "According to the Bank Fraud Prevention Policy, transactions above $10,000 require additional verification."
            return "The Bank Fraud Prevention Policy requires additional verification for transactions above certain thresholds, but I couldn't find the exact amount in the provided information."
        
        # If we have relevant text chunks, use them to generate an answer
        if chunks:
            most_relevant_chunk = chunks[0]
            
            # If the chunk has high similarity, use it directly
            if most_relevant_chunk.similarity > 0.5:
                return f"Based on the available information: {most_relevant_chunk.text}"
            
            # Otherwise, combine information from multiple chunks
            if len(chunks) >= 2:
                combined_info = "\n".join([c.text for c in chunks[:2]])
                return f"Based on the available information:\n\n{combined_info}"
        
        # If we have entities but no specific match
        if entities:
            entity_info = "\n".join([f"- {e.name} ({e.type})" for e in entities[:5]])
            return f"Based on your query, I found these relevant items in the knowledge base:\n\n{entity_info}\n\nFor more specific information, please try refining your question."
        
        # Default response
        return "I don't have enough information to answer that specific question. Please try asking about credit scores, loan approvals, data deletion, transaction verification, or fraud prevention."
    
    def get_example_questions(self) -> List[str]:
        """Get example questions based on the current knowledge graph"""
        questions = []
        
        # Check for specific entity types and generate relevant questions
        if any(e.type == "Policy" for e in self.kg.entities):
            questions.append("What are the main policies in the system?")
        
        if any(e.type == "Threshold" and "$10,000" in e.name for e in self.kg.entities):
            questions.append("What transactions require additional verification?")
        
        if any(e.type == "TimePeriod" and "30 day" in e.name for e in self.kg.entities):
            questions.append("How long do we have to process data deletion requests?")
        
        if any(e.type == "Threshold" and "700" in e.name for e in self.kg.entities):
            questions.append("What is the minimum credit score needed for a loan?")
        
        # Add some generic questions
        if len(questions) < 5:
            generic_questions = [
                "What are the requirements for large loans?",
                "How are customer data and fraud prevention related?",
                "What security measures are required for customer data?",
                "What happens when a transaction appears suspicious?",
                "How often are security audits conducted?"
            ]
            
            questions.extend(generic_questions[:5 - len(questions)])
        
        return questions

