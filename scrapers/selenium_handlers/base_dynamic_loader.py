# scrapers/selenium_handlers/base_dynamic_loader.py
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import logging

class BaseDynamicLoader:
    def __init__(self):
        self.driver = webdriver.Chrome()
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