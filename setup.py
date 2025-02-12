from setuptools import setup, find_packages

setup(
    name='ng_news_scraper',
    version='0.1',
    packages=find_packages(),
    install_requires=[
        'scrapy>=2.12.0',
        'sqlalchemy>=2.0.0',
        'psycopg2-binary>=2.9.0',
        'requests>=2.31.0',
        'selenium>=4.0.0',
        'python-dateutil>=2.8.0',
        'pytz>=2024.1'
    ]
)