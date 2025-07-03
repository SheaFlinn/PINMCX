import unittest
from unittest.mock import patch, MagicMock
import os
from api_chain.scraper_api import run_scraper, get_reddit_instance, get_city_subreddit, fetch_reddit_headlines

class TestScraperAPI(unittest.TestCase):
    def setUp(self):
        self.test_city = "memphis"
        self.expected_keys = ['city', 'source', 'headlines']
        self.expected_headline_keys = ['title', 'url', 'created_utc', 'author']

    def test_run_scraper_returns_dict(self):
        """Test that run_scraper returns a dictionary."""
        result = run_scraper(self.test_city)
        self.assertIsInstance(result, dict)

    def test_run_scraper_returns_headlines_structure(self):
        """Test that the output structure matches the expected format."""
        result = run_scraper(self.test_city)
        
        # Check top-level structure
        self.assertEqual(len(result), 3)
        self.assertEqual(result['city'], self.test_city.lower())
        self.assertIn(result['source'], ['reddit', 'mock'])
        self.assertIsInstance(result['headlines'], list)
        
        # Check headline structure
        for headline in result['headlines']:
            self.assertIsInstance(headline, dict)
            self.assertEqual(len(headline), 4)
            for key in self.expected_headline_keys:
                self.assertIn(key, headline)

    @patch('api_chain.scraper_api.get_reddit_instance')
    def test_run_scraper_mock_fallback_on_failure(self, mock_get_reddit):
        """Test that mock data is used when Reddit fails."""
        # Mock Reddit instance to fail
        mock_get_reddit.return_value = None
        
        result = run_scraper(self.test_city)
        
        # Verify mock data was used
        self.assertEqual(result['source'], 'mock')
        self.assertGreater(len(result['headlines']), 0)
        
        # Verify mock headlines have expected structure
        for headline in result['headlines']:
            self.assertIn(self.test_city.lower(), headline['url'])
            self.assertIn(self.test_city.title(), headline['title'])

    @patch('api_chain.scraper_api.get_city_subreddit')
    def test_run_scraper_invalid_city(self, mock_get_subreddit):
        """Test handling of invalid city."""
        mock_get_subreddit.return_value = None
        
        result = run_scraper("invalidcity")
        
        # Verify mock data is used as fallback
        self.assertEqual(result['source'], 'mock')
        self.assertGreater(len(result['headlines']), 0)

    @patch('api_chain.scraper_api.fetch_reddit_headlines')
    def test_run_scraper_no_reddit_headlines(self, mock_fetch_headlines):
        """Test handling of no Reddit headlines."""
        mock_fetch_headlines.return_value = []
        
        result = run_scraper(self.test_city)
        
        # Verify mock data is used as fallback
        self.assertEqual(result['source'], 'mock')
        self.assertGreater(len(result['headlines']), 0)

    def test_get_reddit_instance_no_env_vars(self):
        """Test Reddit instance creation without environment variables."""
        # Clear environment variables
        original_env = dict(os.environ)
        os.environ.clear()
        
        try:
            reddit = get_reddit_instance()
            self.assertIsNone(reddit)
        finally:
            # Restore environment variables
            os.environ.update(original_env)

    def test_get_city_subreddit_mapping(self):
        """Test city to subreddit mapping."""
        test_cases = {
            'memphis': 'memphis',
            'nashville': 'nashville',
            'knoxville': 'knoxville',
            'chattanooga': 'chattanooga',
            'invalidcity': 'memphis'  # Should fallback to default
        }
        
        for city, expected in test_cases.items():
            result = get_city_subreddit(city)
            self.assertEqual(result, expected)

    @patch('api_chain.scraper_api.fetch_reddit_headlines')
    def test_fetch_reddit_headlines_structure(self, mock_fetch_headlines):
        """Test structure of fetched Reddit headlines."""
        # Create sample posts
        sample_posts = [
            {
                "title": "Test Title",
                "url": "https://reddit.com/test",
                "created_utc": 1234567890,
                "author": "test_user"
            },
            {
                "title": "Another Title",
                "url": "https://reddit.com/another",
                "created_utc": 1234567891,
                "author": None
            }
        ]
        
        # Mock the function to return our sample posts
        mock_fetch_headlines.return_value = sample_posts
        
        # Test fetching headlines
        result = mock_fetch_headlines(None, "test_subreddit")
        
        # Verify structure
        self.assertEqual(len(result), 2)
        for headline in result:
            self.assertEqual(len(headline), 4)
            for key in self.expected_headline_keys:
                self.assertIn(key, headline)

if __name__ == '__main__':
    unittest.main()
