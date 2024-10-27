import logging
import json
from datetime import datetime
from typing import List, Dict, Optional
from utils.database import Database
from utils.selenium_scraper import SeleniumScraper
from utils.web_scraper import get_page_content, extract_job_data_from_html
import time
import random

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class JobScraper:
    def __init__(self):
        self.db = Database()
        self.selenium_scraper = None
        
    def get_active_sources(self) -> List[Dict]:
        """Get all active job sources from database"""
        with self.db.conn.cursor() as cur:
            cur.execute("""
                SELECT * FROM job_sources 
                WHERE is_active = true 
                ORDER BY last_scraped_at ASC NULLS FIRST
                LIMIT 3  -- Limit sources per run to avoid overloading
            """)
            columns = [desc[0] for desc in cur.description]
            return [dict(zip(columns, row)) for row in cur.fetchall()]
    
    def save_jobs(self, jobs: List[Dict], source_id: int) -> None:
        """Save scraped jobs to database"""
        try:
            with self.db.conn.cursor() as cur:
                for job in jobs:
                    cur.execute("""
                        INSERT INTO jobs 
                        (title, company, location, description, source_id, external_id, url, posted_at)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT ON CONSTRAINT unique_external_job DO NOTHING
                    """, (
                        job['title'], job['company'], job['location'], job['description'],
                        source_id, job['external_id'], job['url'], datetime.now()
                    ))
                self.db.conn.commit()
                logger.info(f"Successfully saved {len(jobs)} jobs from source {source_id}")
                
        except Exception as e:
            logger.error(f"Error saving jobs: {str(e)}")
            self.db.conn.rollback()
    
    def update_last_scraped(self, source_id: int) -> None:
        """Update last scraped timestamp for a source"""
        try:
            with self.db.conn.cursor() as cur:
                cur.execute("""
                    UPDATE job_sources 
                    SET last_scraped_at = CURRENT_TIMESTAMP 
                    WHERE id = %s
                """, (source_id,))
                self.db.conn.commit()
        except Exception as e:
            logger.error(f"Error updating last scraped timestamp: {str(e)}")
            self.db.conn.rollback()

    def scrape_with_fallback(self, url: str, config: Dict) -> List[Dict]:
        """Try scraping with Selenium first, fallback to basic scraping if it fails"""
        jobs = []
        
        # Try Selenium first
        try:
            if not self.selenium_scraper:
                self.selenium_scraper = SeleniumScraper()
            jobs = self.selenium_scraper.scrape_jobs(url, config)
        except Exception as e:
            logger.error(f"Selenium scraping failed: {str(e)}")
            
        # If Selenium fails or returns no jobs, try fallback method
        if not jobs:
            logger.info("Falling back to basic web scraping")
            try:
                html_content = get_page_content(url)
                if html_content:
                    job_data = extract_job_data_from_html(html_content, config)
                    if job_data:
                        jobs.append(job_data)
            except Exception as e:
                logger.error(f"Fallback scraping failed: {str(e)}")
        
        return jobs
    
    def scrape_jobs(self) -> None:
        """Main job scraping function"""
        try:
            sources = self.get_active_sources()
            logger.info(f"Found {len(sources)} active sources to scrape")
            
            for source in sources:
                try:
                    logger.info(f"Scraping jobs from {source['name']}")
                    
                    # Add random delay between sources
                    time.sleep(random.uniform(2, 5))
                    
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
                    
                except Exception as e:
                    logger.error(f"Error scraping source {source['name']}: {str(e)}")
                    continue
                    
        except Exception as e:
            logger.error(f"Critical error in job scraping: {str(e)}")
        finally:
            if self.selenium_scraper:
                self.selenium_scraper.close()
