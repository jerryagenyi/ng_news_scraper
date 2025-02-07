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
