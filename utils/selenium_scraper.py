from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager
import time
import logging
import random
from typing import Dict, List, Optional

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SeleniumScraper:
    def __init__(self):
        self.setup_driver()
        
    def setup_driver(self):
        """Initialize Chrome driver with appropriate options"""
        chrome_options = Options()
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36')
        
        self.driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()),
            options=chrome_options
        )
        
    def random_delay(self, min_seconds=2, max_seconds=5):
        """Add random delay between requests to avoid detection"""
        time.sleep(random.uniform(min_seconds, max_seconds))
        
    def extract_job_indeed(self, job_card, config: Dict) -> Optional[Dict]:
        """Extract job information from Indeed job card"""
        try:
            title = job_card.find_element(By.CSS_SELECTOR, config['title_selector']).text
            company = job_card.find_element(By.CSS_SELECTOR, config['company_selector']).text
            location = job_card.find_element(By.CSS_SELECTOR, config['location_selector']).text
            
            # Get job URL and ID
            job_link = job_card.find_element(By.TAG_NAME, 'a')
            job_url = job_link.get_attribute('href')
            job_id = job_link.get_attribute('data-jk')
            
            # Get full job description
            self.driver.execute_script('window.open("","_blank");')
            self.driver.switch_to.window(self.driver.window_handles[-1])
            self.driver.get(job_url)
            self.random_delay(1, 3)
            
            try:
                description = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.CLASS_NAME, 'jobsearch-jobDescriptionText'))
                ).text
            except TimeoutException:
                description = "Description not available"
                
            self.driver.close()
            self.driver.switch_to.window(self.driver.window_handles[0])
            
            return {
                'title': title,
                'company': company,
                'location': location,
                'description': description,
                'url': job_url,
                'external_id': job_id
            }
            
        except Exception as e:
            logger.error(f"Error extracting Indeed job details: {str(e)}")
            return None
            
    def extract_job_linkedin(self, job_card, config: Dict) -> Optional[Dict]:
        """Extract job information from LinkedIn job card"""
        try:
            title = job_card.find_element(By.CSS_SELECTOR, config['title_selector']).text
            company = job_card.find_element(By.CSS_SELECTOR, config['company_selector']).text
            location = job_card.find_element(By.CSS_SELECTOR, config['location_selector']).text
            
            # Get job URL and ID
            job_link = job_card.find_element(By.TAG_NAME, 'a')
            job_url = job_link.get_attribute('href')
            job_id = job_link.get_attribute('data-id')
            
            # Get full job description
            self.driver.execute_script('window.open("","_blank");')
            self.driver.switch_to.window(self.driver.window_handles[-1])
            self.driver.get(job_url)
            self.random_delay(1, 3)
            
            try:
                description = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.CLASS_NAME, 'jobs-description'))
                ).text
            except TimeoutException:
                description = "Description not available"
                
            self.driver.close()
            self.driver.switch_to.window(self.driver.window_handles[0])
            
            return {
                'title': title,
                'company': company,
                'location': location,
                'description': description,
                'url': job_url,
                'external_id': job_id
            }
            
        except Exception as e:
            logger.error(f"Error extracting LinkedIn job details: {str(e)}")
            return None
    
    def scrape_jobs(self, url: str, config: Dict) -> List[Dict]:
        """Scrape jobs from a given URL using Selenium"""
        jobs = []
        try:
            self.driver.get(url)
            self.random_delay()
            
            # Wait for job cards to load
            WebDriverWait(self.driver, 20).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, config['job_card_selector']))
            )
            
            # Get all job cards
            job_cards = self.driver.find_elements(By.CSS_SELECTOR, config['job_card_selector'])
            
            for card in job_cards[:10]:  # Limit to 10 jobs per source to avoid overloading
                if config['type'] == 'indeed':
                    job_data = self.extract_job_indeed(card, config)
                elif config['type'] == 'linkedin':
                    job_data = self.extract_job_linkedin(card, config)
                    
                if job_data:
                    jobs.append(job_data)
                self.random_delay(1, 3)
                
        except Exception as e:
            logger.error(f"Error scraping jobs from {url}: {str(e)}")
            
        return jobs
        
    def close(self):
        """Close the Selenium driver"""
        if self.driver:
            self.driver.quit()
