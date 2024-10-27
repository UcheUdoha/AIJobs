import trafilatura
import logging
from typing import Optional, Dict
import json

logger = logging.getLogger(__name__)

def extract_job_data_from_html(html: str, config: Dict) -> Optional[Dict]:
    """Extract job data using trafilatura when Selenium fails"""
    try:
        # Extract main content
        extracted_text = trafilatura.extract(html)
        
        if not extracted_text:
            return None
            
        # Basic job information extraction
        job_data = {
            'title': '',
            'company': '',
            'location': '',
            'description': extracted_text,
            'url': '',
            'external_id': ''
        }
        
        return job_data
    except Exception as e:
        logger.error(f"Error extracting job data: {str(e)}")
        return None

def get_page_content(url: str) -> Optional[str]:
    """Get website content using trafilatura"""
    try:
        downloaded = trafilatura.fetch_url(url)
        return downloaded
    except Exception as e:
        logger.error(f"Error fetching URL {url}: {str(e)}")
        return None
