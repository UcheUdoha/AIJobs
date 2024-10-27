import spacy
from sklearn.feature_extraction.text import TfidfVectorizer
from typing import List, Set, Dict, Optional, Tuple
import re
from collections import defaultdict

class NLPProcessor:
    def __init__(self):
        self.vectorizer = TfidfVectorizer(stop_words='english', max_features=100)
        try:
            self.nlp = spacy.load('en_core_web_sm')
        except OSError:
            import subprocess
            subprocess.run(['python', '-m', 'spacy', 'download', 'en_core_web_sm'])
            self.nlp = spacy.load('en_core_web_sm')
        
        # Common country names and their variations
        self.country_dict = {
            'usa': 'United States',
            'us': 'United States',
            'united states': 'United States',
            'uk': 'United Kingdom',
            'gb': 'United Kingdom',
            'great britain': 'United Kingdom',
            'canada': 'Canada',
            'australia': 'Australia',
            'germany': 'Germany',
            'deutschland': 'Germany',
            'france': 'France',
            'japan': 'Japan',
            'india': 'India',
            'singapore': 'Singapore',
        }
        
    def extract_skills(self, text: str) -> Set[str]:
        # Vectorize the text
        tfidf_matrix = self.vectorizer.fit_transform([text])
        
        # Get feature names (words) and their scores
        feature_names = self.vectorizer.get_feature_names_out()
        scores = tfidf_matrix.toarray()[0]
        
        # Get words with non-zero TF-IDF scores
        skills = {word for word, score in zip(feature_names, scores) if score > 0}
        return skills

    def extract_location(self, text: str) -> Tuple[Optional[str], Optional[str]]:
        """
        Extract location information using regex patterns and NLP
        Returns: (location, country)
        """
        try:
            # Process text with spaCy
            doc = self.nlp(text)
            
            # Extract location entities
            locations = []
            for ent in doc.ents:
                if ent.label_ in ['GPE', 'LOC']:
                    locations.append(ent.text)

            # Common location patterns with international support
            location_patterns = [
                r'(?:Location|Based in|Located in|Remote from):\s*([\w\s,]+)',
                r'(?:City|State|Country|Region):\s*([\w\s,]+)',
                r'(?:in|at)\s+([\w\s,]+)',
                r'(?:Remote|Hybrid|On-site)\s+in\s+([\w\s,]+)',
                r'(?:Location):\s*([\w\s,]+)',
                r'(?:📍|🌍|🌎|🌏)\s*([\w\s,]+)'  # Support for location emojis
            ]
            
            extracted_location = None
            country = None
            
            # Try each pattern
            for pattern in location_patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    extracted_location = match.group(1).strip()
                    break
            
            if not extracted_location and locations:
                extracted_location = locations[0]
            
            if extracted_location:
                # Try to identify country
                location_parts = extracted_location.lower().split(',')
                for part in location_parts:
                    part = part.strip()
                    if part in self.country_dict:
                        country = self.country_dict[part]
                        # Remove country from location if it's the only component
                        if len(location_parts) == 1:
                            extracted_location = None
                        break
            
            # Handle "Remote" cases
            if extracted_location and 'remote' in extracted_location.lower():
                if '/' in extracted_location:
                    # Handle "Remote/London" format
                    parts = extracted_location.split('/')
                    extracted_location = parts[1].strip()
                elif 'in' in extracted_location.lower():
                    # Handle "Remote in Germany" format
                    parts = extracted_location.lower().split('in')
                    location_part = parts[1].strip()
                    if location_part in self.country_dict:
                        country = self.country_dict[location_part]
                        extracted_location = 'Remote'
            
            return extracted_location, country
                    
        except Exception as e:
            print(f"Error in location extraction: {str(e)}")
            return None, None

    def calculate_similarity(self, resume_text: str, job_description: str) -> float:
        # Vectorize both texts
        tfidf_matrix = self.vectorizer.fit_transform([resume_text, job_description])
        
        # Calculate cosine similarity
        similarity = (tfidf_matrix * tfidf_matrix.T).A[0][1]
        return float(similarity)

    def extract_entities(self, text: str) -> List[tuple]:
        # Process with spaCy for better entity recognition
        doc = self.nlp(text)
        
        # Extract named entities
        entities = [(ent.text, ent.label_) for ent in doc.ents 
                   if ent.label_ in ['SKILL', 'ORG', 'GPE', 'PERSON', 'LOC']]
        
        # Add TF-IDF based keywords
        tfidf_matrix = self.vectorizer.fit_transform([text])
        feature_names = self.vectorizer.get_feature_names_out()
        scores = tfidf_matrix.toarray()[0]
        
        # Get top scoring words and label them as 'KEYWORD'
        keywords = [(word, 'KEYWORD') for word, score in zip(feature_names, scores) 
                   if score > 0][:10]  # Limit to top 10 keywords
        
        return entities + keywords
