import logging
import json
from datetime import datetime
from typing import List, Dict, Optional
from utils.database import Database
from utils.selenium_scraper import SeleniumScraper
from utils.web_scraper import get_page_content, extract_job_data_from_html
from utils.rate_limiter import RateLimiter, CircuitBreaker
import time
import random

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class JobScraper:
    def __init__(self):
        self.db = Database()
        self.selenium_scraper = None
        self.rate_limiter = RateLimiter(max_requests=1, time_window=2)  # 1 request per 2 seconds
        self.circuit_breaker = CircuitBreaker(failure_threshold=5, reset_timeout=300)  # 5 failures, 5 min timeout
        
    def get_active_sources(self) -> List[Dict]:
        """Get all active job sources from database"""
        with self.db.get_cursor() as cur:
            cur.execute("""
                SELECT * FROM job_sources 
                WHERE is_active = true 
                ORDER BY last_scraped_at ASC NULLS FIRST
                LIMIT 3
            """)
            columns = [desc[0] for desc in cur.description]
            return [dict(zip(columns, row)) for row in cur.fetchall()]
    
    def save_jobs(self, jobs: List[Dict], source_id: int) -> None:
        """Save scraped jobs to database with batch processing"""
        try:
            with self.db.get_cursor() as cur:
                # Prepare batch insert
                args = []
                for job in jobs:
                    args.extend([
                        job['title'], job['company'], job['location'],
                        job['description'], source_id, job['external_id'],
                        job['url'], datetime.now()
                    ])
                
                cur.execute("""
                    INSERT INTO jobs 
                    (title, company, location, description, source_id, external_id, url, posted_at)
                    VALUES %s
                    ON CONFLICT ON CONSTRAINT unique_external_job DO NOTHING
                """, args)
                
                self.db.conn.commit()
                logger.info(f"Successfully saved {len(jobs)} jobs from source {source_id}")
                
        except Exception as e:
            logger.error(f"Error saving jobs: {str(e)}")
            self.db.conn.rollback()
    
    def update_last_scraped(self, source_id: int) -> None:
        """Update last scraped timestamp for a source"""
        try:
            with self.db.get_cursor() as cur:
                cur.execute("""
                    UPDATE job_sources 
                    SET last_scraped_at = CURRENT_TIMESTAMP 
                    WHERE id = %s
                """, (source_id,))
                self.db.conn.commit()
        except Exception as e:
            logger.error(f"Error updating last scraped timestamp: {str(e)}")
            self.db.conn.rollback()

    def exponential_backoff(self, attempt: int, base_delay: float = 1.0, max_delay: float = 60.0) -> float:
        """Calculate exponential backoff delay"""
        delay = min(base_delay * (2 ** attempt), max_delay)
        jitter = random.uniform(0, 0.1 * delay)
        return delay + jitter

    def scrape_with_fallback(self, url: str, config: Dict) -> List[Dict]:
        """Try scraping with Selenium first, fallback to basic scraping if it fails"""
        if not self.circuit_breaker.can_execute():
            logger.warning("Circuit breaker is open, skipping scrape")
            return []
        
        jobs = []
        attempt = 0
        max_attempts = 3
        
        while attempt < max_attempts:
            try:
                # Wait for rate limit
                self.rate_limiter.wait()
                
                if not self.selenium_scraper:
                    self.selenium_scraper = SeleniumScraper()
                jobs = self.selenium_scraper.scrape_jobs(url, config)
                
                if jobs:
                    self.circuit_breaker.record_success()
                    break
                    
            except Exception as e:
                logger.error(f"Selenium scraping failed (attempt {attempt + 1}): {str(e)}")
                self.circuit_breaker.record_failure()
                
                delay = self.exponential_backoff(attempt)
                logger.info(f"Waiting {delay:.2f} seconds before retry")
                time.sleep(delay)
                
                attempt += 1
        
        # If Selenium fails or returns no jobs, try fallback method
        if not jobs:
            logger.info("Falling back to basic web scraping")
            try:
                self.rate_limiter.wait()
                html_content = get_page_content(url)
                if html_content:
                    job_data = extract_job_data_from_html(html_content, config)
                    if job_data:
                        jobs.append(job_data)
                        self.circuit_breaker.record_success()
            except Exception as e:
                logger.error(f"Fallback scraping failed: {str(e)}")
                self.circuit_breaker.record_failure()
        
        return jobs
    
    def scrape_jobs(self) -> None:
        """Main job scraping function with optimizations"""
        try:
            sources = self.get_active_sources()
            logger.info(f"Found {len(sources)} active sources to scrape")
            
            for source in sources:
                try:
                    logger.info(f"Scraping jobs from {source['name']}")
                    
                    # Scrape jobs with fallback mechanism
                    jobs = self.scrape_with_fallback(
                        source['url'],
                        source['scraping_config']
                    )
                    
                    # Save jobs and update timestamp
                    if jobs:
                        self.save_jobs(jobs, source['id'])
                        self.update_last_scraped(source['id'])
                        logger.info(f"Successfully scraped {len(jobs)} jobs from {source['name']}")
                    
                    # Rate limiting between sources
                    time.sleep(2)
                    
                except Exception as e:
                    logger.error(f"Error scraping source {source['name']}: {str(e)}")
                    continue
                    
        except Exception as e:
            logger.error(f"Critical error in job scraping: {str(e)}")
        finally:
            if self.selenium_scraper:
                self.selenium_scraper.close()
