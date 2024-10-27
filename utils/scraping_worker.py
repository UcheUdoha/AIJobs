import logging
import threading
import time
from utils.job_scraper import JobScraper

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def setup_scraping_worker():
    """Set up the job scraping worker to run periodically"""
    def worker():
        logger.info("Starting job scraping worker")
        scraper = JobScraper()
        
        while True:
            try:
                logger.info("Running job scraping cycle")
                scraper.scrape_jobs()
            except Exception as e:
                logger.error(f"Critical error in scraping worker: {str(e)}")
            finally:
                # Run every 6 hours
                time.sleep(6 * 3600)
    
    thread = threading.Thread(target=worker, daemon=True)
    thread.start()
    logger.info("Job scraping worker initialized")
