from sklearn.feature_extraction.text import TfidfVectorizer
from typing import List, Set, Dict, Optional
import re

class NLPProcessor:
    def __init__(self):
        self.vectorizer = TfidfVectorizer(stop_words='english', max_features=100)
        
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
        """Extract location information using regex patterns"""
        try:
            # Common location patterns
            location_patterns = [
                r'(?:Location|Based in|Located in|Remote from):\s*([\w\s,]+)',
                r'(?:City|State|Country):\s*([\w\s,]+)',
                r'(?:in|at)\s+([\w\s,]+(?:USA|US|United States|UK|Canada))',
                r'(?:Remote|Hybrid|On-site)\s+in\s+([\w\s,]+)',
                r'(?:Location):\s*([\w\s,]+)'
            ]
            
            # Try each pattern
            for pattern in location_patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    return match.group(1).strip()
                    
            # Additional location extraction from common formats
            lines = text.split('\n')
            for line in lines:
                if any(keyword in line.lower() for keyword in ['location:', 'address:', 'city:']):
                    return line.split(':', 1)[1].strip()
                    
            return None
            
        except Exception as e:
            print(f"Error in location extraction: {str(e)}")
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
