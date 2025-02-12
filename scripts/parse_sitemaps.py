import requests
from xml.etree import ElementTree as ET
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from ng_news_scraper.models.models import Sitemap
from ng_news_scraper.config.settings import SCRAPER_SETTINGS
from datetime import datetime
import pytz
import logging
import time

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

DEFAULT_SETTINGS = {
    'timeout': 60,
    'max_retries': 3,
    'retry_delay': 5,
    'headers': {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
    }
}

WEBSITE_CONFIGS = {
    1: {  # Blueprint
        'name': 'Blueprint',
        'base_url': 'https://blueprint.ng',
        'sitemap_index': '/sitemap_index.xml',
        'sitemap_pattern': '/post-sitemap{}.xml',
        'total_sitemaps': 221,
        **DEFAULT_SETTINGS
    },
    2: {  # Channels TV
        'name': 'Channels TV',
        'base_url': 'https://www.channelstv.com',
        'sitemap_index': None,
        'sitemap_pattern': '/post-sitemap{}.xml',
        'total_sitemaps': 160,
        **DEFAULT_SETTINGS,
        'timeout': 90  # Custom timeout for slower sites
    },
    3: {  # Daily Nigerian
        'name': 'Daily Nigerian',
        'base_url': 'https://dailynigerian.com',
        'sitemap_index': '/wp-sitemap.xml',
        'sitemap_pattern': '/wp-sitemap-posts-post-{}.xml',
        'total_sitemaps': 45,
        **DEFAULT_SETTINGS
    },
    4: {  # Daily Post
        'name': 'Daily Post',
        'base_url': 'https://dailypost.ng',
        'sitemap_index': '/sitemap_index.xml',
        'sitemap_pattern': '/post-sitemap{}.xml',
        'total_sitemaps': 404,
        **DEFAULT_SETTINGS
    },
    5: {  # Daily Times
        'name': 'Daily Times',
        'base_url': 'https://dailytimesng.com',
        'sitemap_index': '/sitemap_index.xml',
        'sitemap_pattern': '/post-sitemap{}.xml',
        'total_sitemaps': 138,
        **DEFAULT_SETTINGS
    },
    7: {  # The Guardian
        'name': 'The Guardian',
        'base_url': 'https://guardian.ng',
        'sitemap_index': '/wp-sitemap.xml',
        'sitemap_pattern': '/wp-sitemap-posts-post-{}.xml',
        'total_sitemaps': 267,
        **DEFAULT_SETTINGS
    },
    8: {  # Independent
        'name': 'Independent',
        'base_url': 'https://independent.ng',
        'sitemap_index': '/wp-sitemap.xml',
        'sitemap_pattern': '/wp-sitemap-posts-post-{}.xml',
        'total_sitemaps': 252,
        **DEFAULT_SETTINGS
    },
    10: {  # Legit
        'name': 'Legit',
        'base_url': 'https://www.legit.ng',
        'sitemap_index': '/legit/sitemap/www/sitemap.xml',
        'sitemap_pattern': '/legit/sitemap/www/article-sitemap-{}.xml',
        'total_sitemaps': 21,
        'custom_parser': True,  # Special XML structure
        **DEFAULT_SETTINGS
    },
    11: {  # NAN
        'name': 'NAN',
        'base_url': 'https://nannews.ng',
        'sitemap_index': '/sitemap_index.xml',
        'sitemap_pattern': '/post-sitemap{}.xml',
        'total_sitemaps': 75,
        **DEFAULT_SETTINGS
    },
    13: {  # PM News
        'name': 'PM News',
        'base_url': 'https://pmnewsnigeria.com',
        'sitemap_index': '/sitemap_index.xml',
        'sitemap_pattern': '/post-sitemap{}.xml',
        'total_sitemaps': 277,
        **DEFAULT_SETTINGS
    },
    14: {  # Premium Times
        'name': 'Premium Times',
        'base_url': 'https://www.premiumtimesng.com',
        'sitemap_index': '/sitemap_index.xml',
        'sitemap_pattern': '/post-sitemap{}.xml',
        'total_sitemaps': 189,
        **DEFAULT_SETTINGS
    },
    17: {  # The Cable
        'name': 'The Cable',
        'base_url': 'https://www.thecable.ng',
        'sitemap_index': '/sitemap_index.xml',
        'sitemap_pattern': '/post-sitemap{}.xml',
        'total_sitemaps': 166,
        **DEFAULT_SETTINGS
    },
    18: {  # Telegraph
        'name': 'Telegraph',
        'base_url': 'https://telegraph.ng',
        'sitemap_index': '/sitemap-index-1.xml',
        'sitemap_pattern': '/sitemap-{}.xml',
        'total_sitemaps': 3,
        **DEFAULT_SETTINGS
    },
    20: {  # Tribune
        'name': 'Tribune',
        'base_url': 'https://tribuneonlineng.com',
        'sitemap_index': '/sitemap_index.xml',
        'sitemap_pattern': '/post-sitemap{}.xml',
        'total_sitemaps': 304,
        **DEFAULT_SETTINGS
    },
    23: {  # NAN PR Wire
        'name': 'NAN PR Wire',
        'base_url': 'https://nanprwire.ng',
        'sitemap_index': '/sitemap_index.xml',
        'sitemap_pattern': '/post-sitemap{}.xml',
        'total_sitemaps': 3,
        **DEFAULT_SETTINGS
    },
    24: {  # Tribune Sports
        'name': 'Tribune Sports',
        'base_url': 'https://sportingtribune.com',
        'sitemap_index': '/sitemap_index.xml',
        'sitemap_pattern': '/post-sitemap{}.xml',
        'total_sitemaps': 17,
        **DEFAULT_SETTINGS
    },
    25: {  # Vanguard
        'name': 'Vanguard',
        'base_url': 'https://www.vanguardngr.com',
        'sitemap_index': '/sitemap_index.xml',
        'sitemap_pattern': '/post-sitemap{}.xml',
        'total_sitemaps': 768,
        **DEFAULT_SETTINGS
    },
    26: {  # Vanguard Allure
        'name': 'Vanguard Allure',
        'base_url': 'https://allure.vanguardngr.com',
        'sitemap_index': '/sitemap_index.xml',
        'sitemap_pattern': '/post-sitemap{}.xml',
        'total_sitemaps': 21,
        **DEFAULT_SETTINGS
    }
}

class SitemapStats:
    def __init__(self):
        self.urls_found = 0
        self.urls_added = 0
        self.urls_skipped = []
        self.urls_failed = []

def fetch_with_retry(url, timeout=60, max_retries=3, headers=None):
    """Fetch URL with retry logic"""
    for attempt in range(max_retries):
        try:
            response = requests.get(url, timeout=timeout, headers=headers)
            response.raise_for_status()
            return response
        except requests.RequestException as e:
            if attempt == max_retries - 1:
                raise
            logger.warning(f"Attempt {attempt + 1} failed for {url}: {e}")
            time.sleep(5 * (attempt + 1))  # Exponential backoff

def parse_url_element(url_element, website_id):
    """Parse URL element based on website-specific structure"""
    website = WEBSITE_CONFIGS.get(website_id)
    
    try:
        if website.get('custom_parser'):
            # Special handling for Legit.ng
            loc_elem = url_element.find('.//{http://www.sitemaps.org/schemas/sitemap/0.9}loc')
            lastmod_elem = url_element.find('.//{http://www.sitemaps.org/schemas/sitemap/0.9}lastmod')
        else:
            # Standard sitemap structure with namespace
            loc_elem = url_element.find('.//{http://www.sitemaps.org/schemas/sitemap/0.9}loc')
            if loc_elem is None:
                # Try without namespace
                loc_elem = url_element.find('loc')
            lastmod_elem = url_element.find('.//{http://www.sitemaps.org/schemas/sitemap/0.9}lastmod')
            if lastmod_elem is None:
                # Try without namespace
                lastmod_elem = url_element.find('lastmod')

        if loc_elem is None:
            raise ValueError("Could not find URL location element")
            
        loc = loc_elem.text
        lastmod = lastmod_elem.text if lastmod_elem is not None else None
        
        logger.debug(f"Found URL: {loc} (last modified: {lastmod})")
        return loc, lastmod
        
    except Exception as e:
        logger.error(f"Error parsing URL element: {e}")
        logger.debug(f"URL element content: {ET.tostring(url_element, encoding='unicode')}")
        raise

def parse_sitemap_index(website_id):
    website = WEBSITE_CONFIGS.get(website_id)
    if not website:
        logger.error(f"No configuration found for website_id {website_id}")
        return
    
    stats = SitemapStats()
    session = Session()
    
    try:
        base_url = website['base_url']
        logger.info(f"Starting sitemap parsing for {website['name']} ({base_url})")
        
        # Handle sites with no index file
        if website['sitemap_index'] is None:
            start_from = website.get('start_from', 1)
            for i in range(start_from, website['total_sitemaps'] + 1):
                sitemap_url = f"{base_url}{website['sitemap_pattern'].format(i)}"
                parse_post_sitemap(website_id, sitemap_url, session, stats)
        else:
            # Handle sites with index file
            index_url = f"{base_url}{website['sitemap_index']}"
            try:
                response = fetch_with_retry(index_url, timeout=60, max_retries=3)
                root = ET.fromstring(response.content)
                
                for sitemap in root.findall('.//{http://www.sitemaps.org/schemas/sitemap/0.9}loc'):
                    parse_post_sitemap(website_id, sitemap.text, session, stats)
                    
            except requests.RequestException as e:
                logger.error(f"Failed to fetch sitemap index: {e}")
                
    finally:
        session.close()
        generate_report(stats, f"sitemap_report_{website_id}.txt")

def parse_post_sitemap(website_id, sitemap_url, session, stats):
    logger.info(f"Processing {sitemap_url}")
    website_config = WEBSITE_CONFIGS.get(website_id)
    
    try:
        response = fetch_with_retry(
            sitemap_url, 
            timeout=website_config.get('timeout', DEFAULT_SETTINGS['timeout']),
            max_retries=website_config.get('max_retries', DEFAULT_SETTINGS['max_retries']),
            headers=website_config.get('headers', DEFAULT_SETTINGS['headers'])
        )
        
        root = ET.fromstring(response.content)
        urls_this_batch = 0
        
        for url in root.findall('.//{http://www.sitemaps.org/schemas/sitemap/0.9}url'):
            stats.urls_found += 1
            try:
                loc, lastmod = parse_url_element(url, website_id)
                
                # Check if URL already exists
                existing = session.query(Sitemap).filter_by(
                    website_id=website_id, 
                    article_url=loc
                ).first()
                
                if existing:
                    stats.urls_skipped.append((loc, "Duplicate URL"))
                    continue
                
                if lastmod is not None:
                    lastmod = datetime.fromisoformat(lastmod.replace('Z', '+00:00'))
                
                sitemap = Sitemap(
                    website_id=website_id,
                    article_url=loc,
                    last_mod=lastmod,
                    is_valid=None,
                    last_checked=None,
                    status_code=None
                )
                
                session.add(sitemap)
                urls_this_batch += 1
                
                # Commit in smaller batches
                if urls_this_batch % 100 == 0:
                    session.commit()
                    stats.urls_added += urls_this_batch
                    urls_this_batch = 0
                
            except Exception as e:
                logger.warning(f"Error processing URL {loc}: {str(e)}")
                stats.urls_skipped.append((loc, str(e)))
                session.rollback()
        
        # Commit remaining URLs
        if urls_this_batch > 0:
            session.commit()
            stats.urls_added += urls_this_batch
        
        logger.info(f"Found {stats.urls_found} URLs, added {stats.urls_added} new entries")
        
    except requests.RequestException as e:
        logger.error(f"Failed to fetch sitemap {sitemap_url}: {e}")
    except ET.ParseError as e:
        logger.error(f"Failed to parse sitemap {sitemap_url}: {e}")

def generate_report(stats, output_file="sitemap_report.txt"):
    with open(output_file, "w") as f:
        f.write(f"Sitemap Processing Report\n")
        f.write(f"========================\n")
        f.write(f"Total URLs found: {stats.urls_found}\n")
        f.write(f"Successfully added: {stats.urls_added}\n")
        f.write(f"Failed URLs: {len(stats.urls_failed)}\n")
        f.write(f"Skipped URLs: {len(stats.urls_skipped)}\n\n")
        
        if stats.urls_failed:
            f.write("Failed URLs:\n")
            for url, reason in stats.urls_failed:
                f.write(f"- {url}: {reason}\n")
        
        if stats.urls_skipped:
            f.write("\nSkipped URLs:\n")
            for url, reason in stats.urls_skipped:
                f.write(f"- {url}: {reason}\n")

def process_all_websites():
    """Process all configured websites sequentially"""
    website_ids = sorted(WEBSITE_CONFIGS.keys())
    logger.info(f"Starting processing of {len(website_ids)} websites")
    
    for website_id in website_ids:
        website = WEBSITE_CONFIGS[website_id]
        logger.info(f"\n{'='*50}\nProcessing {website['name']} (ID: {website_id})\n{'='*50}")
        try:
            parse_sitemap_index(website_id)
        except Exception as e:
            logger.error(f"Failed to process {website['name']}: {e}")
            continue

# Fix the escape sequence in get_last_processed_sitemap function
def get_last_processed_sitemap(website_id, session):
    """Get the last successfully processed sitemap number"""
    website = WEBSITE_CONFIGS.get(website_id)
    if not website:
        return 0
        
    try:
        last_url = session.query(Sitemap.article_url)\
            .filter_by(website_id=website_id)\
            .order_by(Sitemap.id.desc())\
            .first()
            
        if not last_url:
            return 0
            
        # Use raw string for regex pattern
        pattern = website['sitemap_pattern'].replace('{}', r'(\d+)')
        match = re.search(pattern, last_url[0])
        if match:
            return int(match.group(1))
    except Exception as e:
        logger.error(f"Error getting last processed sitemap: {e}")
    return 0

# Update the main section to properly handle command line arguments
if __name__ == "__main__":
    import argparse
    import re
    
    parser = argparse.ArgumentParser(description='Parse sitemaps for Nigerian news websites')
    parser.add_argument('--website-id', '-w', type=int, 
                       choices=[1,2,3,4,5,7,8,10,11,13,14,17,18,20,23,24,25,26],
                       help='Process specific website ID')
    parser.add_argument('--all', '-a', action='store_true', 
                       help='Process all websites sequentially')
    parser.add_argument('--resume', '-r', action='store_true',
                       help='Resume from last processed sitemap')
    args = parser.parse_args()

    engine = create_engine(SCRAPER_SETTINGS['DATABASE_URL'])
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        if args.resume and args.website_id:
            last_sitemap = get_last_processed_sitemap(args.website_id, session)
            logger.info(f"Resuming from sitemap {last_sitemap}")
            # Update total_sitemaps to start from last processed
            WEBSITE_CONFIGS[args.website_id]['start_from'] = last_sitemap
            
        if args.all:
            process_all_websites()
        elif args.website_id:
            parse_sitemap_index(args.website_id)
        else:
            parser.print_help()
    finally:
        session.close()