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
            # Remove any explicit ID handling
            article = Article(
                website_id=item['website_id'],
                category_id=item['category_id'],
                article_title=item['article_title'],
                article_url=item['article_url'],
                author=item.get('author'),
                pub_date=item.get('pub_date'),
                scraped=False
            )
            session.add(article)
            session.commit()
            spider.logger.info(f"Added article: {item['article_title']}")
        except Exception as e:
            spider.logger.error(f"Error processing article: {item['article_title']} - {e}")
            session.rollback()
        finally:
            session.close()
        return item