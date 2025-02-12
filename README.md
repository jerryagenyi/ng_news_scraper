# README.md

# Nigerian News AI Assistant (Data Collection Phase)

A comprehensive news scraping and AI analysis platform focused on Nigerian news sources.

## Project Overview

Building an AI-powered news assistant that can answer questions about Nigerian news history by:

1. Scraping articles from major Nigerian news websites
2. Training an LLM model on the collected data
3. Providing a user-friendly query interface

## Project Roadmap

1. Phase 1: Database Setup & Category Collection. _✅ Done_
2. Phase 2: Article Archive Collection. _🔄 In progress..._
3. Phase 3: Content Extraction. _⏳ Planned_
4. Phase 4: AI Training. _⏳ Planned_

## Tech Stack

- Python (BeautifulSoup, Scrapy, Selenium)
- PostgreSQL with SQLAlchemy ORM for enriched relational mapping
- Enhanced support for dynamic web content extraction in addition to traditional scraping
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

## Creating New Spiders - _Quick_

To create a new spider:

1. **Inspect:** Use browser dev tools to analyze the target website's HTML to find CSS selectors for key elements like:
   – Article container/block
   – Article title
   – Article URL
   – Publication date
   – Author
   – Next page/pagination link

2. **Create/Copy:** Create a new spider file (e.g., `new_spider.py`) in the spiders directory, or copy an existing one (like `blueprint_spider.py`).

3. **Adapt:** Adapt the spider's `parse` method to extract article data from the target website's HTML.

- Update name, allowed_domains.
- Modify `start_requests` to fetch categories for the new website's ID.
- Adapt CSS selectors in `parse_category` and `handle_pagination`.
- Ensure correct `website_id` and `category_id` usage.

4. **Test:** Run the spider and verify data extraction and pagination.

## Creating New Spiders - _TLDR_

This project is designed to be easily extensible to scrape articles from various Nigerian news websites. Follow these steps to create a new spider:

**_Key File Structure:_**

1. **Understand Website Structure:** Use your browser's developer tools to inspect the HTML structure of the target website's category pages and article pages. Pay close attention to:

- CSS selectors for article titles, URLs, dates, and other metadata.
- Pagination mechanism (numbered pages, "Load More" button, etc.).
- Key Files Structure (see below):

```
ng_news_scraper/
├── spiders/
│   ├── blueprint_spider.py    # Blueprint-specific implementation
│   └── base_news_spider.py    # Base spider with common functionality
├── models/
│   └── models.py             # SQLAlchemy models
└── config/
    └── settings.py           # Configuration settings
```

2. **Create a New Spider File:** In the `spiders` directory, create a new Python file for your spider (e.g., `new_website_spider.py`).

3. **Inherit from `BaseNewsSpider`:** Your new spider should inherit from the `BaseNewsSpider` class.

4. **Implement `parse` method:** This is the core logic of your spider. You'll need to:

- Fetch categories from your database based on the website ID.
- Use CSS selectors to extract article data.
- Handle pagination (see examples below).
- Yield Scrapy Request objects for each article URL.

5. **Handle Pagination:**

- Numbered Pagination (Example: `blueprint_spider.py`):

```bash
next_page = response.css('a.next.page-numbers::attr(href)').get()  # Adapt selector
if next_page:
    yield scrapy.Request(
        url=next_page,
        callback=self.parse_category,
        meta={'category_id': category_id, 'website_id': website_id, 'article_count': article_count}
    )
```

- "Load More" Button (Work in Progress): Handling "Load More" buttons requires dynamic loading of content, usually with Selenium. See guardian_spider.dat for a starting point, but this functionality is still under development.

6. **Update `start_requests`:** Modify `start_requests` to query the database for categories associated with the new website's ID.

7. **Add to `allowed_domains`:** Add the new website's domain to the `allowed_domains` list in your spider class.

8. **Test Thoroughly:** Run your spider and carefully check the scraped data for accuracy and completeness.

## Project Structure

```
.
├── _misc               # Miscellaneous scripts and logs (e.g., codebase concatenation, progress notes)
├── guardian_test.log   # Log file for testing Guardian spider
├── main.py             # Application entry point
├── ng_news_scraper     # Main project package
│   ├── config          # Project configuration files (e.g., settings.py)
│   ├── items.py        # Scrapy item definitions
│   ├── middlewares.py  # Custom middlewares for Scrapy
│   ├── models          # Database models & initialization scripts
│   │   ├── init_db.py      # Script to initialize the database
│   │   ├── models.py       # SQLAlchemy ORM models and relationships
│   │   └── reset_db.py     # Script to reset the database
│   ├── pipelines.py    # Data processing pipelines
│   ├── scrapy.cfg      # Scrapy project configuration
│   ├── selenium_handlers  # Handlers for dynamic content extraction using Selenium
│   │   ├── base_dynamic_loader.py  # Base class for dynamic content loaders
│   │   └── guardian_dynamic_loader.py  # Dynamic loader for the Guardian website
│   ├── settings.py     # Scrapy settings file
│   └── spiders         # Spider definitions for various news websites
│       ├── base_news_spider.py  # Base spider for static pages and traditional pagination
│       ├── blueprint_spider.py  # Spider implementation for blueprint.ng
│       ├── guardian_spider.dat  # Spider configuration/data for guardian.ng
│       ├── guardian_test_spider.py  # Test spider for Guardian dynamic content
│       └── punch_spider.py  # Spider for punch.ng
├── scrapy.cfg          # Root-level Scrapy configuration
├── tree.sh             # Script to generate a tree view of the project
└── tree.txt            # Saved tree view of the project structure
```

## Contributing

1. Create a feature branch for your changes.
2. Follow the updated DB schema and spider guidelines when modifying article collection or crawling mechanisms.
3. Add tests for new features, especially for dynamic crawling and data processing.
4. Ensure your changes are documented both in the code and in this README.
5. Submit a pull request and follow the project's code of conduct.

**Test Thoroughly**
Before merging changes or adding features, run your spider(s) with the following commands to test:

- Run a Single Spider in Debug Mode:

```bash
scrapy crawl blueprint -L DEBUG
```

- Check Logs:
  Verify the output in the terminal and/or check the log files (e.g., guardian_test.log) for any errors or unexpected behavior.

- Database Verification:
  Ensure that scraped items (article titles and URLs) are correctly inserted into the database by querying relevant tables.

**Planned Features**

- Dynamic Crawling Enhancements:
  Refine Selenium-based spiders to better handle "load more" functionality and improve dynamic content extraction.

- Content Extraction & Cleaning:
  Develop methods to extract full article content, clean the data, and normalize publication dates/formats.

- User Query Interface:
  Build a front-end interface or API that allows users to query the scraped article data effectively.

- Optimised codebase:
  Refactor and optimize the codebase for better maintainability and performance. (ie, dictionary of required selectors for a website, etc.)

- LLM Integration:
  Create a training pipeline for an LLM model that leverages the scraped Nigerian news data for historical querying.

- Improved Logging & Error Handling:
  Add more robust logging, error management, and duplicate filtering across spiders and pipelines.

**Performance Optimization:**

- Update coming...
  _+ Ideas welcome..._

## Team Members

- [Jeremiah Agenyi](https://github.com/jerryagenyi) - Project Lead
- [Kelvin Bawa](https://github.com/kelvinbawa) - Project Mentor

## ProjectUpdates:

**Feb 7, 2025**

- ✅ Phase 1 Complete: Database created, Categories curated.
  - Core infrastructure: Scrapy + SeleniumSuccessfully collected all **765 categories** across **26 websites**, including:
    - "https://blueprint.ng"
    - "https://www.channelstv.com"
    - "https://dailynigerian.com"
    - "https://dailypost.ng"
    - "https://dailytimesng.com"
    - "https://dailytrust.com"
    - "https://guardian.ng"
    - "https://independent.ng"
    - "https://leadership.ng"
    - "https://www.legit.ng"
    - "https://www.nannews.ng"
    - "https://thenationonlineng.net"
    - "https://pmnewsnigeria.com"
    - "https://www.premiumtimesng.com"
    - "https://www.punchng.com"
    - "https://saharareporters.com"
    - "https://www.thecable.ng"
    - "https://telegraph.ng"
    - "https://www.thisdaylive.com"
    - "https://tribuneonlineng.com"
    - "https://nationaleconomy.com/"
    - "https://levogue.leadership.ng/"
    - "https://nanprwire.ng/"
    - "https://sportingtribune.com"
    - "https://www.vanguardngr.com"
    - "https://allure.vanguardngr.com/"
- 🔄 Phase 2 In Progress: Article Collection & Dynamic Crawling
  - Article titles and URLs are now being collected in the database, starting with blueprint.ng.
  - The project supports both static crawling (using BaseNewsSpider) and dynamic crawling (leveraging Selenium for dynamic content).

**Feb. 5, 2025**

- Project restarted with Scrapy for paginated archives and Selenium for dynamic content where 'load-more' button is used.
- Project cost reassessed.

**Jan. 30, 2025**

- Project initiated with bruteforce attempt at scraping. Failed...IP blocked on multiple websites
