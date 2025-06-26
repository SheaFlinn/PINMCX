# MCX Clean Restart Plan

## PRIORITY: DO NOT RE-PLAN. EXECUTE THIS SEQUENCE IN ORDER.

### Task 1: Refactor `app/models.py`
- Remove **points**, **xp**, **reliability**, and **liquidity** logic from:
  - `User`
  - `Market`
  - `Prediction`
  - `LiquidityProvider`
- Move logic into `PointsService` in `services.py`
- Validate by running `python3 run.py` and using all core functions

### Task 2: Fix Admin Approval Bugs
- Ensure approving/rejecting drafts works
- Fix HTTP 415 error
- Verify title/description fields are passed and saved correctly

### Task 3: End-to-End Test
- Scrape news → Generate drafts → Approve → Market created → Predict → Resolve
- Confirm XP/points move correctly
- Confirm market resolution updates reliability

### Task 4: Reddit Scraper
- Verify .env credentials loaded
- Ensure redirect URI = `http://localhost:5001`
- Scrape `r/memphis`, `r/tennessee`, `r/memphispolitics`
- Score ≥ 10, title length ≥ 7 words
- Save to `reddit_drafts.json`

### Task 5: Signal Integrity & Transparency
- Log Market creation, prediction, resolution
- Display lineage on `market.html`
- Add downloadable CSV of user predictions

---

## Current Goal
✅ Task 1 — Refactor `app/models.py` and move all business logic into `services.py`. DO NOT EDIT `plan.md`. Just do it.

