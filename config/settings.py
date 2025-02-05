# config/settings.py
SCRAPER_SETTINGS = {
    # Scraper settings
    'ROBOTSTXT_OBEY': True,
    'CONCURRENT_REQUESTS': 16,
    'DOWNLOAD_DELAY': 3,  # 3 second delay between requests
    'COOKIES_ENABLED': False,
    
    # Database settings
    'DATABASE_URL': 'postgresql://postgres:naija1@localhost:5432/ng_news',
    
    # Pipeline settings
    'ITEM_PIPELINES': {
        'scrapers.pipelines.sql_pipeline.SQLAlchemyPipeline': 300,
    },
    
    # Middleware settings
    'DOWNLOADER_MIDDLEWARES': {
        'scrapers.middlewares.rotate_useragent.RotateUserAgentMiddleware': 400,
    }
}
