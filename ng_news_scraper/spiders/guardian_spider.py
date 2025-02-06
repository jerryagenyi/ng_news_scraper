# ng_news_scraper/spiders/guardian_spider.py
import scrapy
from ..selenium_handlers.guardian_dynamic_loader import GuardianDynamicLoader
from .base_news_spider import BaseNewsSpider

class GuardianSpider(BaseNewsSpider):
    name = 'guardian'
    allowed_domains = ['guardian.ng']
    start_urls = ['https://guardian.ng']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.dynamic_loader = GuardianDynamicLoader()
    
    def parse(self, response):
        # Your list of categories and URLs
        categories = [
            # Add your category list here
            {"name": "Metro", "url": "https://guardian.ng/category/news/nigeria/metro/"},
            # Add more categories...
        ]
        
        for category in categories:
            yield scrapy.Request(
                category['url'],
                self.parse_article_list,
                meta={'category': category['name']}
            )
    
    def parse_article_list(self, response):
        # Use dynamic loader to get all articles
        articles = self.dynamic_loader.load_more_content(response.url)
        
        for article in articles:
            yield scrapy.Request(
                article['url'],
                self.parse_article,
                meta={
                    'category': response.meta['category'],
                    'title': article['title']
                }
            )
    
    def parse_article(self, response):
        try:
            # Extract article content
            content = ' '.join(response.css('div.article-body p::text').getall())
            date = response.css('time.post-date::attr(datetime)').get()
            
            yield {
                'title': response.meta['title'],
                'date': date,
                'content': content,
                'category': response.meta['category'],
                'url': response.url
            }
        except Exception as e:
            self.logger.error(f"Error parsing article {response.url}: {str(e)}")