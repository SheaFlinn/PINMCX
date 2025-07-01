import feedparser
import praw
import os

def fetch_memphis_rss() -> list:
    """Fetches civic headlines from RSS-based sources in Memphis"""
    sources = [
        "https://dailymemphian.com/feed",  # Example RSS feed
        "https://www.commercialappeal.com/news/local/rss/"
    ]
    headlines = []
    for url in sources:
        feed = feedparser.parse(url)
        for entry in feed.entries:
            headlines.append({
                "city": "Memphis",
                "source": url,
                "headline": entry.title.strip()
            })
    return headlines

def fetch_reddit(city: str) -> list:
    """Fetches top civic posts from a city's subreddit"""
    reddit = praw.Reddit(
        client_id=os.getenv("REDDIT_CLIENT_ID"),
        client_secret=os.getenv("REDDIT_CLIENT_SECRET"),
        user_agent="pin-civic-predictor"
    )
    subreddit = reddit.subreddit(city.lower())
    results = []
    for post in subreddit.hot(limit=15):
        if any(k in post.title.lower() for k in ["council", "vote", "zoning", "permit", "funding", "plan"]):
            results.append({
                "city": city.title(),
                "source": f"reddit.com/r/{city}",
                "headline": post.title.strip()
            })
    return results

def fetch_city_headlines(city: str) -> list:
    """Fetches headlines for a given city from multiple sources"""
    city = city.title()
    rss = fetch_memphis_rss() if city == "Memphis" else []
    reddit = fetch_reddit(city)
    return rss + reddit
