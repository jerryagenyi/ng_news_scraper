# ng_news_scraper/selenium_handlers/base_dynamic_loader.py
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import logging

class BaseDynamicLoader:
    def __init__(self):
        chrome_options = Options()
        chrome_options.add_argument("--headless")  # Run in headless mode
        self.driver = webdriver.Chrome(options=chrome_options)
        self.logger = logging.getLogger(__name__)
    
    def load_more_content(self, url):
        """Base implementation for loading more content"""
        raise NotImplementedError("Each site loader must implement this method")
    
    def extract_articles(self):
        """Base implementation for extracting article data"""
        raise NotImplementedError("Each site loader must implement this method")
    
    def close(self):
        """Clean up Selenium driver"""
        if self.driver:
            self.driver.quit()