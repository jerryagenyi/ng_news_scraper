# models/reset_db.py
import sys
import os
from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Text, create_engine
from sqlalchemy.orm import relationship, declarative_base
from datetime import datetime

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from ng_news_scraper.config.settings import SCRAPER_SETTINGS

Base = declarative_base()

class Website(Base):
    __tablename__ = 'websites'
    id = Column(Integer, primary_key=True)
    website_name = Column(String, nullable=False)
    url = Column(Text)
    categories = relationship('Category', back_populates='website')

class Category(Base):
    __tablename__ = 'categories'
    id = Column(Integer, primary_key=True)
    website_id = Column(Integer, ForeignKey('websites.id'), nullable=False)
    category_name = Column(String, nullable=False)
    category_url = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    website = relationship('Website', back_populates='categories')
    articles = relationship('Article', back_populates='category')

class Article(Base):
    __tablename__ = 'articles'
    id = Column(Integer, primary_key=True)
    categories_id = Column(Integer, ForeignKey('categories.id'), nullable=False)
    article_title = Column(String, nullable=False)
    article_url = Column(String, unique=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    scraped = Column(Boolean, default=False)
    pub_date = Column(DateTime)  # Add this line
    author = Column(String)  # Add this line
    category = relationship('Category', back_populates='articles')
    data = relationship('ArticleData', back_populates='article', uselist=False)

class ArticleData(Base):
    __tablename__ = 'article_data'
    id = Column(Integer, primary_key=True)
    article_id = Column(Integer, ForeignKey('articles.id'), unique=True, nullable=False)
    article_title = Column(String)
    article_content = Column(Text)
    pub_date = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    article = relationship('Article', back_populates='data')

DATABASE_URL = SCRAPER_SETTINGS['DATABASE_URL']
engine = create_engine(DATABASE_URL)
Base.metadata.drop_all(engine)
Base.metadata.create_all(engine)