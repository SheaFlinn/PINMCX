# PIN MVP Flask Application Project Plan

## Current State
- ✅ Flask app running with proper login and database migration
- ✅ Leaderboard working with XP, reliability, and points display
- ✅ Badge system functional (but missing icons)
- ✅ Admin draft page loads
- ❌ Reddit entries not populating
- ❌ News headlines show as "Untitled"
- ❌ News scraper test script has import issues
- ❌ Reddit JSON file empty or improperly parsed
- ❌ Wallet and badge pages need cleanup
- ✅ FLASK_APP set to run.py
- ✅ Using app factory pattern (create_app)

## Immediate Priorities

### 1. Core Functionality Fixes
- [ ] Fix news scraper selectors
  - [ ] Test each news source in `scripts/test_scraper.py`
  - [ ] Verify selector patterns
  - [ ] Ensure proper content extraction

- [ ] Fix app import issues
  - [ ] Add missing `__init__.py` in root or restructure `scripts/` folder
  - [ ] Ensure proper module path configuration

- [ ] Fix Reddit draft parsing
  - [ ] Debug `parse_reddit_drafts()`
  - [ ] Verify JSON file format
  - [ ] Implement proper draft population

### 2. Badge System
- [ ] Update badge icons
  - [ ] Add missing icons to database
  - [ ] Place image assets in `static/badges/`
  - [ ] Verify icon paths in templates

### 3. Wallet Page Restoration
- [ ] Restore wallet page functionality
  - [ ] Display XP properly
  - [ ] Show leaderboard position
  - [ ] Display reliability score
  - [ ] Show badge progress

### 4. Navigation
- [ ] Add working navigation
  - [ ] Link to `/wallet`
  - [ ] Link to `/badges`
  - [ ] Link to `/leaderboard`

## Deferred Tasks

### 1. UX Improvements
- [ ] Reliability index display in wallet
- [ ] League UX polish
- [ ] Market resolution UX improvements

### 2. Social Media Integration
- [ ] Create daily teaser script
  - [ ] Extract headlines for social media
  - [ ] Format for YouTube
  - [ ] Format for Facebook
  - [ ] Format for Instagram

## Technical Notes
- Using app factory pattern in [run.py](cci:7://file:///Users/georgeflinn/PM4/run.py:0:0-0:0)
- FLASK_APP configured correctly
- Database migrations in place
- Admin user and base badges seeded
- Streak and XP logic implemented

## Next Steps
1. Focus on core functionality fixes
2. Address badge system issues
3. Restore wallet page
4. Implement navigation
5. Move to deferred tasks
