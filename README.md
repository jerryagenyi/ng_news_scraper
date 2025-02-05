# README.md

# Nigerian News AI Assistant (Data Collection Phase)

A comprehensive news scraping and AI analysis platform focused on Nigerian news sources.

## Project Overview

Building an AI-powered news assistant that can answer questions about Nigerian news history by:

1. Scraping articles from major Nigerian news websites
2. Training an LLM model on the collected data
3. Providing a user-friendly query interface

## Current Status (as of Feb 2025)

- ✅ Phase 1 Complete: Database Setup & Category Collection

  - PostgreSQL schema with three tables (categories, articles, article_data)
  - 101 Guardian categories imported
  - Core infrastructure: Scrapy + Selenium

- 🔄 Phase 2 In Progress: Article Collection

  - Developing URL extraction system
  - Implementing archive page handling
  - Testing with single category (100 articles limit)

- ⏳ Phase 3 Planned: Content Extraction
- ⏳ Phase 4 Planned: AI Training

## Tech Stack

- Python (Scrapy, Selenium)
- PostgreSQL
- SQLAlchemy
- Future: LLM Training Pipeline

## Setup

1. Database:

```bash
createdb ng_news
python models/init_db.py
```

2. Dependencies:

```bash
pip install -r requirements.txt
```

3. Configuration:

- Copy `.env.example` to `.env`
- Update database credentials

## Project Structure

```
ng_news_scraper/
├── config
│   └── settings.py
├── main.py
├── models
│   ├── init_db.py
│   └── models.py
└── scrapers
    ├── middlewares
    │   └── rotate_useragent.py
    ├── pipelines
    │   └── sql_pipeline.py
    ├── selenium_handlers
    │   ├── base_dynamic_loader.py
    │   └── guardian_dynamic_loader.py
    └── spiders
        ├── base_news_spider.py
        ├── guardian_spider.py
        └── punch_spider.py
```

## Contributing

1. Create feature branch
2. Test with single category first
3. Follow PEP 8 guidelines
4. Add tests for new features

## Team Members

- [Kelvin Bawa](https://github.com/kelvinbawa) - Project Mentor
- [Jeremiah Agenyi](https://github.com/jerryagenyi) - Project Lead
