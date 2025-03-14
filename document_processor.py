import re
import os
from typing import Dict, List, Any, Tuple, Optional
from knowledge_graph import KnowledgeGraph

class DocumentProcessor:
    def __init__(self, knowledge_graph: KnowledgeGraph):
        self.kg = knowledge_graph
    
    def process_document(self, text: str, document_name: str, document_type: str = "generic") -> Dict[str, Any]:
        """Process a document and extract entities and relationships"""
        if document_type == "banking_policy":
            return self._process_banking_policy(text, document_name)
        else:
            return self._process_generic_document(text, document_name)
    
    def _process_banking_policy(self, text: str, document_name: str) -> Dict[str, Any]:
        """Process a banking policy document"""
        # Determine policy type
        policy_type = "Bank Policy"
        if "loan" in document_name.lower():
            policy_type = "Loan Policy"
        elif "data" in document_name.lower() or "protection" in document_name.lower():
            policy_type = "Data Protection Policy"
        elif "fraud" in document_name.lower() or "prevention" in document_name.lower():
            policy_type = "Fraud Prevention Policy"
        
        # Create policy entity
        policy_id = self.kg.add_entity(
            entity_type="Policy",
            name=policy_type,
            properties={"filename": document_name},
            confidence=0.95
        )
        
        # Add text chunk for the full document
        self.kg.add_text_chunk(
            text=text,
            metadata={"source": document_name, "policy": policy_type}
        )
        
        # Extract requirements
        lines = text.split("\n")
        current_section = ""
        requirement_ids = []
        
        for line in lines:
            line = line.strip()
            
            # Check if this is a section header
            if line and not re.match(r'^\d+\.', line):
                current_section = line
                continue
            
            # Check for numbered requirements
            requirement_match = re.match(r'^(\d+)\.\s+(.*)', line)
            if requirement_match:
                req_number = requirement_match.group(1)
                req_text = requirement_match.group(2)
                
                # Create requirement entity
                req_id = self.kg.add_entity(
                    entity_type="Requirement",
                    name=f"Requirement {req_number}",
                    properties={
                        "text": req_text,
                        "section": current_section or policy_type
                    },
                    confidence=0.9
                )
                requirement_ids.append(req_id)
                
                # Add relationship between policy and requirement
                self.kg.add_relationship(
                    rel_type="HAS_REQUIREMENT",
                    source=policy_id,
                    target=req_id,
                    confidence=0.95
                )
                
                # Extract monetary values
                money_matches = re.findall(r'\$([0-9,]+)', req_text)
                for match in money_matches:
                    amount = match.replace(',', '')
                    threshold_id = self.kg.add_entity(
                        entity_type="Threshold",
                        name=f"${match} Threshold",
                        properties={
                            "amount": int(amount),
                            "text": req_text
                        },
                        confidence=0.85
                    )
                    
                    self.kg.add_relationship(
                        rel_type="MENTIONS",
                        source=req_id,
                        target=threshold_id,
                        confidence=0.8
                    )
                
                # Extract time periods
                time_matches = re.findall(r'(\d+)\s+(day|hour|minute|business day|week|month|year)s?', req_text, re.IGNORECASE)
                for match in time_matches:
                    time_period = f"{match[0]} {match[1]}"
                    time_id = self.kg.add_entity(
                        entity_type="TimePeriod",
                        name=time_period,
                        properties={"text": req_text},
                        confidence=0.85
                    )
                    
                    self.kg.add_relationship(
                        rel_type="SPECIFIES",
                        source=req_id,
                        target=time_id,
                        confidence=0.8
                    )
                
                # Extract percentages
                percent_matches = re.findall(r'(\d+)%', req_text)
                for match in percent_matches:
                    percent_id = self.kg.add_entity(
                        entity_type="Percentage",
                        name=f"{match}%",
                        properties={
                            "value": int(match),
                            "text": req_text
                        },
                        confidence=0.85
                    )
                    
                    self.kg.add_relationship(
                        rel_type="SPECIFIES",
                        source=req_id,
                        target=percent_id,
                        confidence=0.8
                    )
                
                # Extract roles/actors
                role_patterns = [
                    "customer", "employee", "officer", "team",
                    "Senior Loan Officer", "fraud detection team", "user"
                ]
                
                for role in role_patterns:
                    if role.lower() in req_text.lower():
                        role_id = self.kg.add_entity(
                            entity_type="Role",
                            name=role.capitalize(),
                            properties={"text": req_text},
                            confidence=0.85
                        )
                        
                        self.kg.add_relationship(
                            rel_type="INVOLVES",
                            source=req_id,
                            target=role_id,
                            confidence=0.8
                        )
        
        # Add relationships between policies if there are multiple
        policy_entities = self.kg.get_entities_by_type("Policy")
        if len(policy_entities) >= 2:
            # Find this policy
            this_policy = None
            for entity in policy_entities:
                if entity.id == policy_id:
                    this_policy = entity
                    break
            
            if this_policy:
                # Connect to other policies
                for other_policy in policy_entities:
                    if other_policy.id != this_policy.id:
                        self.kg.add_relationship(
                            rel_type="RELATED_TO",
                            source=this_policy.id,
                            target=other_policy.id,
                            properties={"reason": "Policy relationship"},
                            confidence=0.7
                        )
        
        return {
            "policy_id": policy_id,
            "requirement_ids": requirement_ids,
            "entity_count": len(self.kg.entities),
            "relationship_count": len(self.kg.relationships)
        }
    
    def _process_generic_document(self, text: str, document_name: str) -> Dict[str, Any]:
        """Process a generic document"""
        # Create document entity
        doc_id = self.kg.add_entity(
            entity_type="Document",
            name=document_name,
            properties={"content_length": len(text)},
            confidence=0.95
        )
        
        # Add text chunk for the full document
        self.kg.add_text_chunk(
            text=text,
            metadata={"source": document_name}
        )
        
        # Split into paragraphs
        paragraphs = re.split(r'\n\s*\n', text)
        
        # Process each paragraph
        for i, paragraph in enumerate(paragraphs):
            if not paragraph.strip():
                continue
                
            # Add as a text chunk
            self.kg.add_text_chunk(
                text=paragraph,
                metadata={"source": document_name, "paragraph": i}
            )
            
            # Extract potential entities using simple patterns
            
            # Dates
            date_matches = re.findall(r'\b(\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|\d{1,2} (Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]* \d{2,4})\b', paragraph)
            for match in date_matches:
                date_str = match[0]
                date_id = self.kg.add_entity(
                    entity_type="Date",
                    name=date_str,
                    properties={"context": paragraph[:100]},
                    confidence=0.8
                )
                
                self.kg.add_relationship(
                    rel_type="MENTIONED_IN",
                    source=date_id,
                    target=doc_id,
                    confidence=0.8
                )
            
            # Organizations (simple heuristic for capitalized multi-word phrases)
            org_matches = re.findall(r'\b([A-Z][a-z]+ [A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\b', paragraph)
            for match in org_matches:
                if len(match.split()) >= 2:  # At least two words
                    org_id = self.kg.add_entity(
                        entity_type="Organization",
                        name=match,
                        properties={"context": paragraph[:100]},
                        confidence=0.7
                    )
                    
                    self.kg.add_relationship(
                        rel_type="MENTIONED_IN",
                        source=org_id,
                        target=doc_id,
                        confidence=0.7
                    )
            
            # Numbers and quantities
            number_matches = re.findall(r'\b(\d+(?:,\d+)*(?:\.\d+)?)\s*(percent|%|dollars|USD|\$|euros|EUR|€)\b', paragraph, re.IGNORECASE)
            for match in number_matches:
                value = match[0].replace(',', '')
                unit = match[1].lower()
                
                if unit in ('percent', '%'):
                    entity_type = "Percentage"
                    name = f"{value}%"
                elif unit in ('dollars', 'usd', '$'):
                    entity_type = "MonetaryValue"
                    name = f"${value}"
                elif unit in ('euros', 'eur', '€'):
                    entity_type = "MonetaryValue"
                    name = f"€{value}"
                else:
                    entity_type = "Quantity"
                    name = f"{value} {unit}"
                
                quantity_id = self.kg.add_entity(
                    entity_type=entity_type,
                    name=name,
                    properties={"value": float(value), "unit": unit, "context": paragraph[:100]},
                    confidence=0.85
                )
                
                self.kg.add_relationship(
                    rel_type="MENTIONED_IN",
                    source=quantity_id,
                    target=doc_id,
                    confidence=0.85
                )
        
        # Extract key terms (simple approach)
        words = re.findall(r'\b[A-Za-z]{4,}\b', text.lower())
        word_freq = {}
        for word in words:
            word_freq[word] = word_freq.get(word, 0) + 1
        
        # Get top terms
        top_terms = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:10]
        
        for term, freq in top_terms:
            if freq >= 3:  # Only terms that appear at least 3 times
                term_id = self.kg.add_entity(
                    entity_type="KeyTerm",
                    name=term.capitalize(),
                    properties={"frequency": freq},
                    confidence=0.6
                )
                
                self.kg.add_relationship(
                    rel_type="APPEARS_IN",
                    source=term_id,
                    target=doc_id,
                    confidence=0.6
                )
        
        return {
            "document_id": doc_id,
            "entity_count": len(self.kg.entities),
            "relationship_count": len(self.kg.relationships)
        }
    
    def load_sample_documents(self, directory: str = "data/bank_policies") -> Dict[str, Any]:
        """Load and process sample documents from a directory"""
        results = {}
        
        if not os.path.exists(directory):
            os.makedirs(directory, exist_ok=True)
            
            # Create sample bank policies if directory is empty
            bank_policies = [
                {
                    "name": "Bank Loan Approval Policy.txt",
                    "content": """Bank Loan Approval Policy

1. Customers must have a minimum credit score of 700 to qualify for a loan.
2. Loan applications must be reviewed within 5 business days.
3. Interest rates depend on customer risk assessment.
4. Large loans ($50,000+) require approval from the Senior Loan Officer.
5. If a customer has a debt-to-income ratio higher than 40%, additional checks are required."""
                },
                {
                    "name": "Bank Customer Data Protection Policy.txt",
                    "content": """Bank Customer Data Protection Policy

1. Customer data must be encrypted before storage.
2. Employees are prohibited from sharing customer information without authorization.
3. Data access is restricted based on user roles.
4. Customer requests for data deletion must be processed within 30 days.
5. Security audits are conducted quarterly."""
                },
                {
                    "name": "Bank Fraud Prevention Policy.txt",
                    "content": """Bank Fraud Prevention Policy

1. Transactions above $10,000 require additional verification.
2. Customers with multiple failed login attempts must reset their password.
3. If a transaction appears suspicious, the fraud detection team is alerted.
4. All ATM withdrawals above $1,000 require two-factor authentication.
5. Fraud reports must be resolved within 72 hours."""
                }
            ]
            
            for policy in bank_policies:
                with open(os.path.join(directory, policy["name"]), "w") as f:
                    f.write(policy["content"])
        
        # Process all files in the directory
        for filename in os.listdir(directory):
            if filename.endswith(".txt"):
                file_path = os.path.join(directory, filename)
                with open(file_path, "r") as f:
                    content = f.read()
                
                # Process the document
                result = self.process_document(content, filename, "banking_policy")
                results[filename] = result
        
        return results

