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

# Website-specific selectors
WEBSITE_SELECTORS = {
    1: {  # Blueprint
        'title': 'h1.entry-title::text',
        'content': 'div.entry-content p::text',
        'pub_date': 'time.entry-date.published::attr(datetime), time.updated::attr(datetime)',  # Both timestamps
        'author': 'span.author.vcard a::text'
    },
    2: {  # ChannelsTV
        'title': 'h1.post-title::text',
        'content': 'div.post-content p::text',
        'pub_date': 'time.post-date::attr(datetime)',
        'author': 'div.post-category.text-sentence::text'
    },
    3: {  # Daily Nigerian
        'title': 'h1.entry-title::text',
        'content': 'div.td-post-content p::text',
        'pub_date': 'time.entry-date::attr(datetime)',
        'author': 'span.td-post-author-name a::text'
    }
}

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
            with self.Session() as session:
                article = session.query(Article).get(response.meta['article_id'])
                if not article:
                    return

                # Get website-specific selectors
                selectors = WEBSITE_SELECTORS.get(article.website_id, {})
                
                # Handle Blueprint's dual timestamps
                if article.website_id == 1:  # Blueprint
                    timestamps = response.css(selectors.get('pub_date', '')).getall()
                    pub_date = timestamps[0] if timestamps else None  # Use published date if available
                else:
                    pub_date = response.css(selectors.get('pub_date', '')).get()

                author = response.css(selectors.get('author', '')).get()

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