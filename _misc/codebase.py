# /Users/jeremiah/Projects/ng_news_scraper/ng_news_scraper/config/settings.py
# ng_news_scraper/config/settings.py
SCRAPER_SETTINGS = {
    # Scraper settings
    'ROBOTSTXT_OBEY': True,
    'CONCURRENT_REQUESTS': 16,
    'DOWNLOAD_DELAY': 3,  # 3 second delay between requests
    'COOKIES_ENABLED': False,
    
    # Database settings
    'DATABASE_URL': 'postgresql://postgres:naija1@localhost:5432/ng_news',
    
    # Pipeline settings
    'ITEM_PIPELINES': {
        'ng_news_scraper.pipelines.SQLAlchemyPipeline': 300,  # Updated path to match new structure
    },
    
    # Middleware settings
    'DOWNLOADER_MIDDLEWARES': {
        'ng_news_scraper.middlewares.RotateUserAgentMiddleware': 400,  # Updated path to match new structure
    }
}

# /Users/jeremiah/Projects/ng_news_scraper/ng_news_scraper/models/init_db.py
# models/init_db.py
import os
import sys

# Add the project root directory to Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from sqlalchemy import create_engine

# Now we can import our local modules
from models.models import Base
from config.settings import SCRAPER_SETTINGS

def init_database():
    engine = create_engine(SCRAPER_SETTINGS['DATABASE_URL'])
    Base.metadata.create_all(engine)
    print("Database initialized successfully!")

if __name__ == "__main__":
    init_database()

# /Users/jeremiah/Projects/ng_news_scraper/ng_news_scraper/models/models.py
# ng_news_scraper/models/models.py
from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()  # Add this line before defining models

class Category(Base):
    __tablename__ = 'categories'
    category_id = Column(Integer, primary_key=True)
    website = Column(String, nullable=False)
    category_name = Column(String, nullable=False)
    url = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    articles = relationship('Article', back_populates='category')

class Article(Base):
    __tablename__ = 'articles'
    article_id = Column(Integer, primary_key=True)
    category_id = Column(Integer, ForeignKey('categories.category_id'))
    url = Column(String, unique=True, nullable=False)
    article_title = Column(String, nullable=False)
    scraped = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    category = relationship('Category', back_populates='articles')
    data = relationship('ArticleData', back_populates='article', uselist=False)

class ArticleData(Base):
    __tablename__ = 'article_data'
    article_data_id = Column(Integer, primary_key=True)
    article_id = Column(Integer, ForeignKey('articles.article_id'), unique=True)
    article_title = Column(String)
    content = Column(Text)
    date = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    article = relationship('Article', back_populates='data')

# /Users/jeremiah/Projects/ng_news_scraper/ng_news_scraper/items.py
# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class NgNewsScraperItem(scrapy.Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    pass


# /Users/jeremiah/Projects/ng_news_scraper/ng_news_scraper/middlewares.py
# Define here the models for your spider middleware
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/spider-middleware.html

from scrapy import signals

# useful for handling different item types with a single interface
from itemadapter import is_item, ItemAdapter


class NgNewsScraperSpiderMiddleware:
    # Not all methods need to be defined. If a method is not defined,
    # scrapy acts as if the spider middleware does not modify the
    # passed objects.

    @classmethod
    def from_crawler(cls, crawler):
        # This method is used by Scrapy to create your spiders.
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        return s

    def process_spider_input(self, response, spider):
        # Called for each response that goes through the spider
        # middleware and into the spider.

        # Should return None or raise an exception.
        return None

    def process_spider_output(self, response, result, spider):
        # Called with the results returned from the Spider, after
        # it has processed the response.

        # Must return an iterable of Request, or item objects.
        for i in result:
            yield i

    def process_spider_exception(self, response, exception, spider):
        # Called when a spider or process_spider_input() method
        # (from other spider middleware) raises an exception.

        # Should return either None or an iterable of Request or item objects.
        pass

    def process_start_requests(self, start_requests, spider):
        # Called with the start requests of the spider, and works
        # similarly to the process_spider_output() method, except
        # that it doesn’t have a response associated.

        # Must return only requests (not items).
        for r in start_requests:
            yield r

    def spider_opened(self, spider):
        spider.logger.info("Spider opened: %s" % spider.name)


class NgNewsScraperDownloaderMiddleware:
    # Not all methods need to be defined. If a method is not defined,
    # scrapy acts as if the downloader middleware does not modify the
    # passed objects.

    @classmethod
    def from_crawler(cls, crawler):
        # This method is used by Scrapy to create your spiders.
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        return s

    def process_request(self, request, spider):
        # Called for each request that goes through the downloader
        # middleware.

        # Must either:
        # - return None: continue processing this request
        # - or return a Response object
        # - or return a Request object
        # - or raise IgnoreRequest: process_exception() methods of
        #   installed downloader middleware will be called
        return None

    def process_response(self, request, response, spider):
        # Called with the response returned from the downloader.

        # Must either;
        # - return a Response object
        # - return a Request object
        # - or raise IgnoreRequest
        return response

    def process_exception(self, request, exception, spider):
        # Called when a download handler or a process_request()
        # (from other downloader middleware) raises an exception.

        # Must either:
        # - return None: continue processing this exception
        # - return a Response object: stops process_exception() chain
        # - return a Request object: stops process_exception() chain
        pass

    def spider_opened(self, spider):
        spider.logger.info("Spider opened: %s" % spider.name)
# 2. scrapers/middlewares/rotate_useragent.py
from scrapy.downloadermiddlewares.useragent import UserAgentMiddleware
import random

class RotateUserAgentMiddleware(UserAgentMiddleware):
    user_agents = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)',
        'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36',
        # Add more user agents
    ]

    def __init__(self, user_agent=''):
        self.user_agent = user_agent

    def process_request(self, request, spider):
        ua = random.choice(self.user_agents)
        request.headers.setdefault('User-Agent', ua)

# /Users/jeremiah/Projects/ng_news_scraper/ng_news_scraper/pipelines.py
# ng_news_scraper/pipelines.py
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from ng_news_scraper.config.settings import SCRAPER_SETTINGS
from ng_news_scraper.models.models import Category, Article, ArticleData

class SQLAlchemyPipeline:
    def __init__(self):
        engine = create_engine(SCRAPER_SETTINGS['DATABASE_URL'])
        self.Session = sessionmaker(bind=engine)
    
    def process_item(self, item, spider):
        session = self.Session()
        try:
            # Check if category already exists
            existing = session.query(Category).filter_by(
                website=item['website'],
                category_name=item['category_name']
            ).first()
            
            if not existing:
                category = Category(
                    website=item['website'],
                    category_name=item['category_name'],
                    url=item['url']
                )
                session.add(category)
                session.commit()
                spider.logger.info(f"Added new category: {item['category_name']}")
            else:
                spider.logger.info(f"Category already exists: {item['category_name']}")
            
            return item
            
        except Exception as e:
            session.rollback()
            spider.logger.error(f"Error processing category: {str(e)}")
            raise
        finally:
            session.close()

# /Users/jeremiah/Projects/ng_news_scraper/ng_news_scraper/selenium_handlers/base_dynamic_loader.py
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

# /Users/jeremiah/Projects/ng_news_scraper/ng_news_scraper/selenium_handlers/guardian_dynamic_loader.py
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

# /Users/jeremiah/Projects/ng_news_scraper/ng_news_scraper/settings.py
# Scrapy settings for ng_news_scraper project
#
# For simplicity, this file contains only settings considered important or
# commonly used. You can find more settings consulting the documentation:
#
#     https://docs.scrapy.org/en/latest/topics/settings.html
#     https://docs.scrapy.org/en/latest/topics/downloader-middleware.html
#     https://docs.scrapy.org/en/latest/topics/spider-middleware.html

# ng_news_scraper/settings.py
from .config.settings import SCRAPER_SETTINGS

# Merge our settings with Scrapy's
locals().update(SCRAPER_SETTINGS)

# Add project root to Python path
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

BOT_NAME = "ng_news_scraper"
SPIDER_MODULES = ["ng_news_scraper.spiders"]
NEWSPIDER_MODULE = "ng_news_scraper.spiders"


# Crawl responsibly by identifying yourself (and your website) on the user-agent
#USER_AGENT = "ng_news_scraper (+http://www.yourdomain.com)"

# Obey robots.txt rules
#ROBOTSTXT_OBEY = True

# Configure maximum concurrent requests performed by Scrapy (default: 16)
#CONCURRENT_REQUESTS = 32

# Configure a delay for requests for the same website (default: 0)
# See https://docs.scrapy.org/en/latest/topics/settings.html#download-delay
# See also autothrottle settings and docs
#DOWNLOAD_DELAY = 3
# The download delay setting will honor only one of:
#CONCURRENT_REQUESTS_PER_DOMAIN = 16
#CONCURRENT_REQUESTS_PER_IP = 16

# Disable cookies (enabled by default)
#COOKIES_ENABLED = False

# Disable Telnet Console (enabled by default)
#TELNETCONSOLE_ENABLED = False

# Override the default request headers:
#DEFAULT_REQUEST_HEADERS = {
#    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
#    "Accept-Language": "en",
#}

# Enable or disable spider middlewares
# See https://docs.scrapy.org/en/latest/topics/spider-middleware.html
#SPIDER_MIDDLEWARES = {
#    "ng_news_scraper.middlewares.NgNewsScraperSpiderMiddleware": 543,
#}

# Enable or disable downloader middlewares
# See https://docs.scrapy.org/en/latest/topics/downloader-middleware.html
#DOWNLOADER_MIDDLEWARES = {
#    "ng_news_scraper.middlewares.NgNewsScraperDownloaderMiddleware": 543,
#}

# Enable or disable extensions
# See https://docs.scrapy.org/en/latest/topics/extensions.html
#EXTENSIONS = {
#    "scrapy.extensions.telnet.TelnetConsole": None,
#}

# Configure item pipelines
# See https://docs.scrapy.org/en/latest/topics/item-pipeline.html
#ITEM_PIPELINES = {
#    "ng_news_scraper.pipelines.NgNewsScraperPipeline": 300,
#}

# Enable and configure the AutoThrottle extension (disabled by default)
# See https://docs.scrapy.org/en/latest/topics/autothrottle.html
#AUTOTHROTTLE_ENABLED = True
# The initial download delay
#AUTOTHROTTLE_START_DELAY = 5
# The maximum download delay to be set in case of high latencies
#AUTOTHROTTLE_MAX_DELAY = 60
# The average number of requests Scrapy should be sending in parallel to
# each remote server
#AUTOTHROTTLE_TARGET_CONCURRENCY = 1.0
# Enable showing throttling stats for every response received:
#AUTOTHROTTLE_DEBUG = False

# Enable and configure HTTP caching (disabled by default)
# See https://docs.scrapy.org/en/latest/topics/downloader-middleware.html#httpcache-middleware-settings
#HTTPCACHE_ENABLED = True
#HTTPCACHE_EXPIRATION_SECS = 0
#HTTPCACHE_DIR = "httpcache"
#HTTPCACHE_IGNORE_HTTP_CODES = []
#HTTPCACHE_STORAGE = "scrapy.extensions.httpcache.FilesystemCacheStorage"

# Set settings whose default value is deprecated to a future-proof value
TWISTED_REACTOR = "twisted.internet.asyncioreactor.AsyncioSelectorReactor"
FEED_EXPORT_ENCODING = "utf-8"


# /Users/jeremiah/Projects/ng_news_scraper/ng_news_scraper/spiders/base_news_spider.py
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


# /Users/jeremiah/Projects/ng_news_scraper/ng_news_scraper/spiders/guardian_spider.py
# ng_news_scraper/spiders/guardian_spider.py
import scrapy
from ..selenium_handlers.guardian_dynamic_loader import GuardianDynamicLoader
from .base_news_spider import BaseNewsSpider

class GuardianSpider(BaseNewsSpider):
    name = 'guardian'
    allowed_domains = ['guardian.ng']
    start_urls = ['https://guardian.ng']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.dynamic_loader = GuardianDynamicLoader()
    
    def parse(self, response):
        # Your list of categories and URLs
        categories = [
            # Add your category list here
            {"name": "Metro", "url": "https://guardian.ng/category/news/nigeria/metro/"},
            # Add more categories...
        ]
        
        for category in categories:
            yield scrapy.Request(
                category['url'],
                self.parse_article_list,
                meta={'category': category['name']}
            )
    
    def parse_article_list(self, response):
        # Use dynamic loader to get all articles
        articles = self.dynamic_loader.load_more_content(response.url)
        
        for article in articles:
            yield scrapy.Request(
                article['url'],
                self.parse_article,
                meta={
                    'category': response.meta['category'],
                    'title': article['title']
                }
            )
    
    def parse_article(self, response):
        try:
            # Extract article content
            content = ' '.join(response.css('div.article-body p::text').getall())
            date = response.css('time.post-date::attr(datetime)').get()
            
            yield {
                'title': response.meta['title'],
                'date': date,
                'content': content,
                'category': response.meta['category'],
                'url': response.url
            }
        except Exception as e:
            self.logger.error(f"Error parsing article {response.url}: {str(e)}")

# /Users/jeremiah/Projects/ng_news_scraper/ng_news_scraper/spiders/guardian_test_spider.py
# ng_news_scraper/spiders/guardian_test_spider.py
import scrapy
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from ng_news_scraper.selenium_handlers.guardian_dynamic_loader import GuardianDynamicLoader
from ng_news_scraper.models.models import Category, Article
from ng_news_scraper.config.settings import SCRAPER_SETTINGS

class GuardianTestSpider(scrapy.Spider):
    name = 'guardian_test'
    allowed_domains = ['guardian.ng']
    article_count = 0
    max_articles = 100

    def __init__(self, category_name='Metro', *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.dynamic_loader = GuardianDynamicLoader()
        self.engine = create_engine(SCRAPER_SETTINGS['DATABASE_URL'])
        self.Session = sessionmaker(bind=self.engine)
        
        # Get category_id
        session = self.Session()
        self.category = session.query(Category).filter_by(
            category_name=category_name
        ).first()
        session.close()
        
        if not self.category:
            raise ValueError(f"Category {category_name} not found")
        
        self.start_urls = [self.category.url]

    def parse(self, response):
        if self.article_count >= self.max_articles:
            return
            
        articles = self.dynamic_loader.load_more_content(response.url)
        
        session = self.Session()
        try:
            for article in articles[:self.max_articles - self.article_count]:
                if not session.query(Article).filter_by(url=article['url']).first():
                    new_article = Article(
                        category_id=self.category.category_id,
                        url=article['url'],
                        article_title=article['title'],
                        scraped=False
                    )
                    session.add(new_article)
                    self.article_count += 1
                    
            session.commit()
            self.logger.info(f"Added {self.article_count} articles")
            
        except Exception as e:
            session.rollback()
            self.logger.error(f"Error saving articles: {str(e)}")
        finally:
            session.close()
            self.dynamic_loader.close()

# /Users/jeremiah/Projects/ng_news_scraper/ng_news_scraper/spiders/punch_spider.py
# scrapers/spiders/punch_spider.py
from .base_news_spider import BaseNewsSpider

class PunchSpider(BaseNewsSpider):
    name = 'punch'
    allowed_domains = ['punchng.com']
    start_urls = ['https://punchng.com']
    
    def parse_category(self, response):
        # Extract category links
        for category in response.css('nav.main-navigation a'):
            yield scrapy.Request(
                category.attrib['href'],
                self.parse_article_list,
                meta={'category': category.css('::text').get()}
            )
    
    def parse_article_list(self, response):
        # Extract article links
        for article in response.css('article.post h2 a'):
            yield scrapy.Request(
                article.attrib['href'],
                self.parse_article,
                meta={'category': response.meta['category']}
            )
        
        # Handle pagination
        yield from self.handle_pagination(response)
    
    def parse_article(self, response):
        yield {
            'title': response.css('h1.post-title::text').get(),
            'date': response.css('time.entry-date::attr(datetime)').get(),
            'content': ' '.join(response.css('div.entry-content p::text').getall()),
            'category': response.meta['category'],
            'url': response.url
        }



