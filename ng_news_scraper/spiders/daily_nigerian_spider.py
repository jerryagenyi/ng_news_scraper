import scrapy
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from ng_news_scraper.models.models import Article, Category, Website
from ng_news_scraper.config.settings import SCRAPER_SETTINGS
from sqlalchemy import func, literal
import re

class DailyNigerianSpider(scrapy.Spider):
    name = 'daily_nigerian'
    allowed_domains = ['dailynigerian.com']
    website_id = 3  # Hardcoded ID for Daily Nigerian

    custom_settings = {
        'ARTICLE_CONTAINER_SELECTOR': 'div.td_module_1',
        'ARTICLE_TITLE_SELECTOR': 'h3.entry-title a::text',
        'ARTICLE_URL_SELECTOR': 'h3.entry-title a::attr(href)',
        'ARTICLE_PUBLICATION_DATE_SELECTOR': 'time.entry-date::attr(datetime)',
        'ARTICLE_AUTHOR_SELECTOR': 'span.td-post-author-name a::text',
        'NEXT_PAGE_SELECTOR': 'div.page-nav a[aria-label="next-page"]::attr(href)'  # Adjust if needed
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.engine = create_engine(
            SCRAPER_SETTINGS['DATABASE_URL'],
            pool_size=10,
            max_overflow=20,
            pool_timeout=30
        )
        self.Session = sessionmaker(bind=self.engine)

    def start_requests(self):
        session = self.Session()
        try:
            # Get categories we haven't finished yet
            categories = (
                session.query(Category)
                .filter(Category.website_id == self.website_id)
                .all()
            )
            
            self.logger.info(f"Found {len(categories)} categories to process")
        finally:
            session.close()
        
        for category in categories:
            yield scrapy.Request(
                url=category.category_url,
                callback=self.parse_category,
                meta={
                    'category_id': category.id,
                    'article_count': 0,
                    'page': 1
                }
            )

    def parse_category(self, response):
        session = self.Session()
        try:
            articles_added = 0
            for article in response.css(self.custom_settings['ARTICLE_CONTAINER_SELECTOR']):
                url = article.css(self.custom_settings['ARTICLE_URL_SELECTOR']).get()
                title = article.css(self.custom_settings['ARTICLE_TITLE_SELECTOR']).get()
                
                # Extract author from title if present (e.g., "Title, by Author Name")
                author = None
                if title and ', by ' in title.lower():
                    title_parts = title.split(', by ')
                    if len(title_parts) > 1:
                        title = title_parts[0]
                        author = title_parts[1]
                
                self.logger.info(f"Found article: {title}")
                self.logger.debug(f"Author from title: {author}")
                
                yield {
                    'website_id': self.website_id,
                    'article_title': title,
                    'article_url': url,
                    'category_id': response.meta['category_id'],
                    'pub_date': None,  # Will be updated by update_articles.py
                    'author': author,
                    'page_number': response.meta.get('page', 1)
                }
                articles_added += 1
        finally:
            session.close()

        # Handle pagination
        next_page = response.css(self.custom_settings['NEXT_PAGE_SELECTOR']).get()
        if next_page:  # Continue as long as there's a next page
            self.logger.info(f"Found next page: {next_page}")
            yield scrapy.Request(
                url=next_page,
                callback=self.parse_category,
                meta={
                    'category_id': response.meta['category_id'],
                    'article_count': response.meta['article_count'] + articles_added,
                    'page': response.meta.get('page', 1) + 1
                }
            )