import re
import logging
from typing import Set, Optional, Tuple
import time
from collections import defaultdict

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class NLPProcessor:
    def __init__(self):
        self.cache = {}
        self.cache_timestamp = time.time()
        self.cache_lifetime = 3600  # 1 hour cache lifetime
        
        # Common skills and their variations
        self.skill_patterns = {
            'languages': r'\b(python|java(?:script)?|typescript|c\+\+|ruby|php|golang|rust|scala)\b',
            'frameworks': r'\b(react|angular|vue|django|flask|spring|express|node\.js|tensorflow|pytorch)\b',
            'databases': r'\b(sql|mysql|postgresql|mongodb|redis|elasticsearch|cassandra)\b',
            'cloud': r'\b(aws|azure|gcp|docker|kubernetes|terraform|jenkins|ci/cd)\b',
            'concepts': r'\b(rest(?:ful)?|graphql|microservices|agile|scrum|devops|machine learning|ai)\b'
        }
        
        # Location patterns
        self.location_patterns = [
            r'(?:Location|Based in|Located in|Remote from):\s*([\w\s,]+)',
            r'(?:City|State|Country|Region):\s*([\w\s,]+)',
            r'(?:in|at)\s+([\w\s,]+)',
            r'(?:Remote|Hybrid|On-site)\s+in\s+([\w\s,]+)',
            r'(?:📍|🌍|🌎|🌏)\s*([\w\s,]+)'
        ]
        
        # Country dictionary
        self.country_dict = {
            'usa': 'United States',
            'us': 'United States',
            'uk': 'United Kingdom',
            'canada': 'Canada',
            'australia': 'Australia',
            'germany': 'Germany',
            'france': 'France',
            'japan': 'Japan',
            'india': 'India'
        }
            
    def _clear_expired_cache(self):
        """Clear expired cache entries"""
        current_time = time.time()
        if current_time - self.cache_timestamp > self.cache_lifetime:
            self.cache.clear()
            self.cache_timestamp = current_time

    def extract_skills(self, text: str) -> Set[str]:
        """Extract skills using regex patterns with error handling and caching"""
        try:
            self._clear_expired_cache()
            
            # Cache key based on text
            cache_key = hash(text)
            if cache_key in self.cache:
                return self.cache[cache_key]
            
            skills = set()
            text = text.lower()
            
            # Try each pattern category
            for category, pattern in self.skill_patterns.items():
                try:
                    matches = re.finditer(pattern, text, re.IGNORECASE)
                    for match in matches:
                        skills.add(match.group(0).lower())
                except Exception as e:
                    logger.error(f"Error in pattern matching for {category}: {str(e)}")
                    continue
            
            # Add fallback for common variations
            skill_variations = {
                'js': 'javascript',
                'py': 'python',
                'ml': 'machine learning',
                'k8s': 'kubernetes'
            }
            
            for abbrev, full in skill_variations.items():
                if re.search(r'\b' + abbrev + r'\b', text, re.IGNORECASE):
                    skills.add(full)
            
            # Cache result
            self.cache[cache_key] = skills
            return skills
            
        except Exception as e:
            logger.error(f"Error in skill extraction: {str(e)}")
            return set()

    def extract_location(self, text: str) -> Optional[str]:
        """Extract location information using regex patterns"""
        try:
            self._clear_expired_cache()
            
            # Cache key based on text
            cache_key = f"loc_{hash(text)}"
            if cache_key in self.cache:
                return self.cache[cache_key]
            
            # Try each pattern
            for pattern in self.location_patterns:
                try:
                    match = re.search(pattern, text, re.IGNORECASE)
                    if match:
                        location = match.group(1).strip()
                        # Basic validation
                        if len(location) > 2 and len(location) < 100:
                            self.cache[cache_key] = location
                            return location
                except Exception as e:
                    logger.error(f"Error in location pattern matching: {str(e)}")
                    continue
            
            # Fallback: Look for postal codes or state codes
            postal_pattern = r'\b[A-Z]{2}\s+\d{5}\b'
            state_pattern = r'\b(?:AL|AK|AZ|AR|CA|CO|CT|DE|FL|GA|HI|ID|IL|IN|IA|KS|KY|LA|ME|MD|MA|MI|MN|MS|MO|MT|NE|NV|NH|NJ|NM|NY|NC|ND|OH|OK|OR|PA|RI|SC|SD|TN|TX|UT|VT|VA|WA|WV|WI|WY)\b'
            
            postal_match = re.search(postal_pattern, text.upper())
            state_match = re.search(state_pattern, text.upper())
            
            if postal_match:
                location = postal_match.group(0)
                self.cache[cache_key] = location
                return location
            elif state_match:
                location = state_match.group(0)
                self.cache[cache_key] = location
                return location
            
            return None
            
        except Exception as e:
            logger.error(f"Error in location extraction: {str(e)}")
            return None

    def process_text(self, text: str) -> dict:
        """Process text to extract all relevant information"""
        try:
            return {
                'skills': self.extract_skills(text),
                'location': self.extract_location(text),
                'processed_text': text.strip()
            }
        except Exception as e:
            logger.error(f"Error in text processing: {str(e)}")
            return {
                'skills': set(),
                'location': None,
                'processed_text': text.strip() if text else ""
            }
