# ../_misc/codebase_make.py
import os

def concatenate_files(output_file, files_to_concatenate):
    with open(output_file, 'w') as output:
        for file_path in files_to_concatenate:
            with open(file_path, 'r') as input_file:
                output.write('# ' + file_path + '\n')
                output.write(input_file.read())
                output.write('\n\n')

files_to_concatenate = [
    '/Users/jeremiah/Projects/ng_news_scraper/ng_news_scraper/config/settings.py',
    '/Users/jeremiah/Projects/ng_news_scraper/scrapy.cfg',
    '/Users/jeremiah/Projects/ng_news_scraper/ng_news_scraper/scrapy.cfg',
    '/Users/jeremiah/Projects/ng_news_scraper/ng_news_scraper/models/init_db.py',
    '/Users/jeremiah/Projects/ng_news_scraper/ng_news_scraper/models/models.py',
    '/Users/jeremiah/Projects/ng_news_scraper/ng_news_scraper/items.py',
    '/Users/jeremiah/Projects/ng_news_scraper/ng_news_scraper/middlewares.py',
    '/Users/jeremiah/Projects/ng_news_scraper/ng_news_scraper/pipelines.py',
    '/Users/jeremiah/Projects/ng_news_scraper/ng_news_scraper/selenium_handlers/base_dynamic_loader.py',
    '/Users/jeremiah/Projects/ng_news_scraper/ng_news_scraper/selenium_handlers/guardian_dynamic_loader.py',
    '/Users/jeremiah/Projects/ng_news_scraper/ng_news_scraper/settings.py',
    '/Users/jeremiah/Projects/ng_news_scraper/ng_news_scraper/spiders/base_news_spider.py',
    '/Users/jeremiah/Projects/ng_news_scraper/ng_news_scraper/spiders/guardian_test_spider.py',
    '/Users/jeremiah/Projects/ng_news_scraper/ng_news_scraper/spiders/punch_spider.py',
    '/Users/jeremiah/Projects/ng_news_scraper/scripts/update_articles.py',
]

concatenate_files('codebase.py', files_to_concatenate)