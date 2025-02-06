# scrapers/spiders/punch_spider.py
from .base_news_spider import BaseNewsSpider

class PunchSpider(BaseNewsSpider):
    name = 'punch'
    allowed_domains = ['punchng.com']
    start_urls = ['https://punchng.com']
    
    def parse_category(self, response):
        # Extract category links
        for category in response.css('nav.main-navigation a'):
            yield scrapy.Request(
                category.attrib['href'],
                self.parse_article_list,
                meta={'category': category.css('::text').get()}
            )
    
    def parse_article_list(self, response):
        # Extract article links
        for article in response.css('article.post h2 a'):
            yield scrapy.Request(
                article.attrib['href'],
                self.parse_article,
                meta={'category': response.meta['category']}
            )
        
        # Handle pagination
        yield from self.handle_pagination(response)
    
    def parse_article(self, response):
        yield {
            'title': response.css('h1.post-title::text').get(),
            'date': response.css('time.entry-date::attr(datetime)').get(),
            'content': ' '.join(response.css('div.entry-content p::text').getall()),
            'category': response.meta['category'],
            'url': response.url
        }

