# ng_news_scraper/models/models.py
from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()

class Website(Base):
    __tablename__ = 'websites'
    id = Column(Integer, primary_key=True)
    website_name = Column(String, nullable=False)
    website_url = Column(Text)
    categories = relationship('Category', back_populates='website')
    articles = relationship('Article', back_populates='website')  # Add this line

class Category(Base):
    __tablename__ = 'categories'
    id = Column(Integer, primary_key=True)
    website_id = Column(Integer, ForeignKey('websites.id'), nullable=False)
    category_name = Column(String, nullable=False)
    category_url = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    website = relationship('Website', back_populates='categories')

class Article(Base):
    __tablename__ = 'articles'
    id = Column(Integer, primary_key=True)
    website_id = Column(Integer, ForeignKey('websites.id'), nullable=False)  # Changed to website_id
    article_title = Column(String, nullable=False)
    article_url = Column(String, unique=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    scraped = Column(Boolean, default=False)
    website = relationship('Website', back_populates='articles')  # Add this relationship
    data = relationship('ArticleData', back_populates='article', uselist=False)

class ArticleData(Base):
    __tablename__ = 'article_data'
    id = Column(Integer, primary_key=True)
    article_id = Column(Integer, ForeignKey('articles.id'), unique=True, nullable=False)
    article_title = Column(String)  # You might want to remove this if you consider it redundant
    article_content = Column(Text)
    date = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    article = relationship('Article', back_populates='data')