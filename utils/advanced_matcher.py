from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
from typing import List, Dict
import re

class AdvancedMatcher:
    def __init__(self):
        # Initialize TF-IDF vectorizer with custom parameters
        self.vectorizer = TfidfVectorizer(
            stop_words='english',
            ngram_range=(1, 2),  # Consider both unigrams and bigrams
            max_features=1000
        )
        
    def preprocess_text(self, text: str) -> str:
        """Clean and standardize input text"""
        # Convert to lowercase and remove special characters
        text = re.sub(r'[^\w\s]', ' ', text.lower())
        # Remove extra whitespace
        text = ' '.join(text.split())
        return text
        
    def extract_skills(self, text: str) -> List[str]:
        """Extract skills from text using keyword-based approach with common tech terms"""
        # Common technical skills and frameworks
        common_skills = {
            'python', 'java', 'javascript', 'react', 'node', 'sql', 'docker',
            'kubernetes', 'aws', 'azure', 'git', 'agile', 'scrum', 'ml',
            'ai', 'data science', 'machine learning', 'devops', 'cloud',
            'frontend', 'backend', 'fullstack', 'testing', 'ci/cd',
            'html', 'css', 'rest api', 'mongodb', 'postgresql', 'mysql',
            'typescript', 'ruby', 'php', 'c++', 'scala', 'rust', 'golang',
            'tensorflow', 'pytorch', 'pandas', 'numpy', 'spring boot'
        }
        
        # Preprocess text
        text = self.preprocess_text(text)
        words = text.split()
        
        # Find skills in text
        found_skills = set()
        for i in range(len(words)):
            # Check single words
            if words[i] in common_skills:
                found_skills.add(words[i])
            # Check two-word phrases
            if i < len(words) - 1:
                phrase = words[i] + ' ' + words[i + 1]
                if phrase in common_skills:
                    found_skills.add(phrase)
                    
        return list(found_skills)
        
    def calculate_semantic_similarity(self, text1: str, text2: str) -> float:
        """Calculate semantic similarity using TF-IDF and cosine similarity"""
        # Fit and transform the texts
        tfidf_matrix = self.vectorizer.fit_transform([text1, text2])
        return float(cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0])
        
    def calculate_match_score(self, resume_text: str, job_description: str) -> Dict:
        """Calculate comprehensive match score using multiple factors"""
        # Preprocess texts
        resume_text = self.preprocess_text(resume_text)
        job_description = self.preprocess_text(job_description)
        
        # Calculate semantic similarity using TF-IDF
        semantic_score = self.calculate_semantic_similarity(resume_text, job_description)
        
        # Extract and compare skills
        resume_skills = set(self.extract_skills(resume_text))
        job_skills = set(self.extract_skills(job_description))
        
        # Calculate skill match metrics
        common_skills = resume_skills.intersection(job_skills)
        required_skills_coverage = len(common_skills) / max(len(job_skills), 1)
        skill_relevance = len(common_skills) / max(len(resume_skills), 1)
        
        # Calculate weighted skill score
        skill_score = (0.7 * required_skills_coverage + 0.3 * skill_relevance)
        
        # Calculate experience level match (based on years mentioned)
        exp_pattern = r'\b(\d+)\s*(?:years?|yrs?)\b'
        resume_years = [int(y) for y in re.findall(exp_pattern, resume_text)]
        job_years = [int(y) for y in re.findall(exp_pattern, job_description)]
        
        exp_score = 1.0  # Default if no years mentioned
        if job_years and resume_years:
            job_exp = max(job_years)
            resume_exp = max(resume_years)
            # Calculate experience match score with some flexibility
            if resume_exp >= job_exp:
                exp_score = 1.0
            else:
                exp_score = resume_exp / max(job_exp, 1)
        
        # Calculate final weighted score
        weights = {
            'semantic': 0.4,
            'skills': 0.4,
            'experience': 0.2
        }
        
        final_score = (
            weights['semantic'] * semantic_score +
            weights['skills'] * skill_score +
            weights['experience'] * exp_score
        )
        
        return {
            'overall_score': round(final_score * 100, 2),
            'semantic_score': round(semantic_score * 100, 2),
            'skill_score': round(skill_score * 100, 2),
            'experience_match': round(exp_score * 100, 2),
            'matching_skills': sorted(list(common_skills))
        }
