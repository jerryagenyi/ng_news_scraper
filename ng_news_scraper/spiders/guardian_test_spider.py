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