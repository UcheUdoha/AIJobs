import spacy
from typing import List, Set

class NLPProcessor:
    def __init__(self):
        self.nlp = spacy.load("en_core_web_sm")
        
    def extract_skills(self, text: str) -> Set[str]:
        doc = self.nlp(text.lower())
        # Common technical skills and keywords
        skills = set()
        
        # Extract noun phrases as potential skills
        for chunk in doc.noun_chunks:
            if len(chunk.text) > 2:  # Avoid single letters
                skills.add(chunk.text.strip())
                
        return skills

    def calculate_similarity(self, resume_text: str, job_description: str) -> float:
        resume_doc = self.nlp(resume_text.lower())
        job_doc = self.nlp(job_description.lower())
        
        # Calculate cosine similarity
        similarity = resume_doc.similarity(job_doc)
        return float(similarity)

    def extract_entities(self, text: str) -> List[tuple]:
        doc = self.nlp(text)
        entities = [(ent.text, ent.label_) for ent in doc.ents]
        return entities
