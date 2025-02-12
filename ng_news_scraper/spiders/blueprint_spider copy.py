# spiders/blueprint_spider.py
import scrapy
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from ng_news_scraper.models.models import Article, Category, Website
from ng_news_scraper.config.settings import SCRAPER_SETTINGS
from sqlalchemy import func, literal
import re

class BlueprintSpider(scrapy.Spider):
    name = 'blueprint'
    allowed_domains = ['blueprint.ng']
    website_id = 1  # Hardcoded ID for Blueprint

    custom_settings = {
        'ARTICLE_CONTAINER_SELECTOR': 'div.archive-content',
        'ARTICLE_TITLE_SELECTOR': 'h3.entry-title a::text',
        'ARTICLE_URL_SELECTOR': 'h3.entry-title a::attr(href)',
        'ARTICLE_PUBLICATION_DATE_SELECTOR': 'time.entry-date.published::attr(datetime), time.updated::attr(datetime)',  # Get both timestamps
        'ARTICLE_AUTHOR_SELECTOR': 'span.author.vcard a::text',
        'NEXT_PAGE_SELECTOR': 'a.next.page-numbers::attr(href)'
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

    def get_website_id(self):
        """Get website ID from database"""
        with self.Session() as session:
            website = session.query(Website).filter_by(website_name=self.website_name).first()
            if not website:
                raise ValueError(f"Website '{self.website_name}' not found in database")
            return website.id

    def start_requests(self):
        session = self.Session()
        try:
            # Get all category URLs we've already fully processed
            completed_categories = (
                session.query(Category.category_url)
                .join(Article)
                .filter(
                    Category.website_id == self.website_id,
                    Article.scraped == True
                )
                .group_by(Category.category_url)
                .having(func.count(Article.id) >= 100)  # Consider category complete if it has 100+ articles
                .all()
            )
            
            # Get categories we haven't finished yet
            categories = (
                session.query(Category)
                .filter(
                    Category.website_id == self.website_id,
                    ~Category.category_url.in_([c.category_url for c in completed_categories])
                )
                .all()
            )
            
            self.logger.info(f"Found {len(categories)} categories to process")
        finally:
            session.close()
        
        for category in categories:
            # Get the last processed page number for this category
            last_page = self.get_last_processed_page(category.id)
            start_url = f"{category.category_url}/page/{last_page}" if last_page > 1 else category.category_url
            
            yield scrapy.Request(
                url=start_url,
                callback=self.parse_category,
                meta={
                    'category_id': category.id,
                    'article_count': 0,
                    'page': last_page
                }
            )

    def get_last_processed_page(self, category_id):
        session = self.Session()
        try:
            # Extract page number from article URLs and get the max
            last_article = (
                session.query(Article)
                .filter(
                    Article.category_id == category_id
                )
                .order_by(Article.created_at.desc())
                .first()
            )
            
            if last_article:
                # Try to extract page number from URL
                match = re.search(r'/page/(\d+)', last_article.article_url)
                if match:
                    return int(match.group(1))
            return 1
        finally:
            session.close()

    def parse_category(self, response):
        session = self.Session()
        category_id = response.meta['category_id']
        article_count = response.meta['article_count']
        current_page = response.meta.get('page', 1)
        
        try:
            articles_added = 0
            for article in response.css(self.custom_settings['ARTICLE_CONTAINER_SELECTOR']):
                url = article.css(self.custom_settings['ARTICLE_URL_SELECTOR']).get()
                
                # Check for duplicates (restore duplicate checking)
                exists = session.query(literal(True)).filter(
                    session.query(Article).filter(Article.article_url == url).exists()
                ).scalar()
                
                if not exists:
                    title = article.css(self.custom_settings['ARTICLE_TITLE_SELECTOR']).get()
                    
                    # Get both timestamps and use published if available, otherwise use updated
                    timestamps = article.css(self.custom_settings['ARTICLE_PUBLICATION_DATE_SELECTOR']).getall()
                    pub_date = timestamps[0] if timestamps else None  # First timestamp is 'published' if available
                    
                    author = article.css(self.custom_settings['ARTICLE_AUTHOR_SELECTOR']).get()
                    
                    self.logger.info(f"Found article: {title} at {url}")
                    self.logger.debug(f"Publication date: {pub_date}")
                    
                    yield {
                        'website_id': self.website_id,
                        'article_title': title,
                        'article_url': url,
                        'category_id': category_id,
                        'pub_date': pub_date,
                        'author': author,
                        'page_number': current_page
                    }
                    articles_added += 1
                    article_count += 1
        finally:
            session.close()

        self.logger.debug(f"=== END Category {category_id}, Added {articles_added} articles ===")

        # Updated pagination logic to match other spiders
        next_page = response.css(self.custom_settings['NEXT_PAGE_SELECTOR']).get()
        if next_page:  # Continue as long as there's a next page
            self.logger.info(f"Found next page: {next_page}")
            yield scrapy.Request(
                url=next_page,
                callback=self.parse_category,
                meta={
                    'category_id': category_id,
                    'article_count': article_count,
                    'page': current_page + 1
                }
            )

