import requests
from sqlalchemy import create_engine, update
from sqlalchemy.orm import sessionmaker
from ng_news_scraper.models.models import Sitemap
from ng_news_scraper.config.settings import SCRAPER_SETTINGS
import logging
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def verify_url(url):
    try:
        response = requests.head(url, timeout=10)
        return url, response.status_code == 200, response.status_code
    except requests.RequestException:
        return url, False, None

def verify_urls(batch_size=100, max_workers=10, website_id=None):
    engine = create_engine(SCRAPER_SETTINGS['DATABASE_URL'])
    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        # Build query
        query = session.query(Sitemap)
        if website_id:
            query = query.filter(Sitemap.website_id == website_id)
        # Only check URLs that haven't been verified or failed previous verification
        query = query.filter(
            (Sitemap.is_valid.is_(None)) | 
            (Sitemap.is_valid.is_(False))
        )
        
        total = query.count()
        logger.info(f"Starting verification of {total} URLs")

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            offset = 0
            while True:
                urls = query.offset(offset).limit(batch_size).all()
                if not urls:
                    break

                results = executor.map(verify_url, [u.article_url for u in urls])
                for url_obj, (url, is_valid, status_code) in zip(urls, results):
                    url_obj.is_valid = is_valid
                    url_obj.last_checked = datetime.utcnow()
                    url_obj.status_code = status_code
                    
                    if not is_valid:
                        logger.warning(f"Invalid URL found: {url} (Status: {status_code})")

                session.commit()
                offset += batch_size
                logger.info(f"Processed {offset}/{total} URLs")
                time.sleep(1)  # Rate limiting

    finally:
        session.close()

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='Verify URLs in sitemap database')
    parser.add_argument('--batch-size', type=int, default=100)
    parser.add_argument('--max-workers', type=int, default=10)
    parser.add_argument('--website-id', type=int, help='Verify only URLs from specific website')
    args = parser.parse_args()

    verify_urls(args.batch_size, args.max_workers, args.website_id)