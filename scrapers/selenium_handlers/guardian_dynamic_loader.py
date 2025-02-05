# scrapers/selenium_handlers/guardian_dynamic_loader.py
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from .base_dynamic_loader import BaseDynamicLoader
import time
import logging

class GuardianDynamicLoader(BaseDynamicLoader):
    def load_more_content(self, url):
        try:
            self.driver.get(url)
            
            # First check if there's a load more button
            try:
                load_more = WebDriverWait(self.driver, 5).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "button.load-more-button"))
                )
                
                # Track number of articles before clicking
                articles_before = len(self.driver.find_elements(
                    By.CSS_SELECTOR, 
                    "div.category-main div.headline"
                ))
                
                while load_more.is_displayed():
                    load_more.click()
                    time.sleep(2)  # Be nice to the server
                    
                    # Check if new articles were loaded
                    articles_after = len(self.driver.find_elements(
                        By.CSS_SELECTOR, 
                        "div.category-main div.headline"
                    ))
                    
                    if articles_after <= articles_before:  # No new articles
                        break
                    articles_before = articles_after
                    
            except Exception as e:
                self.logger.info(f"No load more button found for {url}: {str(e)}")
                # This is not an error - some categories don't have the button
                
            # Extract all loaded articles
            return self.extract_articles()
            
        except Exception as e:
            self.logger.error(f"Error loading content from Guardian: {str(e)}")
            return []
    
    def extract_articles(self):
        articles = []
        headlines = self.driver.find_elements(
            By.CSS_SELECTOR, 
            "div.category-main div.headline"
        )
        
        for headline in headlines:
            try:
                link = headline.find_element(By.CSS_SELECTOR, "span.title a")
                articles.append({
                    'url': link.get_attribute('href'),
                    'title': link.text
                })
            except Exception as e:
                self.logger.error(f"Error extracting article data: {str(e)}")
                continue
                
        return articles