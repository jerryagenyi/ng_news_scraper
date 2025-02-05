# 4. main.py (updated for Scrapy)
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings
from config.settings import SCRAPER_SETTINGS
import logging

def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(message)s',
        handlers=[
            logging.FileHandler('scraper.log'),
            logging.StreamHandler()
        ]
    )

def run_spiders():
    # Get Scrapy settings
    settings = get_project_settings()
    settings.update(SCRAPER_SETTINGS)
    
    # Initialize the process
    process = CrawlerProcess(settings)
    
    # Add spiders to crawl
    process.crawl('punch')  # Add more spiders here
    
    # Start crawling
    process.start()

if __name__ == "__main__":
    setup_logging()
    run_spiders()

