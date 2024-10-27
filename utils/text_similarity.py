import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

class TextSimilarity:
    def __init__(self):
        self.vectorizer = TfidfVectorizer(stop_words='english')
        
    def calculate_match_score(self, resume_text: str, job_description: str) -> float:
        # Vectorize the texts
        tfidf_matrix = self.vectorizer.fit_transform([resume_text, job_description])
        
        # Calculate cosine similarity
        similarity = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])
        
        return float(similarity[0][0])

    def get_matching_keywords(self, resume_text: str, job_description: str) -> list:
        # Get common important terms between resume and job description
        documents = [resume_text, job_description]
        tfidf_matrix = self.vectorizer.fit_transform(documents)
        
        feature_names = self.vectorizer.get_feature_names_out()
        dense = tfidf_matrix.todense()
        
        matches = []
        for term_idx, term in enumerate(feature_names):
            if dense[0, term_idx] > 0 and dense[1, term_idx] > 0:
                matches.append(term)
                
        return matches
