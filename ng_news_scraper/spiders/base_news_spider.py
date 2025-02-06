# ng_news_scraper/spiders/base_news_spider.py
import scrapy
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from ..selenium_handlers.base_dynamic_loader import BaseDynamicLoader  # Changed import

class BaseNewsSpider(scrapy.Spider):
    name = 'base_news'
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.dynamic_loader = BaseDynamicLoader()  # Changed to match our base class
    
    def start_requests(self):
        for url in self.start_urls:
            yield scrapy.Request(url, self.parse_category)
    
    def handle_pagination(self, response):
        """Handle both traditional pagination and 'load more' buttons"""
        # Try traditional pagination first
        next_page = response.css('a.next-page::attr(href)').get()
        if next_page:
            yield scrapy.Request(next_page, self.parse)
        else:
            # Try 'load more' button using Selenium
            more_content = self.dynamic_loader.load_more_content(response.url)
            if more_content:
                # Process the additional content
                for item in more_content:
                    yield self.parse_article(item)
