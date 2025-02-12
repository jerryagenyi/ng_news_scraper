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

# /Users/jeremiah/Projects/ng_news_scraper/scrapy.cfg
# ng_news_scraper/scrapy.cfg
[settings]
default = ng_news_scraper.settings

[deploy]
project = ng_news_scraper

# /Users/jeremiah/Projects/ng_news_scraper/ng_news_scraper/scrapy.cfg
# ng_news_scraper/spiders/base_news_spider.py
import scrapy
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from ng_news_scraper.selenium_handlers.guardian_dynamic_loader import GuardianDynamicLoader
from ng_news_scraper.models.models import Category, Article
from ng_news_scraper.config.settings import SCRAPER_SETTINGS
import logging

class BaseNewsSpider(scrapy.Spider):
    name = 'base_news'
    custom_settings = {
        'DOWNLOAD_DELAY': 3,
        'CONCURRENT_REQUESTS_PER_DOMAIN': 1,
        'ROBOTSTXT_OBEY': True,
        'LOG_LEVEL': 'INFO',
        'DEPTH_LIMIT' = 0  # 0 means no limit (or set to a specific integer value)
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setup_logging()
        self.dynamic_loader = GuardianDynamicLoader()
        self.engine = create_engine(SCRAPER_SETTINGS['DATABASE_URL'])
        self.Session = sessionmaker(bind=self.engine)

    def setup_logging(self):
        self.logger = logging.getLogger(self.name)
        handler = logging.FileHandler(f'{self.name}.log')
        handler.setFormatter(logging.Formatter(
            '%(asctime)s [%(levelname)s] %(message)s'
        ))
        self.logger.addHandler(handler)
        self.logger.setLevel(logging.INFO)

    def start_requests(self):
        for url in self.start_urls:
            yield scrapy.Request(
                url, 
                self.parse,
                errback=self.handle_error,
                dont_filter=True
            )

    def parse(self, response):
        raise NotImplementedError("Subclasses must implement parse method")

    def handle_pagination(self, response):
        """Handle both traditional pagination and 'load more' buttons"""
        next_page = response.css('a.next-page::attr(href)').get()
        if next_page:
            yield scrapy.Request(
                next_page, 
                self.parse,
                errback=self.handle_error
            )
        else:
            more_content = self.dynamic_loader.load_more_content(response.url)
            if more_content:
                for item in more_content:
                    yield item

    def get_category(self, category_name):
        session = self.Session()
        try:
            return session.query(Category).filter_by(
                category_name=category_name
            ).first()
        finally:
            session.close()

    def handle_error(self, failure):
        self.logger.error(f"Request failed: {failure.value}")

    def closed(self, reason):
        self.logger.info(f"Spider closed: {reason}")
        if hasattr(self, 'dynamic_loader'):
            self.dynamic_loader.close()

    def is_valid_article(self, article):
        return all([
            article.get('url'),
            article.get('title'),
            len(article['title'].strip()) > 0
        ])

    def article_exists(self, session, url):
        return session.query(Article).filter_by(url=url).first() is not None



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

Base = declarative_base()

class Website(Base):
    __tablename__ = 'websites'
    id = Column(Integer, primary_key=True)
    website_name = Column(String, nullable=False)
    website_url = Column(Text)
    categories = relationship('Category', back_populates='website')
    articles = relationship('Article', back_populates='website')

class Category(Base):
    __tablename__ = 'categories'
    id = Column(Integer, primary_key=True)
    website_id = Column(Integer, ForeignKey('websites.id'), nullable=False)
    category_name = Column(String, nullable=False)
    category_url = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    website = relationship('Website', back_populates='categories')
    articles = relationship('Article', back_populates='category')

class Article(Base):
    __tablename__ = 'articles'
    id = Column(Integer, primary_key=True)
    website_id = Column(Integer, ForeignKey('websites.id'), nullable=False)
    category_id = Column(Integer, ForeignKey('categories.id'), nullable=False)
    article_title = Column(String, nullable=False)
    article_url = Column(String, unique=True, nullable=False)
    author = Column(Text)  # Change from String to Text
    pub_date = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    scraped = Column(Boolean, default=False)
    
    website = relationship('Website', back_populates='articles')
    category = relationship('Category', back_populates='articles')
    data = relationship('ArticleData', back_populates='article', uselist=False)

class ArticleData(Base):
    __tablename__ = 'article_data'
    id = Column(Integer, primary_key=True)
    article_id = Column(Integer, ForeignKey('articles.id'), unique=True, nullable=False)
    article_title = Column(String)  # You might want to remove this if you consider it redundant
    article_content = Column(Text)
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
from ng_news_scraper.models.models import Article, ArticleData

class SQLAlchemyPipeline:
    def __init__(self):
        self.engine = create_engine(SCRAPER_SETTINGS['DATABASE_URL'])
        self.Session = sessionmaker(bind=self.engine)

    def process_item(self, item, spider):
        session = self.Session()
        try:
            website_id = item.get('website_id')
            if not website_id:
                spider.logger.error("Missing website_id in item")
                return item

            article = Article(
                website_id=website_id,
                category_id=item['category_id'],  # Add this
                article_title=item['article_title'],
                article_url=item['article_url'],
                pub_date=item['pub_date'],  # Add this
                author=item['author'],      # Add this
                scraped=False
            )
            session.add(article)
            session.commit()

            spider.logger.info(f"Added new article: {item['article_title']}")
        except Exception as e:
            spider.logger.error(f"Error processing article: {item['article_title']} - {e}")
            session.rollback()
        finally:
            session.close()
        return item

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

# Set settings whose default value is deprecated to a future-proof value
TWISTED_REACTOR = "twisted.internet.asyncioreactor.AsyncioSelectorReactor"
FEED_EXPORT_ENCODING = "utf-8"

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
HTTPCACHE_ENABLED = True
HTTPCACHE_EXPIRATION_SECS = 0  # Never expire
HTTPCACHE_DIR = 'httpcache'
HTTPCACHE_IGNORE_HTTP_CODES = []
HTTPCACHE_STORAGE = 'scrapy.extensions.httpcache.FilesystemCacheStorage'


# /Users/jeremiah/Projects/ng_news_scraper/ng_news_scraper/spiders/base_news_spider.py
# ng_news_scraper/spiders/base_news_spider.py
import scrapy
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from ng_news_scraper.selenium_handlers.guardian_dynamic_loader import GuardianDynamicLoader
from ng_news_scraper.models.models import Category, Article
from ng_news_scraper.config.settings import SCRAPER_SETTINGS
import logging

class BaseNewsSpider(scrapy.Spider):
    name = 'base_news'
    custom_settings = {
        'DOWNLOAD_DELAY': 3,
        'CONCURRENT_REQUESTS_PER_DOMAIN': 1,
        'ROBOTSTXT_OBEY': True,
        'LOG_LEVEL': 'INFO'
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setup_logging()
        self.dynamic_loader = GuardianDynamicLoader()
        self.engine = create_engine(SCRAPER_SETTINGS['DATABASE_URL'])
        self.Session = sessionmaker(bind=self.engine)

    def setup_logging(self):
        self._logger = logging.getLogger(self.name)
        handler = logging.FileHandler(f'{self.name}.log')
        handler.setFormatter(logging.Formatter(
            '%(asctime)s [%(levelname)s] %(message)s'
        ))
        self._logger.addHandler(handler)
        self._logger.setLevel(logging.INFO)

    @property
    def logger(self):
        return self._logger

    def start_requests(self):
        for url in self.start_urls:
            yield scrapy.Request(
                url, 
                self.parse,
                errback=self.handle_error,
                dont_filter=True
            )

    def parse(self, response):
        raise NotImplementedError("Subclasses must implement parse method")

    def handle_pagination(self, response):
        """Handle both traditional pagination and 'load more' buttons"""
        next_page = response.css('a.next-page::attr(href)').get()  # Or a.next.page-numbers if that's the correct selector
        if next_page:
            self.logger.info(f"Following next page: {next_page}")  # Log the next page URL here
            yield scrapy.Request(
                next_page,
                self.parse,
                errback=self.handle_error
            )
        else:
            more_content = self.dynamic_loader.load_more_content(response.url)
            if more_content:
                for item in more_content:
                    yield item

    def get_category(self, category_name):
        session = self.Session()
        try:
            return session.query(Category).filter_by(
                category_name=category_name
            ).first()
        finally:
            session.close()

    def handle_error(self, failure):
        self.logger.error(f"Request failed: {failure.value}")

    def closed(self, reason):
        self.logger.info(f"Spider closed: {reason}")
        if hasattr(self, 'dynamic_loader'):
            self.dynamic_loader.close()

    def is_valid_article(self, article):
        return all([
            article.get('url'),
            article.get('title'),
            len(article['title'].strip()) > 0
        ])

    def article_exists(self, session, url):
        return session.query(Article).filter_by(url=url).first() is not None


# /Users/jeremiah/Projects/ng_news_scraper/ng_news_scraper/spiders/guardian_test_spider.py
# ng_news_scraper/spiders/guardian_test_spider.py
import scrapy
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from ng_news_scraper.selenium_handlers.guardian_dynamic_loader import GuardianDynamicLoader
from ng_news_scraper.models.models import Category, Article
from ng_news_scraper.config.settings import SCRAPER_SETTINGS
import logging
from .base_news_spider import BaseNewsSpider

class GuardianTestSpider(BaseNewsSpider):
    name = 'guardian_test'
    allowed_domains = ['guardian.ng']
    article_count = 0
    max_articles = 100
    
    custom_settings = {
        'DOWNLOAD_DELAY': 3,
        'CONCURRENT_REQUESTS_PER_DOMAIN': 1,
        'ROBOTSTXT_OBEY': True,
        'LOG_LEVEL': 'INFO'
    }

    def __init__(self, category_name='Nigeria', *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.category = self.get_category(category_name)
        if not self.category:
            raise ValueError(f"Category {category_name} not found")
        self.start_urls = [self.category.url]

    def parse(self, response):
        if self.article_count >= self.max_articles:
            self.logger.info(f"Reached max articles limit ({self.max_articles})")
            return

        try:
            articles = self.dynamic_loader.load_more_content(
                response.url,
                max_retries=5,
                delay=3
            )
            
            if not articles:
                self.logger.warning("No articles found in response")
                return

            self.logger.info(f"Found {len(articles)} articles")
            self.save_articles(articles)

        except Exception as e:
            self.logger.error(f"Error in parse: {str(e)}")
            raise
        finally:
            self.dynamic_loader.close()

    def save_articles(self, articles):
        session = self.Session()
        try:
            articles_to_process = articles[:self.max_articles - self.article_count]
            saved_count = 0
            
            self.logger.debug(f"Articles to process: {len(articles_to_process)}")
            
            for article in articles_to_process:
                self.logger.debug(f"Processing article: {article['url']}")
                if not self.is_valid_article(article):
                    self.logger.debug(f"Invalid article: {article['url']}")
                    continue
                    
                if not self.article_exists(session, article['url']):
                    new_article = Article(
                        category_id=self.category.category_id,
                        url=article['url'],
                        article_title=article['title'],
                        scraped=False
                    )
                    session.add(new_article)
                    saved_count += 1
                    self.article_count += 1
                    self.logger.debug(f"Article saved: {article['url']}")
                else:
                    self.logger.debug(f"Article already exists: {article['url']}")

            if saved_count > 0:
                session.commit()
                self.logger.info(f"Saved {saved_count} new articles")
            else:
                self.logger.info("No new articles to save")

        except Exception as e:
            session.rollback()
            self.logger.error(f"Error saving articles: {str(e)}")
            raise
        finally:
            session.close()

    def is_valid_article(self, article):
        return all([
            article.get('url'),
            article.get('title'),
            article['url'].startswith('https://guardian.ng'),
            len(article['title'].strip()) > 0
        ])

    def article_exists(self, session, url):
        return session.query(Article).filter_by(url=url).first() is not None

    def handle_error(self, failure):
        self.logger.error(f"Request failed: {failure.value}")

    def closed(self, reason):
        self.logger.info(f"Spider closed: {reason}")
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



# /Users/jeremiah/Projects/ng_news_scraper/scripts/update_articles.py
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import scrapy
from scrapy.crawler import CrawlerProcess
from sqlalchemy import create_engine, Column, Integer, String, DateTime, ForeignKey, Boolean, Text, and_, or_  # Added or_
from sqlalchemy.orm import sessionmaker, declarative_base, relationship
from datetime import datetime
from ng_news_scraper.config.settings import SCRAPER_SETTINGS
from scrapy.spidermiddlewares.httperror import HttpError
from twisted.internet.error import DNSLookupError, TimeoutError
from scrapy.downloadermiddlewares.retry import RetryMiddleware

Base = declarative_base()

class Website(Base): # Add Website Model
    __tablename__ = 'websites'
    id = Column(Integer, primary_key=True)
    website_name = Column(String, nullable=False)
    website_url = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    categories = relationship("Category", back_populates="website")
    articles = relationship("Article", back_populates="website")

class Category(Base):
    __tablename__ = 'categories'
    id = Column(Integer, primary_key=True)
    website_id = Column(Integer, ForeignKey('websites.id'), nullable=False) # Correct foreign key
    category_name = Column(String, nullable=False)
    category_url = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    website = relationship("Website", back_populates="categories")
    articles = relationship("Article", back_populates="category")

class Article(Base):
    __tablename__ = 'articles'
    id = Column(Integer, primary_key=True)
    website_id = Column(Integer, ForeignKey('websites.id'), nullable=False)
    category_id = Column(Integer, ForeignKey('categories.id'), nullable=False)  # Add category_id
    article_title = Column(String, nullable=False)
    article_url = Column(String, unique=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    scraped = Column(Boolean, default=False)
    pub_date = Column(DateTime)
    author = Column(Text)  # Change from String to Text for unlimited length

    website = relationship('Website', back_populates='articles')
    category = relationship('Category', back_populates='articles')
    data = relationship('ArticleData', back_populates='article', uselist=False)

class ArticleData(Base):
    __tablename__ = 'article_data'
    id = Column(Integer, primary_key=True)
    article_id = Column(Integer, ForeignKey('articles.id'), unique=True, nullable=False)
    article_title = Column(String)
    article_content = Column(Text)
    pub_date = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    article = relationship("Article", back_populates="data")


# Database connection settings
DATABASE_URL = SCRAPER_SETTINGS['DATABASE_URL']

# CSS selectors (Make these more specific if needed)
ARTICLE_PUBLICATION_DATE_SELECTOR = 'time.entry-date::attr(datetime)'
ARTICLE_AUTHOR_SELECTOR = 'span.author.vcard a::text'

# Create a Scrapy spider to fetch the data
class ArticleUpdateSpider(scrapy.Spider):
    name = 'article_update'
    
    custom_settings = {
        'RETRY_ENABLED': True,
        'RETRY_TIMES': 3,
        'RETRY_HTTP_CODES': [429, 500, 502, 503, 504, 522, 524, 408, 404],
        'HTTPERROR_ALLOWED_CODES': [404, 429, 503],
        'DOWNLOAD_DELAY': 1,
        'CONCURRENT_REQUESTS_PER_DOMAIN': 8
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.engine = create_engine(DATABASE_URL)
        self.Session = sessionmaker(bind=self.engine)
        self.stats = {'processed': 0, 'failed': 0}

    def start_requests(self):
        with self.Session() as session:
            # Query articles that haven't been updated (null pub_date or author)
            articles = (
                session.query(Article)
                .filter(
                    and_(
                        or_(
                            Article.pub_date.is_(None),
                            Article.author.is_(None)
                        )
                    )
                )
                .order_by(Article.id)
                .all()
            )
            
            self.logger.info(f"Found {len(articles)} articles to update")
            
            for article in articles:
                url = article.article_url
                if not url.startswith(('http://', 'https://')):
                    url = f'https://{url}'
                
                yield scrapy.Request(
                    url=url,
                    callback=self.parse_article,
                    errback=self.errback_httpbin,
                    meta={
                        'article_id': article.id,
                        'dont_retry': False,
                        'handle_httpstatus_list': [404, 429, 503]
                    },
                    dont_filter=True  # Allow revisiting URLs
                )

    def parse_article(self, response):
        try:
            pub_date = response.css(ARTICLE_PUBLICATION_DATE_SELECTOR).get()
            author = response.css(ARTICLE_AUTHOR_SELECTOR).get()
            
            # Clean and truncate data if needed
            if author:
                author = author.strip()[:500]  # Reasonable limit for author names
            
            if pub_date:
                try:
                    # Ensure pub_date is in proper format
                    pub_date = datetime.fromisoformat(pub_date.replace('Z', '+00:00'))
                except ValueError:
                    self.logger.warning(f"Invalid date format: {pub_date}")
                    pub_date = None

            with self.Session() as session:
                article = session.query(Article).get(response.meta['article_id'])
                if article:
                    if pub_date:
                        article.pub_date = pub_date
                    if author:
                        article.author = author
                    try:
                        session.commit()
                        self.stats['processed'] += 1
                    except Exception as e:
                        session.rollback()
                        self.logger.error(f"Database error: {e}")
                        self.stats['failed'] += 1

        except Exception as e:
            self.logger.error(f"Error processing article {response.url}: {e}")
            self.stats['failed'] += 1

    def errback_httpbin(self, failure):
        """Handle request errors"""
        if failure.check(HttpError):
            response = failure.value.response
            self.logger.error(f'HttpError on {response.url} - {response.status}')
        elif failure.check(DNSLookupError):
            request = failure.request
            self.logger.error(f'DNSLookupError on {request.url}')
        elif failure.check(TimeoutError):
            request = failure.request
            self.logger.error(f'TimeoutError on {request.url}')
        
        self.stats['failed'] += 1

    def closed(self, reason):
        """Log statistics when spider closes"""
        self.logger.info(f"Spider closed: {reason}")
        self.logger.info(f"Processed: {self.stats['processed']}, Failed: {self.stats['failed']}")

# Function to update the articles in the database
def update_articles():
    process = CrawlerProcess({
        'USER_AGENT': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36',
        'LOG_LEVEL': 'INFO',
        'COOKIES_ENABLED': True,
        'DOWNLOAD_DELAY': 1,
        'CONCURRENT_REQUESTS_PER_DOMAIN': 8,
        'RETRY_ENABLED': True,
        'RETRY_TIMES': 3,
        'RETRY_HTTP_CODES': [429, 500, 502, 503, 504, 522, 524, 408, 404],
        'HTTPERROR_ALLOWED_CODES': [404, 429, 503]
    })

    process.crawl(ArticleUpdateSpider)
    process.start()

# Run the update
if __name__ == '__main__':
    update_articles()

