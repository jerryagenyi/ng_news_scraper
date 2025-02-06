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