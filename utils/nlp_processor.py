import spacy
from sklearn.feature_extraction.text import TfidfVectorizer
from typing import List, Set, Dict, Optional

class NLPProcessor:
    def __init__(self):
        self.vectorizer = TfidfVectorizer(stop_words='english', max_features=100)
        # Load spaCy model for named entity recognition
        try:
            self.nlp = spacy.load("en_core_web_sm")
        except OSError:
            # Download the model if not available
            import os
            os.system("python -m spacy download en_core_web_sm")
            self.nlp = spacy.load("en_core_web_sm")
        
    def extract_skills(self, text: str) -> Set[str]:
        # Vectorize the text
        tfidf_matrix = self.vectorizer.fit_transform([text])
        
        # Get feature names (words) and their scores
        feature_names = self.vectorizer.get_feature_names_out()
        scores = tfidf_matrix.toarray()[0]
        
        # Get words with non-zero TF-IDF scores
        skills = {word for word, score in zip(feature_names, scores) if score > 0}
        return skills

    def extract_location(self, text: str) -> Optional[str]:
        """Extract location information from text using spaCy NER"""
        try:
            doc = self.nlp(text)
            locations = []
            
            # Extract location entities
            for ent in doc.ents:
                if ent.label_ in ['GPE', 'LOC']:  # Geographical and Location entities
                    locations.append(ent.text)
            
            # Return the most relevant location (usually the last mentioned)
            return locations[-1] if locations else None
            
        except Exception as e:
            print(f"Error extracting location: {str(e)}")
            return None

    def calculate_similarity(self, resume_text: str, job_description: str) -> float:
        # Vectorize both texts
        tfidf_matrix = self.vectorizer.fit_transform([resume_text, job_description])
        
        # Calculate cosine similarity
        similarity = (tfidf_matrix * tfidf_matrix.T).A[0][1]
        return float(similarity)

    def extract_entities(self, text: str) -> List[tuple]:
        # Simple keyword extraction based on TF-IDF scores
        tfidf_matrix = self.vectorizer.fit_transform([text])
        feature_names = self.vectorizer.get_feature_names_out()
        scores = tfidf_matrix.toarray()[0]
        
        # Get top scoring words and label them as 'KEYWORD'
        entities = [(word, 'KEYWORD') for word, score in zip(feature_names, scores) 
                   if score > 0][:10]  # Limit to top 10 keywords
        return entities

    def calculate_location_similarity(self, loc1: Optional[str], loc2: Optional[str]) -> float:
        """Calculate similarity score between two locations"""
        if not loc1 or not loc2:
            return 0.0
            
        # Convert to lowercase for comparison
        loc1 = loc1.lower()
        loc2 = loc2.lower()
        
        # Exact match
        if loc1 == loc2:
            return 1.0
            
        # Partial match (e.g., same city or state)
        loc1_parts = set(loc1.replace(',', '').split())
        loc2_parts = set(loc2.replace(',', '').split())
        
        common_parts = loc1_parts.intersection(loc2_parts)
        if common_parts:
            return len(common_parts) / max(len(loc1_parts), len(loc2_parts))
            
        return 0.0
