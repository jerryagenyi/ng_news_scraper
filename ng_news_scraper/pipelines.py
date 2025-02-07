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
            article = Article(
                website_id=1,  # Set website_id to 1 (Blueprint) directly
                article_title=item['article_title'],
                article_url=item['article_url'],
                scraped=False
            )
            session.add(article)
            session.commit()

            # ... (Rest of your pipeline code for ArticleData)
            spider.logger.info(f"Added new article: {item['article_title']}")
        except Exception as e:
            spider.logger.error(f"Error processing article: {item['article_title']} - {e}")
            session.rollback()
        finally:
            session.close()
        return item