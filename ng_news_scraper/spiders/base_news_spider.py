import scrapy
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from ng_news_scraper.selenium_handlers.guardian_dynamic_loader import GuardianDynamicLoader
from ng_news_scraper.models.models import Category, Article
from ng_news_scraper.config.settings import SCRAPER_SETTINGS
import logging

class GuardianTestSpider(scrapy.Spider):
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

    def __init__(self, category_name='Metro', *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setup_logging()
        self.dynamic_loader = GuardianDynamicLoader()
        self.engine = create_engine(SCRAPER_SETTINGS['DATABASE_URL'])
        self.Session = sessionmaker(bind=self.engine)
        self.category = self.get_category(category_name)
        if not self.category:
            raise ValueError(f"Category {category_name} not found")
        self.start_urls = [self.category.url]

    def setup_logging(self):
        self.logger = logging.getLogger(self.name)
        handler = logging.FileHandler(f'{self.name}.log')
        handler.setFormatter(logging.Formatter(
            '%(asctime)s [%(levelname)s] %(message)s'
        ))
        self.logger.addHandler(handler)
        self.logger.setLevel(logging.INFO)

    def get_category(self, category_name):
        session = self.Session()
        try:
            return session.query(Category).filter_by(
                category_name=category_name
            ).first()
        finally:
            session.close()

    def start_requests(self):
        self.logger.info(f"Starting article extraction for category: {self.category.category_name}")
        yield scrapy.Request(
            self.category.url,
            self.parse,
            errback=self.handle_error,
            dont_filter=True
        )

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
            
            for article in articles_to_process:
                if not self.is_valid_article(article):
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

            if saved_count > 0:
                session.commit()
                self.logger.info(f"Saved {saved_count} new articles")

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