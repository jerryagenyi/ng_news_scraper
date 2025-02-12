# spiders/channelstv_spider.py
import scrapy
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from ng_news_scraper.models.models import Article, Category, Website
from ng_news_scraper.config.settings import SCRAPER_SETTINGS
from sqlalchemy import func, literal
import re

class ChannelsTVSpider(scrapy.Spider):
    name = 'channelstv'
    allowed_domains = ['channelstv.com']
    website_name = 'ChannelsTV'  # This is what we'll search for

    custom_settings = {
        'ARTICLE_CONTAINER_SELECTOR': 'div.post-content.sumry-content',
        'ARTICLE_TITLE_SELECTOR': 'h3.post-title.sumry-title a::text',
        'ARTICLE_URL_SELECTOR': 'h3.post-title.sumry-title a::attr(href)',
        # Author and date are in: div.post-category.text-sentence
        # Format: "4m | Kayode Oyero"
        'ARTICLE_META_SELECTOR': 'div.post-category.text-sentence::text',
        'NEXT_PAGE_SELECTOR': 'a.next.page-numbers::attr(href)',
        'CONCURRENT_REQUESTS': 8,  # Reduced from 16
        'DOWNLOAD_DELAY': 2,      # Increased from 1
        'COOKIES_ENABLED': False,
        'RETRY_ENABLED': True,
        'RETRY_TIMES': 3,
        'DOWNLOAD_TIMEOUT': 180,
        'CLOSESPIDER_TIMEOUT': 0,  # Disable auto-close
        'DEPTH_LIMIT': 0,  # Remove depth limit
        'ROBOTSTXT_OBEY': False,  # Add this
        'HTTPCACHE_ENABLED': False,
        'LOG_LEVEL': 'INFO'
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.website_id = 2  # Hardcoded ID for ChannelsTV
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
        with self.Session() as session:
            categories = (
                session.query(Category)
                .filter(Category.website_id == self.website_id)
                .all()
            )
            
            self.logger.info(f"Found {len(categories)} categories for ChannelsTV")
            
            for category in categories:
                url = category.category_url
                if not url.startswith(('http://', 'https://')):
                    url = f'https://{url}'
                
                yield scrapy.Request(
                    url=url,
                    callback=self.parse_category,
                    meta={
                        'category_id': category.id,
                        'article_count': 0,
                        'page': 1
                    }
                )

    def parse_category(self, response):
        session = self.Session()
        category_id = response.meta['category_id']
        current_page = response.meta.get('page', 1)
        
        try:
            articles = response.css(self.custom_settings['ARTICLE_CONTAINER_SELECTOR'])
            self.logger.info(f"Page {current_page}: Found {len(articles)} articles")
            
            if len(articles) == 0:
                self.logger.warning(f"No articles found on page {current_page} - stopping pagination")
                return
            
            articles_added = 0
            for article in articles:
                url = article.css(self.custom_settings['ARTICLE_URL_SELECTOR']).get()
                if not url:
                    continue
                    
                # Add URL logging
                self.logger.debug(f"Checking URL: {url}")
                
                # Check for duplicates with logging
                exists = session.query(literal(True)).filter(
                    session.query(Article).filter(Article.article_url == url).exists()
                ).scalar()
                
                if not exists:
                    title = article.css(self.custom_settings['ARTICLE_TITLE_SELECTOR']).get()
                    if not title:
                        continue
                        
                    meta_text = article.css(self.custom_settings['ARTICLE_META_SELECTOR']).get()
                    time_ago, author = self.parse_meta(meta_text)
                    
                    self.logger.info(f"Adding article: {title}")
                    
                    yield {
                        'website_id': self.website_id,
                        'article_title': title,
                        'article_url': url,
                        'category_id': category_id,
                        'pub_date': None,
                        'author': author,
                        'page_number': current_page
                    }
                    articles_added += 1
        
            # Only continue pagination if we found and processed articles
            if articles_added > 0:
                next_page = response.css(self.custom_settings['NEXT_PAGE_SELECTOR']).get()
                if next_page:
                    yield scrapy.Request(
                        url=next_page,
                        callback=self.parse_category,
                        meta={
                            'category_id': category_id,
                            'page': current_page + 1
                        },
                        dont_filter=True
                    )
            else:
                self.logger.warning(f"No new articles added on page {current_page} - stopping pagination")
                
        except Exception as e:
            self.logger.error(f"Error in parse_category: {str(e)}")
        finally:
            session.close()

    def parse_meta(self, meta_text):
        """Parse the combined meta text into author and relative time"""
        if not meta_text:
            return None, None
        
        try:
            parts = meta_text.strip().split('|')
            time_ago = parts[0].strip()
            author = parts[1].strip() if len(parts) > 1 else None
            return time_ago, author
        except:
            return None, None