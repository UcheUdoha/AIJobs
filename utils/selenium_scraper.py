from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import time
import logging
import random
from typing import Dict, List, Optional
import os
import subprocess
import uuid

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SeleniumScraper:
    def __init__(self):
        try:
            self.setup_driver()
        except Exception as e:
            logger.error(f"Failed to initialize Selenium driver: {str(e)}")
            raise

    def setup_driver(self):
        """Initialize Chrome driver with appropriate options"""
        try:
            chrome_options = Options()
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--headless')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--window-size=1920,1080')
            chrome_options.add_argument('--disable-notifications')
            
            # Add stealth options
            chrome_options.add_argument('--disable-blink-features=AutomationControlled')
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
            
            # Find chromium binary
            try:
                chrome_path = subprocess.check_output(['which', 'chromium']).decode().strip()
                if chrome_path:
                    chrome_options.binary_location = chrome_path
                    logger.info(f"Found Chromium binary at: {chrome_path}")
            except subprocess.CalledProcessError:
                logger.error("Could not find Chromium binary")
                raise

            # Find chromedriver path
            try:
                chromedriver_path = subprocess.check_output(['which', 'chromedriver']).decode().strip()
                if not chromedriver_path:
                    raise ValueError("Chromedriver not found")
                logger.info(f"Found chromedriver at: {chromedriver_path}")
                
                # Initialize driver
                self.driver = webdriver.Chrome(
                    service=Service(chromedriver_path),
                    options=chrome_options
                )
                logger.info("Successfully initialized Chrome driver")
                
                # Execute CDP commands to avoid detection
                self.driver.execute_cdp_cmd('Network.setUserAgentOverride', {
                    "userAgent": 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0 Safari/537.36'
                })
                self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
                
            except (subprocess.CalledProcessError, ValueError) as e:
                logger.error(f"Error finding chromedriver: {str(e)}")
                raise
                
        except Exception as e:
            logger.error(f"Error in setup_driver: {str(e)}")
            raise
        
    def random_delay(self, min_seconds=2, max_seconds=5):
        """Add random delay between requests to avoid detection"""
        time.sleep(random.uniform(min_seconds, max_seconds))

    def extract_job_linkedin(self, job_card, config: Dict) -> Optional[Dict]:
        """Extract job information from LinkedIn job card"""
        try:
            # Extract basic job information
            try:
                title = job_card.find_element(By.CSS_SELECTOR, config['title_selector']).text.strip()
                company = job_card.find_element(By.CSS_SELECTOR, config['company_selector']).text.strip()
                location = job_card.find_element(By.CSS_SELECTOR, config['location_selector']).text.strip()
                
                if not all([title, company, location]):
                    logger.warning("Missing required job information")
                    return None
                    
            except NoSuchElementException as e:
                logger.error(f"Could not find job information elements: {str(e)}")
                return None
                
            # Get job URL and ID
            try:
                parent_link = job_card.find_element(By.CSS_SELECTOR, "a.base-card__full-link")
                job_url = parent_link.get_attribute('href')
                job_id = job_url.split('/')[-1].split('?')[0]
                
                if not job_url:
                    logger.warning("Missing job URL")
                    return None
                    
            except NoSuchElementException:
                logger.error("Could not find job link element")
                return None
            
            # Click job card and wait for description
            try:
                parent_link.click()
                self.random_delay(1, 2)
                
                # Wait for description to load
                description = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "div.show-more-less-html__markup"))
                ).text.strip()
                
                if not description:
                    logger.warning(f"Empty description for job: {title}")
                    return None
                    
            except (TimeoutException, Exception) as e:
                logger.error(f"Error getting job description: {str(e)}")
                return None
            
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
            logger.info(f"Starting to scrape jobs from: {url}")
            
            # Navigate to URL with retry logic
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    self.driver.get(url)
                    break
                except Exception as e:
                    if attempt == max_retries - 1:
                        logger.error(f"Failed to load URL after {max_retries} attempts: {str(e)}")
                        return jobs
                    logger.warning(f"Attempt {attempt + 1} failed, retrying...")
                    self.random_delay(5, 10)
            
            self.random_delay()
            
            # Wait for job cards to load
            try:
                WebDriverWait(self.driver, 20).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, config['job_card_selector']))
                )
            except TimeoutException:
                logger.error("Timeout waiting for job cards to load")
                return jobs
            
            # Scroll to load more jobs
            for _ in range(3):
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                self.random_delay(1, 2)
            
            # Get all job cards
            job_cards = self.driver.find_elements(By.CSS_SELECTOR, config['job_card_selector'])
            logger.info(f"Found {len(job_cards)} job cards")
            
            # Process job cards
            for index, card in enumerate(job_cards[:10]):  # Limit to 10 jobs per source
                try:
                    if config['type'] == 'linkedin':
                        job_data = self.extract_job_linkedin(card, config)
                    else:
                        logger.error(f"Unsupported job source type: {config['type']}")
                        continue
                        
                    if job_data:
                        jobs.append(job_data)
                        logger.info(f"Successfully extracted job {index + 1}: {job_data['title']}")
                    
                    self.random_delay(1, 3)
                    
                except Exception as e:
                    logger.error(f"Error processing job card {index + 1}: {str(e)}")
                    continue
                    
        except Exception as e:
            logger.error(f"Error scraping jobs from {url}: {str(e)}")
            
        finally:
            logger.info(f"Completed scraping {len(jobs)} jobs from {url}")
            
        return jobs
        
    def close(self):
        """Close the Selenium driver"""
        if hasattr(self, 'driver'):
            try:
                self.driver.quit()
                logger.info("Successfully closed Selenium driver")
            except Exception as e:
                logger.error(f"Error closing Selenium driver: {str(e)}")
