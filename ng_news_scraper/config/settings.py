# ng_news_scraper/config/settings.py
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
        'ng_news_scraper.pipelines.SQLAlchemyPipeline': 300,  # Updated path to match new structure
    },
    
    # Middleware settings
    'DOWNLOADER_MIDDLEWARES': {
        'ng_news_scraper.middlewares.RotateUserAgentMiddleware': 400,  # Updated path to match new structure
    }
}