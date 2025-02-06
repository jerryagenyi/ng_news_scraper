# ng_news_scraper/selenium_handlers/guardian_dynamic_loader.py
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from .base_dynamic_loader import BaseDynamicLoader
import time
import logging

class GuardianDynamicLoader(BaseDynamicLoader):
    def load_more_content(self, url, max_retries=10, delay=3):
        """
        Load content with retry mechanism for the load more button.
        """
        try:
            self.logger.info(f"Starting to load content from {url}")
            self.driver.get(url)
            time.sleep(delay)  # Initial delay for page load
            
            # Try to find load more button with retries
            load_more_found = False
            retry_count = 0
            
            while retry_count < max_retries and not load_more_found:
                try:
                    # First collect initial articles count
                    initial_articles = len(self.driver.find_elements(
                        By.CSS_SELECTOR, 
                        "div.category-main div.headline"
                    ))
                    self.logger.info(f"Found {initial_articles} articles initially")
                    
                    # Look for load more button
                    load_more = WebDriverWait(self.driver, 5).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, 
                        "button.load-more-button"))
                    )
                    load_more_found = True
                    self.logger.info("Load more button found, starting to load additional articles")
                    
                    articles_loaded = 0
                    # Click load more until no new articles are loaded
                    while load_more.is_displayed():
                        load_more.click()
                        time.sleep(2)
                        
                        current_articles = len(self.driver.find_elements(
                            By.CSS_SELECTOR,
                            "div.category-main div.headline"
                        ))
                        
                        if current_articles <= initial_articles:
                            self.logger.info("No new articles loaded, stopping")
                            break
                        
                        articles_loaded = current_articles - initial_articles
                        self.logger.info(f"Loaded {articles_loaded} additional articles")
                        initial_articles = current_articles
                        
                except Exception as e:
                    retry_count += 1
                    if retry_count == max_retries:
                        self.logger.warning(
                            f"Could not find load more button after {max_retries} "
                            f"retries. Proceeding with currently loaded articles. "
                            f"Error: {str(e)}"
                        )
                    else:
                        self.logger.info(f"Retry {retry_count}/{max_retries} to find load more button")
                        time.sleep(delay)
                        self.driver.refresh()
            
            # Extract all loaded articles
            self.logger.info("Starting article extraction")
            articles = self.extract_articles()
            self.logger.info(f"Finished extracting {len(articles)} articles")
            return articles
            
        except Exception as e:
            self.logger.error(f"Error loading content from Guardian: {str(e)}")
            return []

    def extract_articles(self):
        articles = []
        try:
            headlines = self.driver.find_elements(
                By.CSS_SELECTOR,
                "div.category-main div.headline"
            )
            
            self.logger.info(f"Found {len(headlines)} headlines to process")
            
            for headline in headlines:
                try:
                    # Find the link inside the headline
                    link = headline.find_element(
                        By.CSS_SELECTOR, 
                        "span.title a"
                    )
                    url = link.get_attribute('href')
                    title = link.text
                    
                    if url and title:  # Only add if we have both URL and title
                        articles.append({
                            'url': url,
                            'title': title
                        })
                except Exception as e:
                    self.logger.error(f"Error extracting article data: {str(e)}")
                    continue
                    
            self.logger.info(f"Successfully extracted {len(articles)} articles")
            return articles
            
        except Exception as e:
            self.logger.error(f"Error in extract_articles: {str(e)}")
            return []