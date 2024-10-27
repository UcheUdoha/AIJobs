from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
from typing import List, Dict, Set

class AdvancedMatcher:
    def __init__(self):
        # Initialize TF-IDF vectorizer
        self.vectorizer = TfidfVectorizer(
            stop_words='english',
            ngram_range=(1, 2),
            max_features=500
        )
        
        # Common technical skills dictionary
        self.common_skills = {
            'python', 'java', 'javascript', 'react', 'node', 'sql', 'docker',
            'kubernetes', 'aws', 'azure', 'git', 'agile', 'scrum', 'ml',
            'ai', 'data science', 'machine learning', 'devops', 'cloud',
            'frontend', 'backend', 'fullstack', 'testing', 'ci/cd',
            'html', 'css', 'rest api', 'mongodb', 'postgresql', 'mysql',
            'typescript', 'ruby', 'php', 'c++', 'scala', 'rust', 'golang'
        }

    def extract_skills(self, text: str) -> Set[str]:
        """Extract skills from text using keyword matching"""
        try:
            # Convert to lowercase for matching
            text = text.lower()
            words = text.split()
            
            # Find skills in text (both single words and two-word phrases)
            found_skills = set()
            for i in range(len(words)):
                # Single word skills
                if words[i] in self.common_skills:
                    found_skills.add(words[i])
                # Two-word skills
                if i < len(words) - 1:
                    phrase = words[i] + ' ' + words[i + 1]
                    if phrase in self.common_skills:
                        found_skills.add(phrase)
            
            return found_skills
        except Exception as e:
            print(f"Error in skill extraction: {str(e)}")
            return set()

    def calculate_semantic_similarity(self, text1: str, text2: str) -> float:
        """Calculate semantic similarity using TF-IDF and cosine similarity"""
        try:
            # Fit and transform the texts
            tfidf_matrix = self.vectorizer.fit_transform([text1, text2])
            similarity = float(cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0])
            return max(0.0, min(1.0, similarity))  # Ensure score is between 0 and 1
        except Exception as e:
            print(f"Error in semantic similarity calculation: {str(e)}")
            return 0.0

    def calculate_match_score(self, resume_text: str, job_description: str) -> Dict:
        """Calculate match score using semantic similarity and skill matching"""
        try:
            # Input validation
            if not resume_text or not job_description:
                raise ValueError("Resume text and job description cannot be empty")

            # Calculate semantic similarity
            semantic_score = self.calculate_semantic_similarity(resume_text, job_description)

            # Extract skills from both texts
            resume_skills = self.extract_skills(resume_text)
            job_skills = self.extract_skills(job_description)

            # Calculate skill match score
            if job_skills:
                matching_skills = resume_skills.intersection(job_skills)
                skill_score = len(matching_skills) / len(job_skills)
            else:
                skill_score = 0.0
                matching_skills = set()

            # Calculate final weighted score (equal weights for semantic and skill matching)
            final_score = (semantic_score * 0.5) + (skill_score * 0.5)

            return {
                'overall_score': round(final_score * 100, 2),
                'semantic_score': round(semantic_score * 100, 2),
                'skill_score': round(skill_score * 100, 2),
                'matching_skills': sorted(list(matching_skills))
            }
        except Exception as e:
            print(f"Error in match score calculation: {str(e)}")
            return {
                'overall_score': 0.0,
                'semantic_score': 0.0,
                'skill_score': 0.0,
                'matching_skills': []
            }
