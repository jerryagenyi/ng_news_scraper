# Personal Project Tracker
# =======================
# This file is for my personal use to track progress, notes, and reminders for the ng_news_scraper project.
# It's not intended to be a public-facing document, but rather a personal reference guide.
# =======================

For Project Tracker (`PROGRESS.md`):
```markdown
# Project Progress Tracker
Last Updated: Feb 5, 2025

## Current Focus
- Testing article URL extraction
- Single category limit: 100 articles
- Guardian website implementation

## Completed Milestones
1. Database Schema
   - [x] Categories table
   - [x] Articles table
   - [x] Article_data table
   - [x] Updated to explicit IDs

2. Infrastructure
   - [x] Scrapy setup
   - [x] Selenium integration
   - [x] Database connections
   - [x] Git repository initialized

## Next Steps
- [ ] Test URL extraction (single category)
- [ ] Implement archive page handling
- [ ] Add rate limiting
- [ ] Scale to all categories

## Technical Notes
- Database: postgresql://postgres:naija1@localhost:5432/ng_news
- Robot.txt compliance important
- Consider rate limiting for production

## Questions/Concerns
- Rate limiting strategy
- Archive page handling
- Production scaling approach

## Resources
- Guardian sitemap
- Scrapy documentation
- Project documentation v1.1