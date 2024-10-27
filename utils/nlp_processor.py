from sklearn.feature_extraction.text import TfidfVectorizer
from typing import List, Set

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
