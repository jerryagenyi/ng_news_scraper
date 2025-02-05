# models/models.py - Corrected version
class Category(Base):
    __tablename__ = 'categories'
    category_id = Column(Integer, primary_key=True)
    website = Column(String, nullable=False)
    category_name = Column(String, nullable=False)
    url = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    articles = relationship('Article', back_populates='category')

class Article(Base):
    __tablename__ = 'articles'
    article_id = Column(Integer, primary_key=True)
    category_id = Column(Integer, ForeignKey('categories.category_id'))
    url = Column(String, unique=True, nullable=False)
    article_title = Column(String, nullable=False)
    scraped = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    category = relationship('Category', back_populates='articles')
    data = relationship('ArticleData', back_populates='article', uselist=False)

class ArticleData(Base):
    __tablename__ = 'article_data'
    article_data_id = Column(Integer, primary_key=True)
    article_id = Column(Integer, ForeignKey('articles.article_id'), unique=True)
    article_title = Column(String)
    content = Column(Text)
    date = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    article = relationship('Article', back_populates='data')