# blueprint_spider.py
import scrapy
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from ng_news_scraper.models.models import Article, Category
from ng_news_scraper.config.settings import SCRAPER_SETTINGS

class BlueprintSpider(scrapy.Spider):
    name = 'blueprint'
    allowed_domains = ['blueprint.ng']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.engine = create_engine(SCRAPER_SETTINGS['DATABASE_URL'])
        self.Session = sessionmaker(bind=self.engine)
    
    def start_requests(self):
        session = self.Session()
        categories = session.query(Category).filter_by(website_id=1).all()
        session.close()
        
        for category in categories:
            yield scrapy.Request(url=category.category_url, callback=self.parse_category, meta={'category_id': category.id, 'article_count': 0})
    
    def parse_category(self, response):
        session = self.Session()
        category_id = response.meta['category_id']
        article_count = response.meta['article_count']
        website_id = 1  # Define website_id
        
        for article in response.css('div.archive-content'):
            #if article_count >= 100:
                #break
                
            url = article.css('h3.entry-title a::attr(href)').get()
            # Check if article exists
            exists = session.query(Article).filter_by(article_url=url).first()
            if exists:
                continue
                
            title = article.css('h3.entry-title a::text').get()
            date = article.css('time.entry-date::attr(datetime)').get()
            article_count += 1
            
            yield {
                'article_title': title,
                'article_url': url,
                'pub_date': date
            }
        
        # Handle pagination
        next_page = response.css('a.next.page-numbers::attr(href)').get()
        if next_page:  # No more article count limit check
            yield scrapy.Request(
                url=next_page,
                callback=self.parse_category,
                meta={
                    'category_id': category_id,
                    'article_count': article_count,  # Keep article_count for potential use
                    'website_id': website_id  # Ensure website_id is passed along
                }
            )

